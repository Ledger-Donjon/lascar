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
nicv_engine.py
"""
import numpy as np

from . import PartitionerEngine


class NicvEngine(PartitionerEngine):
    """
        NicvEngine is a PartitionerEngine used to compute the Normalized-Inter-Class-Variance on Side-Channel Traces.


        (S. Bhasin, J.-L. Danger, S. Guilley, Z. Najm, "
        NICV: Normalized Inter-Class Variance for Detection of Side-Channel Leakage",
        Cryptology ePrint Archive Report 2013/717, 2013.)

        It needs a partition_function that will take trace values as an input and returns output within partition_range.
        """

    def __init__(self, name, partition_function, partition_range):
        """

        :param name:
        :param partition_function: function that will take trace values as an input and returns output within partition_range.
        :param partition_range: possible values for the partitioning.
        """
        PartitionerEngine.__init__(self, name, partition_function, partition_range, 1)
        self.logger.debug(
            'Creating NicvEngine "%s" with %d classes.'
            % (name, len(self._partition_range))
        )

    def _finalize(self):

        acc = np.zeros(self._acc_x_by_partition.shape[2:], np.double)
        acc2 = np.zeros(self._acc_x_by_partition.shape[2:], np.double)

        number_of_partitions = 0
        for v in self._partition_range:
            i = self._partition_range_to_index[v]
            if not self._partition_count[i]:
                continue

            # tmp = self._acc_x_by_partition[0, i] / self._partition_count[i]
            acc += self._acc_x_by_partition[0, i] / self._partition_count[i]
            acc2 += (self._acc_x_by_partition[0, i] / self._partition_count[i]) ** 2
            # acc += tmp
            # acc2 += tmp * tmp
            number_of_partitions += 1

        return np.nan_to_num(
            ((acc2 / number_of_partitions) - (acc / number_of_partitions) ** 2)
            / self._session["var"].finalize(),
            False,
        )
