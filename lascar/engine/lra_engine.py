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
# Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Adrian Thillard Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr, adrian.thillard@ledger.fr

"""
lra_engine.py
"""
from itertools import combinations
import numpy as np
from math import comb

from . import GuessEngine
from . import PartitionerEngine

def get_bit_coefficients(value, order):
    # return value as a sequence of bit coefficients,
    # ie, considering the binary expression of value 
    # it will return every bit combination up to the given order

    bits = [int(i) for i in "{:08b}".format(value)]
    
    # we always start with a constant 1
    res = [1]

    for o in range(order):
        for i in combinations(bits,o+1):
            res += [np.prod(i)]
    return np.array(res,dtype=np.uint)

class LraEngine(PartitionerEngine,GuessEngine):
    """
    LraEngine is a GuessEngine used to perform Linear Regression Analysis.
    It is implemented as a PartitionerEngine to allow for improvements as described in
    (M. Ouladj, S. Guilley, E. Prouff, On the Implementation Efficiency of Linear Regression-Based Side-Channel Attacks)

    Given a selection_function on the values under a guess guess (emulating a leakage model),
    LraEngine computes, for each guess guess, the goodness of fit, based on the coefficient of determination,
    between the output of the selection_function and the corresponding leakages.
    """
    def __init__(
        self,
        name,
        partition_function,
        partition_range,
        selection_function,
        guess_range,
        solution = None,
        regression_order = 1,
        size_target_value = 8,
    ):
        """
        :param name:
        :param partition_function: partition_function, takes a value and returns an int within partition_range
        :param partition_range: what are the possible outputs for the partition
        :param selection_function: selection_function: takes (partition_value,guess) as an input
        :param guess_range: what are the possible outputs for the guess guess. Note that this value should be a power of 2.
        :param solution:
        :param regression_order: the regression order (by default =1)
        :param size_target_value: the number of bits of the target value, that we are regressing (by default = 8). 
        """
        PartitionerEngine.__init__(self, name, partition_function, partition_range, 2)
        GuessEngine.__init__(self, name, selection_function, guess_range, solution)
        self.logger.debug(
            'Creating LraEngine "%s" with %d partitions, %d guesses.'
            % (name, len(self._partition_range), len(guess_range))
        )

        self._output_cardinality = len(self._partition_range)
        
        # from the order, we compute the number of coefficients that we will regress against
        # it is simply sum_i=0^{order} (binomial(size_target_value, i))
        # to the best of my knowledge, there is no closed form for that formula
        self._nb_of_coefs = 0
        for i in range(regression_order+1):
            self._nb_of_coefs += comb(size_target_value,i)

        # preprocess all prediction matrices
        self.P = np.zeros((len(guess_range), self._nb_of_coefs, self._output_cardinality))
        self.M = np.zeros((len(guess_range), self._output_cardinality, self._nb_of_coefs))
        for k in guess_range:
            for v in self._partition_range:
                x = self._partition_range_to_index[v]
                self.M[k][x]= get_bit_coefficients(selection_function(x,k),regression_order)
            self.P[k] = np.linalg.inv(self.M[k].T @ self.M[k]) @ self.M[k].T
        

    def _finalize(self):
        self.R = np.zeros(
            (self._number_of_guesses,) + self._session.leakage_shape, np.double
        )

        # compute the total sum of squares, from  acc_x_by_partition[i,j,k] = sum( (leakages[k])**i | partition = j)
        u =  self._acc_x_by_partition[0].sum(axis=0)
        v =  self._acc_x_by_partition[1].sum(axis=0)
        self.SST = v - (u ** 2) / self._partition_count.sum()
        
        # compute the coalesced matrix of traces
        self.L = np.array([self._acc_x_by_partition[0][i]/self._partition_count[i] for i in range(len(self._partition_range))])
        
        for k in range(self.P.shape[0]):
            beta = self.P[k] @ self.L
            epsilon = self.M[k] @ beta
            SSR = np.sum((epsilon - self.L)**2,axis=0)
            self.R[k] = 1 -(SSR/self.SST[None,:])
        return np.nan_to_num(self.R)

