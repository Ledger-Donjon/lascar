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

import h5py

from . import OutputMethod


class Hdf5OutputMethod(OutputMethod):
    """
    Hdf5OutputMethod is an OutputMethod that will store inside a hdf5 file the results from its tracked engines (for each output_step).

    For each engine tracked, a hdf5 group is added to the file
    For each output_step, a hdf5 dataset is added inside the group corresponding to each engine.

    A prefix can be specified if you want to store several Hdf5OutputMethod inside the same hdf5 file.

    in the end:

    hdf5_output_method[prefix + engine_name/output_step] contains  engine.results after output_step traces processed.

    """

    def __init__(self, filename, *engines, prefix=""):
        """

        :param filename: the filename for the hdf5 file.
        :param engines: the engines to be tracked
        """
        OutputMethod.__init__(self, *engines)
        self.file = h5py.File(filename,'a')
        self.prefix = prefix

    def _update(self, engine, results):

        try:
            dset_name = "%s%s/%d" % (
                self.prefix,
                engine.name,
                engine._number_of_processed_traces,
            )
            if dset_name in self.file:
                del self.file[dset_name]

            self.file[dset_name] = results

        except Exception as e:
            self.logger.warning(
                "Engine %s with %d traces: cannot be used with Hdf5OutputMethod. %s"
                % (engine.name, engine._number_of_processed_traces, e)
            )

    def _finalize(self):
        return self.file

    @staticmethod
    def load(filename):
        return Hdf5OutputMethod(filename)

    def __getitem__(self, item):
        return self.file[item]

    def __getitem__(self, item):
        if len(self.file[item]) > 1:
            return self.file[item]
        elif len(self.file[item]) == 1:
            return self.file[item][list(self.file[item])[0]]
        else:
            raise ValueError("%s not set for this output method." % (item))
