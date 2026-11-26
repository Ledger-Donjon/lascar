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
multiple_container.py

    MultipleContainer concatenate containers already instanciated.

"""
import numpy as np

from .container import AbstractArray, Container, TraceBatchContainer


class MultipleContainer(Container):
    def __init__(self, *args, **kwargs):
        """
        Constructor.
        :param args: a *list of containers to be concatenated into the MultipleContainer
        """
        self._containers = args
        self.number_of_traces = sum([len(container) for container in args])
        self.leakages = AbstractArray(
            (self.number_of_traces,) + self._containers[0].leakages.shape[1:],
            self._containers[0].leakages.dtype,
        )
        self.values = AbstractArray(
            (self.number_of_traces,) + self._containers[0].values.shape[1:],
            self._containers[0].values.dtype,
        )

        super().__init__(**kwargs)
        self.logger.debug(
            "Creating MultipleContainer using %d Container." % len(self._containers)
        )

        # improvement (todo)
        current = 0
        self._t = np.zeros((self.number_of_traces + 1, 2), int)
        for i, container in enumerate(args):
            l = len(container)
            self._t[current : current + l, 0] = i
            self._t[current : current + l, 1] = range(l)
            current += l
        self._t[current] = i, l

    def __getitem__(self, item):

        self.logger.debug("__getitem__ with key %s %s" % (str(item), type(item)))
        if isinstance(item, int):
            container_idx, suboffset = self._t[item]
            return self._containers[container_idx][int(suboffset)]

        elif isinstance(item, slice):
            # check contiguity:
            if item.step is not None and item.step > 1:
                raise ValueError(
                    "MultipleContainer __getitem__ slice elements must be contiguous"
                )
            offset_begin = item.start if item.start else 0
            offset_end = item.stop if item.stop else self.number_of_traces

        elif isinstance(item, list):
            # check contiguity:
            if np.any(np.diff(np.array(item)) != 1):
                raise ValueError(
                    "MultipleContainer __getitem__ list elements must be contiguous"
                )
            offset_begin = item[0]
            offset_end = item[-1]
        else:
            raise ValueError(
                "MultipleContainer __getitem__ only accepts int, list and slices (contiguous)"
            )

        container_offset_begin, suboffset_offset_begin = self._t[offset_begin]
        container_offset_end, suboffset_offset_end = self._t[offset_end]

        # if container_offset_begin == container_offset_end:
        #     return self._containers[container_offset_end][suboffset_offset_begin:suboffset_offset_end]
        #
        # else:
        #     leakages = np.empty((offset_end - offset_begin,) + self._leakage_abstract.shape, self._leakage_abstract.dtype)
        #     values = np.empty((offset_end - offset_begin,) + self._value_abstract.shape, self._value_abstract.dtype)
        #     #first container:
        #     leakages[:len(container_offset_begin)-suboffset_offset_begin] =

        suboffsets = []
        if container_offset_begin == container_offset_end:
            suboffsets.append(
                [container_offset_begin, suboffset_offset_begin, suboffset_offset_end]
            )
        else:
            suboffsets.append(
                [
                    container_offset_begin,
                    suboffset_offset_begin,
                    len(self._containers[container_offset_begin]),
                ]
            )
            for i in range(container_offset_begin + 1, container_offset_end):
                suboffsets.append([i, 0, len(self._containers[i])])
            suboffsets.append([container_offset_end, 0, suboffset_offset_end])

        # TODO: Find a better solution...
        leakages = np.concatenate(
            [
                self._containers[suboffset[0]][suboffset[1] : suboffset[2]].leakages
                for suboffset in suboffsets
            ]
        )
        values = np.concatenate(
            [
                self._containers[suboffset[0]][suboffset[1] : suboffset[2]].values
                for suboffset in suboffsets
            ]
        )

        # leakages = np.zeros((offset_end - offset_begin,) + self._leakage_abstract.shape, self._leakage_abstract.dtype)
        # values = np.zeros((offset_end - offset_begin,) + self._value_abstract.shape, self._value_abstract.dtype)
        #
        #
        # print("leakages,values", leakages.shape, values.shape)
        # print()
        # print([str(i) for i in self._containers])
        # print("offsets", offset_begin, offset_end)
        # print("suboffsets", suboffsets)
        # print("leakages", leakages.shape)
        # print("values", values.shape)
        #
        # i = 0
        #
        # print("loop")
        # for suboffset in suboffsets:
        #     print("suboffset", suboffset)
        #     batch = self._containers[suboffset[0]][suboffset[1]:suboffset[2]]
        #     print('batch',batch)
        #     print('i:i+len', i, i+len(batch))
        #     print('leakages[i:i + len(batch)]',leakages[i:i + len(batch)].shape)
        #     leakages[i:i + len(batch)] = batch.leakages
        #     values[i:i + len(batch)] = batch.values
        #     i += len(batch)
        return TraceBatchContainer(leakages, values)

    def __len__(self):
        acc = 0
        for container in self._containers:
            acc += len(container)
        return acc

    @property
    def leakage_section(self):
        return self._leakage_section

    @leakage_section.setter
    def leakage_section(self, section):
        for c in self._containers:
            c.leakage_section = section
        self._leakage_section = section
        self._leakage_section_abstract = c._leakage_section_abstract
        self._leakage_abstract = c._leakage_abstract

    @property
    def leakage_processing(self):
        return self._leakage_processing

    @leakage_processing.setter
    def leakage_processing(self, processing):
        for c in self._containers:
            c.leakage_processing = processing
        self._leakage_processing = processing
        self._leakage_section_abstract = c._leakage_section_abstract
        self._leakage_abstract = c._leakage_abstract

    @property
    def value_section(self):
        return self._value_section

    @value_section.setter
    def value_section(self, section):
        for c in self._containers:
            c.value_section = section
        self._value_section = section
        self._value_section_abstract = c._value_section_abstract
        self._value_abstract = c._value_abstract

    @property
    def value_processing(self):
        return self._value_processing

    @value_processing.setter
    def value_processing(self, processing):
        for c in self._containers:
            c.value_processing = processing
        self._value_processing = processing
        self._value_section_abstract = c._value_section_abstract
        self._value_abstract = c._value_abstract

    def get_leakage_mean_var(self):
        """
        Compute mean/var of the leakage.
        :return: mean/var of the container leakages
        """

        sum_x = np.zeros((self._leakage_abstract.shape))
        sum_x2 = np.zeros((self._leakage_abstract.shape))
        
        for c in self._containers:
            m, v = c.get_leakage_mean_var()
            
            sum_x += m * len(c)
            sum_x2 += (v + m ** 2) * len(c)

        return sum_x / len(self), (sum_x2 / len(self)) - (sum_x / len(self)) ** 2
