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
guess_engine.py
"""
import numpy as np

from . import Engine


class GuessEngine(Engine):
    """
    GuessEngine is a specialized Engine which is used when dealing with Side-Channel Analysis
     involving a guess guess (such as Dpa, Cpa, Mia, Template matching, ...).

     It requires a selection_function taking as an input the trace value and a guess guess which lives in guess_range.

    In the case where the solution is known, it can be passed as an argument.
    """

    def __init__(self, name, selection_function, guess_range, solution=None, jit=True):
        """

        :param name:
        :param selection_function:
        :param guess_range:
        :param solution:
        """
        Engine.__init__(self, name)
        self._function = selection_function
        self._guess_range = list(guess_range)
        self._number_of_guesses = len(guess_range)
        self._guess_range_to_index = {j: i for i, j in enumerate(self._guess_range)}
        self.solution = solution
        self.jit = jit
        if self.jit:
            try:
                from numba import jit, uint32
            except Exception:
                raise Exception(
                    "Cannot jit without Numba. Please install Numba or consider turning off the jit option"
                )

            try:
                f = jit(nopython=True)(self._function)
            except Exception:
                raise Exception(
                    "Numba could not jit this guess function. If it contains an assignment such as `value['your_string']`, Numba most likely cannot resolve it. Use the 'value_section' field of your container instead and set it to 'your_string'."
                )

            @jit(nopython=True)
            def hf(guessrange, batchvalues):
                out = np.zeros(
                    (batchvalues.shape[0], guessrange.shape[0]), dtype=np.uint32
                )
                for d in np.arange(batchvalues.shape[0]):
                    for guess in np.arange(guessrange.shape[0]):
                        out[d, guess] = f(batchvalues[d], guessrange[guess])
                return out

            self._mapfunction = hf
            self._guess_range = np.array(guess_range, dtype=np.uint32)

    def _mapfunction(self, guess_range, batch):
        return np.array(
            [[self._function(d, guess) for guess in guess_range] for d in batch]
        )
