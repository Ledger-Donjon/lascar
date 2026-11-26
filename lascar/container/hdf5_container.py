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
hdf5_container.py
"""
import h5py

from lascar.container import TraceBatchContainer, Container


class Hdf5Container(Container):
    """
    Hdf5Container is a Container based upon hdf5 files (with h5py).

    A hdf5 file emulates a file system and can contains two types of objects:
    - Group = folder
    - Dataset = multidimensional array of data (which are loaded into np.array thanks to h5py)

    A Hdf5Container consists in a hdf5 file which containes at least two datasets;
    - 1 dataset containing the leakages
    - 1 dataset containing the values
    """

    def __init__(
        self,
        filename,
        leakages_dataset_name="leakages",
        values_dataset_name="values",
        mode="r",
        **kwargs
    ):
        """
        Basic constructor

        :param filename:
        :param leakages_dataset_name:
        :param values_dataset_name:
        :param mode: mode for opening filename: default is read-only
        """

        self._file = h5py.File(filename, mode)
        self.leakages = self._file[leakages_dataset_name]
        self.values = self._file[values_dataset_name]

        Container.__init__(self, **kwargs)

        self.logger.debug(
            "Creating Hdf5Container from file %s with datasests %s/%s."
            % (filename, leakages_dataset_name, values_dataset_name)
        )

    def __getitem__(self, key):
        return TraceBatchContainer.__getitem__(self, key)

    def __setitem__(self, key, value):
        TraceBatchContainer.__setitem__(self, key, value)

    def __len__(self):
        return len(self.leakages)

    @staticmethod
    def void_container(
        filename,
        number_of_traces,
        leakage_shape,
        leakage_dtype,
        value_shape,
        value_dtype,
        leakages_dataset_name="leakages",
        values_dataset_name="values",
        **kwargs
    ):
        """
        void_container is a static method for building an empty Hdf5Container with the specified parameters.

        :param filename: container filename
        :param number_of_traces:
        :param leakage_shape: shape of 1 leakage
        :param leakage_dtype: dtype of leakage
        :param value_shape: shape of 1 value
        :param value_dtype: dtype of value
        :param leakages_dataset_name:
        :param values_dataset_name:
        :return: an empty Hdf5Container
        """
        try:  # if file exists
            file = h5py.File(filename,"a")
            if leakages_dataset_name in file:
                del file[leakages_dataset_name]
            if values_dataset_name in file:
                del file[values_dataset_name]
        except:
            file.close()
            file = h5py.File(filename, "w")

        file.create_dataset(
            leakages_dataset_name, (number_of_traces,) + leakage_shape, leakage_dtype
        )
        file.create_dataset(
            values_dataset_name, (number_of_traces,) + value_shape, value_dtype
        )
        file.close()

        return Hdf5Container(
            filename, leakages_dataset_name, values_dataset_name, mode="r+", **kwargs
        )

    @staticmethod
    def export(
        container,
        filename,
        name=None,
        leakages_dataset_name="leakages",
        values_dataset_name="values",
        batch_size=100,
    ):
        """
        export method is used to export an existing container into an Hdf5Container.

        It creates a session and use a ContainerDumpEngine to recopy the traces delivered by the original container.

        :param container: container to be exported
        :param filename: name of the Hdf5Container to build
        :param leakages_dataset_name:
        :param values_dataset_name:
        :param batch_size:
        :return:
        """

        leakage, value = container[0]
        out = Hdf5Container.void_container(
            filename,
            len(container),
            leakage.shape,
            leakage.dtype,
            value.shape,
            value.dtype,
            leakages_dataset_name,
            values_dataset_name,
        )

        from lascar import Session
        from lascar.engine import ContainerDumpEngine

        session = Session(
            container,
            engine=ContainerDumpEngine(out),
            name=name if name else "Hdf5Container",
        )
        session.run(batch_size)
        # Adding mean/var: to leakage_dataset_name as attributes
        try:
            out._file[leakages_dataset_name].attrs["mean"] = session["mean"].finalize()
            out._file[leakages_dataset_name].attrs["var"] = session["var"].finalize()
        except:
            pass

        return out

    def get_leakage_mean_var(self):
        """
        Compute mean/var of the leakage.
        :return: mean/var of the container leakages
        """
        try:
            mean, var = self.leakages.attrs["mean"], self.leakages.attrs["var"]
            return self.apply_both_leakage(mean), self.apply_both_leakage(var)

        except:
            mean, var = Container.get_leakage_mean_var(self)

            try:
                self.leakages.attrs["mean"] = mean
                self.leakages.attrs["var"] = var
            except:
                pass
        return mean, var
