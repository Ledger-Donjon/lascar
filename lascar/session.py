# This file is part of lascar
#
# lascar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
# Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr

import logging
from threading import Thread
import numpy as np
from .engine import MeanEngine, VarEngine
from .output import MultipleOutputMethod, DictOutputMethod, OutputMethod, NullOutputMethod

import progressbar

class Session:
    """
    This class is leading side-channel operation in lascar.

    a :class:`lascar.session.Session` object's role is to:

    - get batch of side channel traces from a Container, 'container'
    - distribute the batchs to the registered engines. 'engines'
    - manage outputs thanks to 'output_method', 'output_step'
        
    :param container: the container that will be read during the session. Only
        mandatory argument for constructor.
    :param engine: lascar engine to be registered by the Session
    :param engines: list of lascar engines to be registered by the Session
    :param output_method: specify the output method: how will the results from
        the engine will be manipulated. see lascar/output for more info.
    :param output_steps: specify when the Session will ask its engines to
        compute results.
    :param name: name given for the Session.
    :param progressbar: Will the Session display a progressbar during its
        process.
    """
    def __init__(self, container, engine=None, engines=None, output_method=None, output_steps=None, name="Session", progressbar=True):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating Session.')

        self.container = container
        self.leakage_shape = container._leakage_abstract.shape
        self.value_shape = container._value_abstract.shape

        self.name = name

        self.engines = {}

        self.add_engine(MeanEngine())
        self.add_engine(VarEngine())

        if engine is not None:
            self.add_engine(engine)
        if engines is not None:
            self.add_engines(engines)

        #output_method: what will I do with my engines results?
        if output_method is not None:
            self.output_method = output_method
        else:
            self.output_method = NullOutputMethod()

        #output_steps: When will OutputMethod will be called?
        self.output_steps=output_steps

        self._progressbar = progressbar

    @property
    def output_method(self):
        return self._output_method

    @output_method.setter
    def output_method(self,output_method):
        if isinstance(output_method, OutputMethod):
            self._output_method = output_method
        elif hasattr(output_method, '__iter__'):
            self._output_method = MultipleOutputMethod(*output_method)
        else:
            self._output_method = OutputMethod()

    @property
    def output_steps(self):
        return self._output_steps

    @output_steps.setter
    def output_steps(self, output_steps):
        if isinstance(output_steps, int):
            self._output_steps = list(range(output_steps, self.container.number_of_traces+1, output_steps))
        elif hasattr(output_steps, '__iter__'):
            self._output_steps = [i for i in output_steps]
        else:
            self._output_steps = []

        if not self.container.number_of_traces in self._output_steps:
            self._output_steps.append(self.container.number_of_traces)
        self._output_steps.sort()


    def add_engine(self, engine):
        """
        Add an engine to the session

        :param engine: engine to be added
        :return: None
        """
        if engine.name in self.engines:
            raise ValueError("%s is already an Engine name for this session." % engine.name)

        self.engines.update({engine.name: engine})
        
    def add_engines(self, engines):
        """
        Add a list of engines to the session

        :param engines: list of engines to be added
        :return: None
        """
        for engine in engines:
            self.add_engine(engine)


    def _generate_batch_offsets(self, batch_size):
        """
        From a maximum batch_size, and output_steps (already inside Session class, this function computes the offsets of the batchs that will be used by the Session.run() method.

        :param batch_size:
        :return:
        """

        batch_offsets = []
        offset = 0

        while offset < self.container.number_of_traces:
            if offset + batch_size > self.container.number_of_traces:
                batch_offsets.append((offset, self.container.number_of_traces))

            else:
                batch_offsets.append((offset, offset + batch_size))
            offset += batch_size

        output_steps = list(self.output_steps)[::-1]

        for output_step in output_steps:

            for i,offsets in enumerate(batch_offsets):
                if offsets[0] < output_step < offsets[1]:
                    batch_offsets = batch_offsets[:i] + [(offsets[0], output_step), (output_step, offsets[1])] + batch_offsets[i+1:]

        return batch_offsets


    def run(self, batch_size=100, thread_on_update=True):
        """
        Core function of Session: read all traces from the container, and distibute them to the engines, and manage results

        :param batch_size: the size of the batch that will be read from the container.
        :param thread_on_update: will the engine be updated on different threads?
        :return:
        """
        self._batch_size = batch_size
        self._thread_on_update = thread_on_update

        [engine.initialize(self) for engine in self.engines.values()]

        self.logger.debug('Process with parameters #%d/%d offsets.' % (self._batch_size, self._thread_on_update))

        batch_offsets = self._generate_batch_offsets(self._batch_size)
        self.logger.debug('Session run() will be done in %d batchs' % (len(batch_offsets)))

        self.logger.info("Session %s: %d traces, %d engines, batch_size=%d, leakage_shape=%s" % (self.name, self.container.number_of_traces, len(self.engines), self._batch_size, self.leakage_shape))

        #  ProgressBar:
        if self._progressbar:
            self_progressbar = self._get_progressbar().start()

        for i, offsets in enumerate(batch_offsets):

            self.logger.debug('Processing batch #%d/%d, with trace offsets: %s.' % (i + 1, len(batch_offsets), str(offsets)))

            batch = self.container[offsets[0]: offsets[1]]

            if not self._thread_on_update:
                [engine.update(batch) for engine in self.engines.values()]

            else:
                threads = []
                for engine in self.engines.values():

                    thread = Thread(target=engine.update, args=(batch,))
                    threads.append(thread)
                    thread.start()

                [thread.join() for thread in threads]

            #  OutputMethod: Get results:
            if offsets[1] and offsets[1] in self.output_steps:
                self.logger.debug("Computing results (output step %d)."%offsets[1])
                for engine in self.engines.values():
                    results = engine.finalize()
                    if isinstance(results, np.ndarray):
                        results = np.copy(results)
                    self.output_method.update(engine,results)

            if self._progressbar:
                self_progressbar.update(offsets[1])

        if self._progressbar:
            self_progressbar.finish()

        self.output_method.finalize()

        return self

    def __getitem__(self, item):
        return self.engines[item]

    def _get_progressbar(self):
        if self._progressbar is not None:
            widgets = [self.name + ' |',
                       progressbar.Percentage(),
                       progressbar.Bar(),
                       progressbar.FormatLabel('%(value)d trc'),
                       "/%d |"% (len(self.container)),
                       " (%d engines, batch_size=%d, leakage_shape=%s) |"%(len(self.engines),self._batch_size, self.leakage_shape),
                       progressbar.AdaptiveETA()]
            return progressbar.ProgressBar(widgets=widgets, max_value=len(self.container))