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
from math import comb
from . import PartitionerEngine


class TTestEngine(PartitionerEngine):
    """
    TtestEngine is a PartitionerEngine used to compute Welch's T-test on Side-Channel Traces

    (Gilbert Goodwill, Benjamin Jun, Josh Jaffe, and Pankaj Rohatgi. A
    testing methodology for side channel resistance validation. NIST noninvasive
    attack testing workshop, 2011. http://csrc.nist.gov/news_events/
    non-invasive-attack-testing-workshop/papers/08_Goodwill.pdf.)

    It needs as input a partition_function that will take trace values as an input and returns 0 or 1
    (2 partitions_values).

    """

    def __init__(self, partition_function, analysis_order=1, name=None):
        """

        :param name:
        :param partition_function: partition_function that will take trace values as an input and returns 0 or 1
        """
        if name is None:
            name = "t-test"
        PartitionerEngine.__init__(self, partition_function, range(2), 2, name=name)
        self.logger.debug('Creating TtestEngine  "%s". ' % (name))
        self._analysis_order = analysis_order

    def _initialize(self):
        super()._initialize()
        if self._analysis_order > 1:
            self._central_sums = np.zeros(
                    (2 * self._analysis_order + 1, self._partition_size) + self._session.leakage_shape,
                    dtype=np.double,
                    )

            self._estimated_means = np.zeros(
                    (self._partition_size,) + self._session.leakage_shape,
                    dtype=np.double,
                    )


    def update(self, batch):
        """
        One-pass update formulas from:

        Formulas for Robust, One-Pass Parallel Computation of Covariances and Arbitrary-Order Statistical Moments,
        P. Pébay, 2008
        (https://www.osti.gov/servlets/purl/1028931)
        """
        super().update(batch)

        if self._analysis_order <= 1:
            return

        indexes = [
                np.where(np.apply_along_axis(self._partition_function, 1, batch.values) == val)[0]
                for val in range(self._partition_size)
                ]

        for idx in range(self._partition_size):
            l = batch.leakages[indexes[idx]]

            n = self._partition_count[idx]
            n2 = len(l)
            n1 = n - n2

            # Compute new estimated mean
            m1 = self._estimated_means[idx]
            m2 = l.mean(0)
            delta = m2 - m1
            self._estimated_means[idx] = m1 + n2 * (delta / n)

            cs1 = np.copy(self._central_sums)
            cs2 = np.zeros(
                    (2 * self._analysis_order + 1,) + self._session.leakage_shape,
                    dtype=np.double,
                    )

            # Update central sums
            for o in range(2, 2 * self._analysis_order + 1):
                cs2[o] = np.power(l - m2, o).sum(0)

                # First batch
                if n1 == 0:
                    self._central_sums[o, idx] = cs2[o]
                    continue

                s = np.power(n1 * n2 * delta / n, o)
                s *= ( np.power(1 / n2, o - 1)
                        - np.power(-1 / n1, o - 1) )
                for k in range(1, o - 1):
                    tmp = np.power(delta, k) * comb(o, k)
                    tmp *= ( np.power(-n2 / n, k) * cs1[o - k, idx]
                            + np.power(n1 / n, k) * cs2[o - k] )
                    s += tmp

                self._central_sums[o, idx] += cs2[o] + s

    def _finalize(self):
        """
        One-pass variances formulas and original idea from:

        Leakage Assessment Methodology – a clear roadmap for side-channel evaluations –,
        T. Schneider and A. Moradi, 2015
        (https://eprint.iacr.org/2015/207)
        """
        n0 = self._partition_count[0]
        n1 = self._partition_count[1]

        if self._analysis_order == 1:
            m0 = self._acc_x_by_partition[0, 0] / n0
            m1 = self._acc_x_by_partition[0, 1] / n1

            v0 = (self._acc_x_by_partition[1, 0] / n0) - m0 ** 2
            v1 = (self._acc_x_by_partition[1, 1] / n1) - m1 ** 2
        else:

            #Central moments
            central_moments = np.zeros(
                    (2 * self._analysis_order + 1, self._partition_size) + self._session.leakage_shape,
                    dtype=np.double,
                    )
            for o in range(2, 2 * self._analysis_order + 1):
                for i in range(self._partition_size):
                    central_moments[o, i] = self._central_sums[o, i] / self._partition_count[i]

            # Standardised moments
            standardized_moments = np.zeros(
                    (2 * self._analysis_order + 1, self._partition_size) + self._session.leakage_shape,
                    dtype=np.double,
                    )

            if self._analysis_order > 2:
                standard_deviations = np.sqrt(central_moments[2])
                standardized_moments[2] = np.ones(standardized_moments[2].shape)
                for o in range(3, 2 * self._analysis_order + 1):
                    standardized_moments[o] = central_moments[o] / np.power(standard_deviations, o)



            # Variance of preprocessed traces
            variances = np.zeros(
                    (2 * self._analysis_order + 1, self._partition_size) + self._session.leakage_shape,
                    dtype=np.double,
                    )
            variances[1] = central_moments[2]
            variances[2] = central_moments[4] - np.square(central_moments[2])
            for i in range(3, self._analysis_order + 1):
                variances[i] = standardized_moments[2 * i] - np.square(standardized_moments[i])

            if self._analysis_order == 2:
                m0 = central_moments[2, 0]
                m1 = central_moments[2, 1]
            else:
                m0 = standardized_moments[self._analysis_order, 0]
                m1 = standardized_moments[self._analysis_order, 1]

            v0 = variances[self._analysis_order, 0]
            v1 = variances[self._analysis_order, 1]

        return np.nan_to_num(
            (m0 - m1)
            / np.sqrt((v0 / n0) + (v1 / n1)),
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
