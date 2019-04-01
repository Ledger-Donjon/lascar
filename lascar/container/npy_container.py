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

from lascar.container import TraceBatchContainer, Container


class NpyContainer(Container):
    """
    NpyContainer is a Container based upon .npy file format.

    Two .npy files (one for the leakages, one for the values) are used by lascar
    using memmap (all data are not loaded in memory, contrary to np.load)
    """

    def __init__(self, leakages_filename, values_filename, **kwargs):
        """
        Basic constructor

        :param leakages_filename: name of the npy file corresponding to the leakages
        :param values_filename: name of the npy file corresponding to the values
        :param kwargs: additional Container keyword arguments

        """

        self.leakages = np.lib.format.open_memmap(leakages_filename,'r+')
        self.values = np.lib.format.open_memmap(values_filename,'r+')

        Container.__init__(self, **kwargs)

        self.logger.debug('Creating NpyContainer from files %s / %s.'%(leakages_filename, values_filename) )

    def __getitem__(self, key):
        return TraceBatchContainer.__getitem__(self, key)

    def __setitem__(self, key, value):
        TraceBatchContainer.__setitem__(self, key, value)


    def _void_container(leakages_filename, values_filename, number_of_traces, leakage_shape, leakage_dtype, value_shape, value_dtype,
                        leakages_dataset_name="leakages", values_dataset_name="values", **kwargs):
        """

        """

        leakages = np.lib.format.open_memmap(leakages_filename,"w+",shape=(number_of_traces,) + leakage_shape, dtype=leakage_dtype)
        values = np.lib.format.open_memmap(values_filename,"w+",shape=(number_of_traces,) + value_shape, dtype=value_dtype)

        return NpyContainer(leakages_filename, values_filename, **kwargs)

    @staticmethod
    def export(container, leakages_filename, values_filename, name=None, batch_size=100):
        """
        export method is used to export an existing container into an NpyContainer.

        It creates a session and use a ContainerDumpEngine to recopy the traces delivered by the original container
        into a NpyContainer.

        :param container: container to be exported
        :param leakages_filename: name of the npy file to create corresponding to the leakages
        :param values_filename: name of the npy file to create corresponding to the values
        :param name: name for the session
        :param batch_size: batch_size for the session
        :return: 
        """

        leakage, value = container[0]
        out = NpyContainer._void_container(leakages_filename, values_filename, container.number_of_traces, leakage.shape, leakage.dtype,
                                           value.shape, value.dtype)

        from lascar import Session
        from lascar.engine import ContainerDumpEngine

        session = Session(container, engine=ContainerDumpEngine(out), name=name if name else 'NpyContainer')
        session.run(batch_size)

        return out
