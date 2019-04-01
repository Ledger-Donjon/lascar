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
trace.py
"""
from . import TraceBatchContainer

import numpy as np

# class TraceBatch(_TraceBatch):
#     """
#     TraceBatch represents batches of Trace.
#     It is a tuple of two items:
#     - The first item is "leakages" and represents the side-channel observables
#     - The second item is "values" and represents the handled values during the observation of "leakages".
#
#     trace_batch = (leakages, values)
#
#     where leakages and value are numpy.arrays sharing the first same dimension (the size of the batch)
#
#     BEWARE Please  of attribute names:
#     For a Trace t, it is t.leakage and t.value
#     For a TraceBatch t, it is t.leakages and t.values (plurial)
#
#     """
#
#     def __new__(cls, *args):
#         super_obj = super(_TraceBatch, cls)
#
#         if len(args) != 2:
#             raise ValueError("TraceBatch: Only two arguments.")
#
#         if not isinstance(args[0], np.ndarray) or not isinstance(args[1], np.ndarray):
#             raise ValueError("TraceBatch: leakages and values must be numpy.ndarray.")
#         if args[0].shape[0] != args[1].shape[0]:
#             raise ValueError("TraceBatch: leakages and values must share the same first dimension.")
#
#         return super_obj.__new__(cls, args)
#
#     def __len__(self):
#         return len(self.leakages)
#
#     def __str__(self):
#         return 'TraceBatch with leakages:[%s, %s] values:[%s, %s]' % (
#         self.leakages.shape, self.leakages.dtype, self.values.shape, self.values.dtype)
#
#     def __repr__(self):
#         return "{}({})".format(
#             self.__class__.__name__,
#             ', '.join("{}=%r".format(name) for name in self._fields) % self)
