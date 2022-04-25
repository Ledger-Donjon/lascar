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

from . import PartitionerEngine
from bisect import bisect
from scipy.stats import chi2_contingency


class Chi2TestEngine(PartitionerEngine):
    """
    TtestEngine is a PartitionerEngine used to compute Pearson's chi square test on Side-Channel Traces

    (Amir Moradi, Bastian Richter, Tobias Schneider, and François-Xavier Standaert.
    Leakage detection with the x2-test. IACR Trans. Cryptogr. Hardw. Embed. Syst.,
    2018(1):209–237, 2018. https://tches.iacr.org/index.php/TCHES/article/view/838/790)

    It needs as en input a partition_function that will take trace values as an input and returns 0 or 1
    (2 partitions_values).

    """

    def __init__(self, name, partition_function, n_bins, bin_range):
        """

        :param name:
        :param partition_function: partition_function that will take trace values as an input and returns 0 or 1
        :param n_bins: number of bins for the histogram
        :param bin_range: (min, max) lower and upper bounds for the bins
        """
        PartitionerEngine.__init__(self, name, partition_function, range(2), 2)
        self.logger.debug('Creating Chi2TestEngine  "%s". ' % (name))

        bin_width = (bin_range[1]-bin_range[0])/n_bins
        self._bin_starts = [bin_range[0]+i*bin_width for i in range(n_bins)]


    def _initialize(self):
        PartitionerEngine._initialize(self)
        self._histogram = np.zeros((self._partition_size,)+self._session.leakage_shape+(len(self._bin_starts),), dtype=np.dtype("uint32"))
        self._update = self._chi2_update

    def _chi2_update(self, batch):
        partition_values = list(map(self._partition_function, batch.values))
        for i, v in enumerate(partition_values):
            idx_part = self._partition_range_to_index[v]
            self._partition_count[idx_part] += 1
            # Increment the right bin for every sample in the trace
            for idx_sample in np.ndindex(self._session.leakage_shape):
                x = batch.leakages[i,idx_sample]
                # Use dichotomy to find bin index
                idx_bin = bisect(self._bin_starts, x) - 1
                self._histogram[idx_part,idx_sample,idx_bin] += 1

    def _finalize(self):
        # P stores the final p-value for each point in time
        P = np.zeros(self._session.leakage_shape)
        for idx_sample in np.ndindex(self._session.leakage_shape):
            # Filter out zero columns for a given point in time
            condition = [not all([self._histogram[idx_part][idx_sample][k] == 0 for idx_part in range(self._partition_size)]) for k in range(len(self._bin_starts))] 
            # Build contingency tables at each point in time
            tables = np.zeros((self._partition_size, condition.count(True)))
            for idx_part in range(self._partition_size):
                tables[idx_part] = self._histogram[idx_part][idx_sample][condition]
    
            _, p, _, _ = chi2_contingency(tables)
            if p == 0:
                p = np.finfo(float).tiny
            P[idx_sample] = p

        return P

    def _clean(self):
        del self._histogram
        del self._bin_starts
        PartitionerEngine._clean(self)
