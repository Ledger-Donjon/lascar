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

import numpy as np
import itertools
from . import PartitionerEngine


class TTestEngine(PartitionerEngine):
    """
    TtestEngine is a PartitionerEngine used to compute Welch's T-test on Side-Channel Traces

    (Gilbert Goodwill, Benjamin Jun, Josh Jaffe, and Pankaj Rohatgi. A
    testing methodology for side channel resistance validation. NIST noninvasive
    attack testing workshop, 2011. http://csrc.nist.gov/news_events/
    non-invasive-attack-testing-workshop/papers/08_Goodwill.pdf.)

    It needs as en input a partition_function that will take trace values as an input and returns 0 or 1
    (2 partitions_values).

    """

    def __init__(self, name, partition_function):
        """

        :param name:
        :param partition_function: partition_function that will take trace values as an input and returns 0 or 1
        """
        PartitionerEngine.__init__(self, name, partition_function, range(2), 2)
        self.logger.debug('Creating TtestEngine  "%s". ' % (name))

    def _finalize(self):
        m0 = self._acc_x_by_partition[0, 0] / self._partition_count[0]
        m1 = self._acc_x_by_partition[0, 1] / self._partition_count[1]

        v0 = (self._acc_x_by_partition[1, 0] / self._partition_count[0]) - m0 ** 2
        v1 = (self._acc_x_by_partition[1, 1] / self._partition_count[1]) - m1 ** 2

        return np.nan_to_num(
            (m0 - m1)
            / np.sqrt(
                (v0 / self._partition_count[0]) + (v1 / self._partition_count[1])
            ),
            False,
        )


def compute_ttest(*containers, batch_size=100):
    """
    Compute Welch's TTest from distinct containers: no need of partitioning function, since each container contain only one of each criterion

    :param *containers:
    :return:
    """
    # first compute each mean/variance:
    means = []
    pseudo_vars = []

    for i, container in enumerate(containers):
        mean, var = container.get_leakage_mean_var()

        means.append(mean)
        pseudo_vars.append(var / len(container))

    return np.vstack(
        [
            (means[i] - means[j]) / np.sqrt(pseudo_vars[i] + pseudo_vars[j])
            for i, j in itertools.combinations(range(len(containers)), 2)
        ]
    )
