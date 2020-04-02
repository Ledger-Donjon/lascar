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

"""
engine.py
"""
import logging
import numpy as np
from lascar.output.parse_results import parse_output_basic


class Engine:
    """
    Engine is an abstract class whose role is to handle TraceBatches from a Session.

    Any class inheriting from Engine must implemement at least 3 methods:
        - _initialize(): called by the Session once before processing batchs
        - _update(batch): called each time the Session has a TraceBatch to process
        - _finalize(): used to deliver the result of the Engine
        - _clean(): used to clean Engine, ie: erase

    """

    def __init__(self, name):
        """
        :param name: the name chosen for the Engine
        """
        if name is None:
            name = hex(id(self))[2:]
        self.name = name

        self.logger = logging.getLogger(__name__)

        self.size_in_memory = 0
        self.result = {}
        self.finalize_step = []

        self.is_initialized = False

        self.output_parser_mode = "basic"

    def initialize(self, session):
        """
        intitialize method is called by the Session the engine is registered.

        :param session: the Session that will drive it
        :return:
        """
        self.logger.debug("Engine %s Initializing.", self.name)
        self._session = session
        self._number_of_processed_traces = 0
        self._initialize()
        self.is_initialized = True

    def update(self, batch):
        """

        :param batch: a TraceBatch
        :return:
        """
        self.logger.debug("Engine %s update with batch %s.", self.name, batch)

        if not self.is_initialized:
            raise ValueError("%s Engine need first to be initialized ." % self.name)

        self.logger.debug("%s Engine updating .", self.name)
        self._update(batch)
        self._number_of_processed_traces += len(batch)

    def finalize(self):
        self.logger.debug("Engine %s Finalizing.", self.name)
        self.finalize_step.append(self._number_of_processed_traces)
        return self._finalize()

    def get_results():
        return self.finalize()

    def clean(self):

        self.logger.debug("Engine %s Cleaning.", self.name)

        if self._number_of_processed_traces not in self.finalize_step:
            self.logger.warning(
                "%s Engine cannot be cleaned, finalize() has not been called.",
                self.name,
            )
            return
        self._clean()


class MeanEngine(Engine):
    """
    MeanEngine is an Engine whose role is to compute the mean of the leakage delivered by the Session.

    (MeanEngine is by default added to any Session under the name 'mean')
    """

    def __init__(self):
        """
        MeanEngine Consructor.

        """
        Engine.__init__(self, "mean")
        self.logger.debug("Creating MeanEngine.")

    def _initialize(self):
        """
        Initialize the accumulators needed by MeanEngine
        :return:
        """
        self.size_in_memory += np.prod(self._session.leakage_shape) * 8
        self._acc_x = np.zeros(self._session.leakage_shape, dtype=np.double)

    def _update(self, batch):
        """
        Update MeanEngine from batchs.

        :param batch: batch of traces delivered by the session: batch = leakages,values

        """
        for leakage in batch.leakages:
            self._acc_x += leakage

        # self._acc_x += (batch.leakages).sum(0)

    def _finalize(self):
        """
        Output the mean of the leakage processed by the session.
        :return: the mean of the leakage processed by the session.
        """
        return np.nan_to_num(self._acc_x / self._number_of_processed_traces, False)

    def _clean(self):
        pass  # Never clean MeanEngine (it can be used by other engines)


class VarEngine(Engine):
    """
    VarEngine is an Engine whose role is to compute the mean of the leakage delivered by the Session.

    (VarEngine is by default added to any Session under the name 'mean')
    """

    def __init__(self):
        """
        VarEngine Consructor.
        """
        Engine.__init__(self, "var")
        self.logger.debug("Creating VarEngine.")

    def _initialize(self):
        """
        Initialize the accumulators needed by VarEngine
        :return:
        """
        self._acc_x2 = np.zeros(self._session.leakage_shape, dtype=np.double)
        self.size_in_memory += np.prod(self._session.leakage_shape) * 8

    def _update(self, batch):
        # for leakage in batch.leakages:
        #    self._acc_x2 += np.square(leakage)
        self._acc_x2 += np.square(batch.leakages, dtype=np.double).sum(0)

    def _finalize(self):
        """
        Output the mean of the leakage processed by the session.
        :return: the mean of the leakage processed by the session.
        """
        return np.nan_to_num(
            (self._acc_x2 / self._number_of_processed_traces)
            - self._session["mean"].finalize() ** 2,
            False,
        )

    def _clean(self):
        pass  # Never clean VarEngine (it can be used by other engines


class ContainerDumpEngine(Engine):
    """
    ContainerDumpEngine is an engine whose role is to simply dump the traces handled by the Session into a specified container.
    The container has to be created before.
    """

    def __init__(self, container_void):
        """

        :param session: The session on which the engine will run
        :param container_void: The container in which the batchs processed will be dumped
        """

        Engine.__init__(self, "dump")
        self.logger.debug("Creating ContainerDumpEngine.")

        self.container = container_void
        self.output_parser_mode = None

    def _initialize(self):
        self.current_offset = 0

    def _update(self, batch):
        self.container[self.current_offset : self.current_offset + len(batch)] = batch
        self.current_offset += len(batch)

    def _finalize(self):
        return self.container


class PearsonCorrelationEngine(Engine):
    """
    PearsonCorrelationEngine is an engine whose role is compute the Pearson Correlation coefficient between
    the observed trace leakages and a model function applied to the trace values

    The model function is a function who takes "value" as input and output a scalar.
    (eg it can compute the hamming weight at the output of a sbox)
    """

    def __init__(self, name, model):
        """

        """

        Engine.__init__(self, name)
        self._model = lambda x: int(model(x))
        self.logger.debug("Creating PearsonCorrelationEngine %s." % (name))

    def _initialize(self):
        """
        Initialize the accumulators needed by PearsonCorrelationEngine
        :return:
        """
        # self.size_in_memory += np.prod(self._session.leakage_shape) * 8

        self._acc_xm = np.zeros(self._session.leakage_shape, dtype=np.double)
        self._acc_m = 0
        self._acc_m2 = 0

    def _update(self, batch):

        model_values = list(map(self._model, batch.values))
        self._acc_m += sum(model_values)
        self._acc_m2 += sum(np.power(model_values, 2))
        self._acc_xm += np.dot(model_values, batch.leakages)

    def _finalize(self):

        m, v = self._session["mean"].finalize(), self._session["var"].finalize()
        numerator = (self._acc_xm / self._number_of_processed_traces) - (
            self._acc_m / self._number_of_processed_traces
        ) * m
        denominator = np.sqrt(
            v
            * (
                (self._acc_m2 / self._number_of_processed_traces)
                - (self._acc_m / self._number_of_processed_traces) ** 2
            )
        )
        mask = v == 0.0
        numerator[mask] = 0.0
        denominator[mask] = 1.0
        return np.nan_to_num(numerator / denominator)


class GroupedEngines(Engine):
    """
    GroupedEngines is an abstact engine whose role regroup engines within one.
    Useful when performing multiple charac/attacks at the same time.
    """

    def __init__(self, name, *engines):
        Engine.__init__(self, name)
        self.engines = engines

    def _initialize(self):
        [e.initialize(self._session) for e in self.engines]

    def _update(self, batch):
        [e.update(batch) for e in self.engines]

    def _finalize(self):

        result = [e.finalize() for e in self.engines]
        if isinstance(result[0], np.ndarray):
            return np.array(result)
        else:
            return result
