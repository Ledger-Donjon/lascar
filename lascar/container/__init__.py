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
container is the module containing all classes and functions dealing with Side channel data storage.
Various format, mechanisms to read, write, acquire, simulate side channel data.
"""

from .container import AbstractContainer
from .container import Container
from .container import TraceBatchContainer
from .filtered_container import FilteredContainer
from .filtered_container import RandomizedContainer
from .filtered_container import split_container
from .hdf5_container import Hdf5Container
from .multiple_container import MultipleContainer
from .simulation_container import BasicAesSimulationContainer
from .container import Trace

from .npy_container import NpyContainer
from .container import AcquisitionFromGenerators
from .container import AcquisitionFromGetters