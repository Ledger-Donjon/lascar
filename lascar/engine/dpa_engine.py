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
dpa_lsb_engine.py
"""
import numpy as np

from . import GuessEngine


class DpaEngine(GuessEngine):
    """
    DpaEngine is a GuessEngine used to perform Differential Power Analysis.

    (P. Kocher, J. Jaffe, and B. Jun. Differential Power Analysis. In M. Wiener, editor,
    Advances in Cryptology – CRYPTO ’99, volume 1666 of Lecture Notes in Computer
    Science, pages 388–397. Springer, 1999.)

    Given a selection_function under a guess guess, DpaEngine separates leakages into two sets,
    and output, for each guess guess, the difference betwenn the means of those two sets.

    """

    def __init__(self, name, selection_function, guess_range, solution=None):
        """

        :param name:
        :param selection_function: takes a value and a guess_guess as input, returns 0 or 1.
        :param guess_range: what are the values for the guess guess
        :param solution: if known, indicate the correct guess guess.
        """
        GuessEngine.__init__(self, name, selection_function, guess_range, solution)
        self.output_parser_mode = "max"
        self.logger.debug('Creating DpaEngine \"%s\" with %d guesses.', name, len(guess_range))

    def _initialize(self):
        self._acc_x = np.zeros((self._number_of_guesses, 2,) + self._session.leakage_shape, np.double)
        self._count_x = np.zeros((self._number_of_guesses, 2,), np.double)

    def _update(self, batch):
        y = np.array([[self._function(d, guess) for guess in self._guess_range] for d in batch.values])

        for i in range(len(batch)):
            y = np.array([self._function(batch.values[i], guess) for guess in self._guess_range])

            idx_0 = np.where(y == 0)[0]
            idx_1 = np.where(y == 1)[0]

            self._acc_x[idx_0, 0] += batch.leakages[i]
            self._count_x[idx_0, 0] += len(idx_0)

            self._acc_x[idx_1, 1] += batch.leakages[i]
            self._count_x[idx_1, 1] += len(idx_1)

    def _finalize(self):
        """
        for each guess, returns the square of difference of the means of the two classes
        """
        return np.nan_to_num([((self._acc_x[guess, 1] / self._count_x[guess, 1]) - (
                self._acc_x[guess, 0] / self._count_x[guess, 0])) ** 2 for guess in self._guess_range])
