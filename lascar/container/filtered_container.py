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
filtered_container.py
"""
from .container import AbstractContainer

import numpy as np


class FilteredContainer(AbstractContainer):
    """
    FilteredContainer is an AbstractContainer,
    which is built from another container, and will select only traces satisfying a specified condition.
    (usefull when doing traces synchronisation)
    """

    def __init__(self, container, filtering, **kwargs):
        """
        FilteredContainer constructor.
        :param container: the container to be filtered
        :param condition: an iterable delivering the traces to keep,  or a function taking a container Trace as input, and returns a boolean
        """
        self.container = container
        self.traces_indexes = []

        if hasattr(filtering, "__call__"):
            for i, trace in enumerate(container):
                if filtering(trace):
                    self.traces_indexes.append(i)

        elif hasattr(filtering, "__iter__") and hasattr(filtering, "__len__"):
            self.traces_indexes = filtering

        else:
            raise ValueError("filtering must be either a callable, or an iterable")

        AbstractContainer.__init__(self, len(self.traces_indexes), **kwargs)
        self.logger.debug("Creating FilteredContainer.")

    def generate_trace(self, idx):
        """
        Return the idx th trace of the container.
        :param idx: integer
        :return:
        """
        self.logger.debug("generate_trace with idx  %d", idx)

        return self.container[int(self.traces_indexes[idx])]


class RandomizedContainer(FilteredContainer):
    """
    RandomizedContainer is an AbstractContainer,
    which is built from another container, and will shuffle the trace order.
    """

    def __init__(self, container, **kwargs):
        FilteredContainer.__init__(
            self, container, np.random.permutation(container.number_of_traces), **kwargs
        )


def split_container(container, random=True, **kwargs):
    """
    :param container:
    :param random: boolean to indicate if spliting is done randomly
    :param kwargs: specify either the number of splits (number_of_splits), or the size of each split (size_of_splits)
    :return: a list of number_of_splits containers OR a list of containers of size_of_splits each.
    """
    n = container.number_of_traces
    if random:
        indexes = np.random.permutation(n)
    else:
        indexes = np.array(range(n))

    number_of_splits = kwargs.pop("number_of_splits", 0)
    size_of_splits = kwargs.pop("size_of_splits", 0)

    if (not number_of_splits and not size_of_splits) or (
        number_of_splits and size_of_splits
    ):
        raise ValueError(
            "split_container needs as kwargs EITHER number_of_splits OR size_of_splits"
        )

    if number_of_splits:
        m = number_of_splits
        offsets = np.split(indexes[: n - (n % m)], m)
        if n % m:
            offsets[-1] = np.append(offsets[-1], indexes[n - (n % m) :])

    if size_of_splits:
        m = size_of_splits
        offsets = [indexes[m * i : m * (i + 1)] for i in range(n // m)]
        if n % m:
            offsets[-1] = np.append(offsets[-1], indexes[n - (n % m) :])

    return [FilteredContainer(container, indexes, **kwargs) for indexes in offsets]
