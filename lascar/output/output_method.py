"""
This file is part of lascar

lascar is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr

"""

import logging


class OutputMethod:
    """
    OutputMethod is an virtual class.
    Its role is to set up the strategy for outputing results computed by engines.

    The Session registers an OutputMethod.
    The OuputMethod tracks engines, and, at each output_step, it request results to them.

    The children inherating from OutputManager implements how to process these results, and how to deliver them to the user.
    """

    def __init__(self, *engines):
        """

        :param engines: the engines to be tracked by the OuputEngine. Other Engines will be ignored. If not specified, the OuputMethod tracks all the engines of the session.
        """
        self.logger = logging.getLogger(__name__)
        self.engines = engines

    def update(self, engine, results):
        """
        update() is the method called by the Session at each output_step.
        After computing its results, the Session calls its OuptutMethod update() method for the results to be processed.

        :param engine: the current engine
        :param results: its result
        :return: None
        """
        if self.engines is ():
            self.engines = list(engine._session.engines)

        if not (engine in self.engines or engine.name in self.engines or len(self.engines) == 0):
            return
        self.logger.debug('Update engine %s', engine.name)
        self._update(engine, results)

    def finalize(self):
        """
        At the end of the Session processing side-channel traces, the OutputMethod finalize() method is called to conclude the ouput strategy
        :return:
        """
        self.logger.debug('Finalize.')
        return self._finalize()


class MultipleOutputMethod(OutputMethod):
    """
    MultipleOutputMethod is the OutputMethod used when the user want to register multiple OutputMethods.
    """

    def __init__(self, *output_methods):
        """

        :param output_methods: the OutputMethods (must be instantiated).
        """
        self.output_engines = output_methods
        self.logger = logging.getLogger(__name__)

    def update(self, engine, results):
        for output_engine in self.output_engines:
            output_engine.update(engine, results)

    def finalize(self):
        for output_engine in self.output_engines:
            output_engine.finalize()
