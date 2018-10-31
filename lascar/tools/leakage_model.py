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

"""

Classes for leakage models
"""

import numpy as np

try:
    from numba import jit
except  Exception:
    print("Numba not present. Jitter will be off.")


    def jit(*args, **kwargs):
        return lambda x: x

_hw = np.array(
    [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4, 1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5, 1, 2, 2, 3, 2, 3,
     3, 4, 2, 3, 3, 4, 3, 4, 4, 5, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4,
     3, 4, 4, 5, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 3, 4,
     4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5, 2, 3, 3, 4, 3, 4, 4, 5,
     3, 4, 4, 5, 4, 5, 5, 6, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6,
     6, 7, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 3, 4, 4, 5,
     4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 4, 5, 5, 6, 5, 6, 6, 7, 5, 6, 6, 7, 6, 7, 7, 8], dtype=np.uint8)


@jit(nopython=True)
def hamming(value):
    r = np.uint32(0)
    while value:
        r += _hw[value & 0xff]
        value >>= 8
    return r


@jit(nopython=True)
def hamming_weight(value):
    """
    Compute the hamming weight of an integer
    https://www.expobrain.net/2013/07/29/hamming-weights-python-implementation/
    :param value: the integer
    :return: the hamming weight of the value
    """
    value = int(value)
    value -= (value >> 1) & 0x5555555555555555
    value = (value & 0x3333333333333333) + ((value >> 2) & 0x3333333333333333)
    value = (value + (value >> 4)) & 0x0f0f0f0f0f0f0f0f
    return ((value * 0x0101010101010101) & 0xffffffffffffffff) >> 56


class LeakageModel:
    """
    LeakageModel is an abstract class.
    A leakage model is a callable object. It can be defined by a simple function,
    or by a class (like LeakageModel) overloading __call__
    """

    def __call__(self, value):
        pass


class HammingPrecomputedModel(LeakageModel):
    """
    HammingPrecomputedModel emulate the hamming weight leakage model by precomputing all the hamming weigths
     until a given values.
    """

    def __init__(self, max=256):
        """
        HammingWeightEightBitsModel constructor: precompute _table with the 256 values

        :param max: maximum value to precompute

        """
        self._table = np.zeros((max,), np.uint8)
        for i in range(max):
            self._table[i] = hamming_weight(i)

    def __call__(self, value):
        return self._table[value]


class BitLeakageModel(LeakageModel):
    """
    BitLeakageModel returns the value of a specified bit.
    """

    def __init__(self, bit):
        self._bit = bit

    def __call__(self, value):
        return (value >> self._bit) & 1
