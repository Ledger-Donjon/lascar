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
partitioner_engine.py
"""
import numpy as np

from .engine import Engine


# class PartitionFunction:
#     def __init__(self, func, size):
#         self.function = func
#         self.size = size
#
#     def __call__(self, arg):
#         return self.function(arg)
#
#
# class guessFunction:
#     def __init__(self, func, guesses):
#         self.function = func
#         self.size = len(guesses)
#         self.guesses = guesses
#
#     def __call__(self, value):
#         return np.array([self.function(value,guess) for guess in self.guesses])


class PartitionerEngine(Engine):
    """
    PartitionEngine is an abstract splecialized Engine which role is to partition the 'leakages', according
    to a 'partition_value' computed from the 'values'.

    The partition_value is computed by a fonction called 'partition', which ouputs are in partition_range.

    partition_value = partition(value)
    0 <= partition_value < partition_size
    """

    def __init__(self, name, partition_function, partition_range, order, jit=True):
        """
        PartitionEngine
        :param name: the name chosen for the Engine
        :param session: the Session that will drive it
        :param partition_function: a function (or callable) which will be applied to the trace values and return a positive integer
        :param partition_range: the possible partition_values
        :param order: the order needed by the engine ( order=1: sum of leakages, order=2: sum of square of leakages,...)

        """

        if isinstance(partition_range, int):
            self._partition_range = range(partition_range)
        else:
            self._partition_range = partition_range

        self._partition_range = np.array(self._partition_range, dtype=np.uint32)
        self._partition_size = len(self._partition_range)
        self._partition_range_to_index = np.zeros((self._partition_range.max()+1,), dtype=np.uint32)
        for i,j in enumerate(self._partition_range):
            self._partition_range_to_index[j] = i

        self._order = order

        self.jit = jit
        if jit:
            try:
                from numba import jit
            except Exception:
                raise Exception(
                    "Cannot jit without Numba. Please install Numba or consider turning off the jit option"
                )
            self._partition_function = jit(nopython=True)(partition_function)
        else:
            self._partition_function = partition_function
        Engine.__init__(self, name)

    def _initialize(self):

        self._acc_x_by_partition = np.zeros(
            (self._order, self._partition_size) + self._session.leakage_shape,
            dtype=np.double,
        )

        # acc_x_by_partition[i,j,k] = sum( (leakages[k])**i | partition = j)

        self._partition_count = np.zeros((self._partition_size,), dtype=np.double)

        self.size_in_memory += self._acc_x_by_partition.nbytes
        self.size_in_memory += self._partition_count.nbytes
        if self.jit:
            from numba import jit

            @jit(nopython=True)
            def jitted_update(batchvalues, batchleakages, pfunc = self._partition_function, psize = self._partition_size, rng2idx = self._partition_range_to_index, order = self._order):
                pcount = np.zeros((psize,), dtype=np.uint32)
                acc_x = np.zeros((order, psize, batchleakages.shape[1]), dtype=np.double)

                for pv in np.arange(batchvalues.shape[0]):
                    idx = rng2idx[pfunc(batchvalues[pv])]
                    pcount[idx] += 1
                    acc_x[0, idx] += batchleakages[pv]
                    for o in range(1,order):
                        acc_x[o, idx] += np.power(batchleakages[pv], o + 1)
                
                return pcount, acc_x

            def new_update(batch):
                pcount, acc_x = jitted_update(batch.values, batch.leakages)
                self._partition_count += pcount
                self._acc_x_by_partition += acc_x

            self._update = new_update 
        else:
            self._update = self._base_update

    def _base_update(self, batch):
        partition_values = list(map(self._partition_function, batch.values))
        for i, v in enumerate(partition_values):
            idx = self._partition_range_to_index[v]
            self._partition_count[idx] += 1
            for o in range(0, self._order):
                self._acc_x_by_partition[
                    o, idx
                ] += np.power(batch.leakages[i], o + 1, dtype=np.double)

    def _finalize(self):
        pass

    def _clean(self):
        del self._acc_x_by_partition
        del self._partition_count
        self.size_in_memory = 0

    def get_mean_by_partition(self):
        """
        Compute a np.array containing the means by partiion

        E[ leakage | partition(value) = i) for i in partiton_values

        :return: np.array containing the means by partition.
        """

        acc = np.zeros(self._acc_x_by_partition.shape[1:], np.double)
        for v in self._partition_range:
            i = self._partition_range_to_index[v]
            acc[i] = self._acc_x_by_partition[0, i] / self._partition_count[i]

        return acc
