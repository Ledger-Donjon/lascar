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
snr_engine.py
"""

import numpy as np

from . import PartitionerEngine

class SnrEngine(PartitionerEngine):
    """
    SnrEngine is a PartitionerEngine used to compute the Signal-to-Noise-Ratio on Side-Channel Traces.


    (Stefan Mangard, Elisabeth Oswald, and Thomas Popp. Power analysis attacks -
    revealing the guesses of smart cards. Springer, 2007.)

    It needs a partition_function that will take trace values as an input and returns output within partition_range.
    """

    def __init__(self, name, partition_function, partition_range, jit = True):
        """
        :param name: 
        :param partition_function: function that will take trace values as an input and returns output within partition_range.
        :param partition_range: possible values for the partitioning.
        """
        
        PartitionerEngine.__init__(self, name, partition_function, partition_range, 1, jit)
        self.logger.debug(
            'Creating SnrEngine  "%s" with %d classes.' % (name, len(partition_range))
        )

    def _finalize(self):
        """
        SNR = V[E[L|X]] / E[V[L|X]]
        Note that E[V[L|X]] + V[E[L|X]] = V[L] (law of total variance)
        We can hence compute SNR using only one accumulator + the variance
        Note that we should beware of ponderation during the computations of conditional expressions
        """
        
        acc = np.zeros(self._acc_x_by_partition.shape[2:], np.double)
        
        number_of_partitions = 0
        total_nb_of_traces = self._partition_count.sum()
        for v in self._partition_range:
            i = self._partition_range_to_index[v]
            if not self._partition_count[i]:
                continue

            # we will do the division by total number once at the end
            acc += (self._acc_x_by_partition[0, i]**2) / self._partition_count[i]

        V_E_cond = ((acc / total_nb_of_traces) - (self._session["mean"].finalize()) ** 2)
        return np.nan_to_num(
            1./(self._session["var"].finalize() / V_E_cond -1),
            False,
        )
        