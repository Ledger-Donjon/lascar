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
cpa_engine.py
"""
import numpy as np

from . import GuessEngine
from . import PartitionerEngine


class CpaEngine(GuessEngine):
    """
    CpaEngine is a GuessEngine used to perform Correlation Power Analysis.

    (E. Brier, C. Clavier, and F. Olivier. Correlation Power Analysis with a Leakage
    Model. In M. Joye and J.-J. Quisquater, editors, Cryptographic Hardware and Embedded
    Systems – CHES 2004, volume 3156 of Lecture Notes in Computer Science,
    pages 16–29. Springer, 2004.)

    Given a selection_function on the values under a guess guess (emulating a leakage model),
    Cpa engines computes, for each guess guess, the Pearson's correlation between the output of the selection_function
    and the corresponding leakages.
    """

    def __init__(self, name, selection_function, guess_range, solution=None, jit=True):
        """

        :param name:
        :param selection_function: takes a value and a guess_guess as input, returns a modelisation of the leakage for this (value/guess).
        :param guess_range: what are the values for the guess guess
        :param solution: if known, indicate the correct guess guess.
        """
        GuessEngine.__init__(self, name, selection_function, guess_range, solution, jit)
        self.logger.debug('Creating CpaEngine \"%s\" with %d guesses.' % (name, len(guess_range)))

        self.output_parser_mode = "argmax"

    def _initialize(self):
        self.size_in_memory += (np.prod(
            (self._number_of_guesses,) + self._session.leakage_shape) + 2 * self._number_of_guesses) * 8
        self._accM = np.zeros((self._number_of_guesses,), np.double)
        self._accM2 = np.zeros((self._number_of_guesses,), np.double)
        self._accXM = np.zeros((self._number_of_guesses,) + self._session.leakage_shape, np.double)

    def _update(self, batch):
        m = self._mapfunction(self._guess_range, batch.values)
        self._accM += m.sum(0)
        self._accM2 += (m ** 2).sum(0)
        self._accXM += np.dot(m.transpose(), batch.leakages)

    def _finalize(self):
        m, v = self._session["mean"].finalize(), self._session["var"].finalize()
        numerator = ((self._accXM / self._number_of_processed_traces) - np.outer( self._accM / self._number_of_processed_traces, m))
        denominator = np.sqrt(np.outer( self._accM2 / self._number_of_processed_traces - (self._accM / self._number_of_processed_traces) ** 2, v)) 
        mask = v==0.
        numerator[:, mask] = 0.
        denominator[:, mask] = 1.
        return np.nan_to_num(numerator / denominator)

    def _clean(self):
        del self._accM
        del self._accM2
        del self._accXM
        self.size_in_memory = 0


class CpaPartitionedEngine(PartitionerEngine, GuessEngine):
    """
    CpaPartitionedEngine is an optimization of CpaEngine, that can be used when the cardinal of the domain
    of the selection_function is low.

    In such a case, this engine first partitions the leakages according to a partitioning_function
     on this 'small' domain.
     Then one (or several) leakage_model can be applied on this partitioning.

     When dealing with appropriate data (enought number of traces, partition appropriated),
     the complexity of this engine is much lower than a classical CpaEngine, since the model is computed once one each
     partition_range values, instead of on all the traces values.

    Victor Lomn´e, Emmanuel Prouff, and Thomas Roche. Behind the Scene of Side
    Channel Attacks. In Kazue Sako and Palash Sarkar, editors, ASIACRYPT (1),
    volume 8269 of Lecture Notes in Computer Science, pages 506–525. Springer, 2013.
    """

    def __init__(self, name, partition_function, partition_range, selection_function, guess_range, solution=None):
        """

        :param name:
        :param partition_function: partition_function, takes a value and returns an int within partition_range
        :param partition_range: what are the possible outputs for the partition
        :param selection_function: selection_function: takes (partition_value,guess) as an input
        :param guess_range: what are the possible outputs for the guess guess
        :param leakage_model:
        :param solution:
        """
        PartitionerEngine.__init__(self, name, partition_function, partition_range, 1)
        GuessEngine.__init__(self, name, selection_function, guess_range, solution)
        self.logger.debug('Creating CpaPartitionedEngine \"%s\" with %d partitions, %d guesses.' % (
            name, len(self._partition_range), len(guess_range)))

    def _finalize(self):
        accXM = np.zeros((self._number_of_guesses,) + self._session.leakage_shape, np.double)
        accM = np.zeros((self._number_of_guesses,), np.double)
        accM2 = np.zeros((self._number_of_guesses,), np.double)

        for val in range(self._partition_size):
            models = np.array([self._function(val, guess) for guess in self._guess_range])
            accXM += np.outer(models, self._acc_x_by_partition[0, val])
            accM += models * self._partition_count[val]
            accM2 += (models ** 2) * self._partition_count[val]

        m, v = self._session["mean"].finalize(), self._session["var"].finalize()
        return np.nan_to_num(((accXM / self._number_of_processed_traces) - np.outer(
            accM / self._number_of_processed_traces, m)) / np.sqrt(np.outer(
            accM2 / self._number_of_processed_traces - (accM / self._number_of_processed_traces) ** 2, v)))

    def _clean(self):
        del self._accM
        del self._accM2
        del self._accXM
        self.size_in_memory = 0
