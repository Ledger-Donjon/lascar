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

import pickle

import numpy as np

from . import OutputMethod


class DictOutputMethod(OutputMethod):
    """
    DictOutputMethod is an OutputMethod that will store inside a dict the results from its tracked engines (for each output_step).

    For each engine tracked, a key is added to the PickleOuputMethod, containing a sub-dict.
    For each output_step, a key is added inside the sub-dict corresponding to each engine.

    in the end:

    pickle_output_method[engine_name][output_step] contains engine.results after output_step traces processed.

    If a filename is specified, the finalize() method will store the dict inside a file using pickle.
    """

    def __init__(self, *engines, filename=None):
        """

        :param engines: the engines to be tracked
        :param filename: optional, if specified, the dict will be stored inside a pickle file.
        """
        OutputMethod.__init__(self, *engines)

        self.results = {}
        self.filename = filename

    def _update(self, engine, results):

        try:
            if not engine.name in self.results:
                self.results[engine.name] = {}
            self.results[engine.name][engine._number_of_processed_traces] = np.copy(results)
        except Exception as e:
            print(e)
            self.logger.warning("Engine %s with %d traces: cannot be used with DictOutputMethod" % (
                engine.name, engine._number_of_processed_traces))

    def _finalize(self):
        if self.filename is not None:
            with open(self.filename, "wb") as file:
                pickle.dump(self.results, file)

    @staticmethod
    def load(filename):
        out = DictOutputMethod()
        with open(filename, "rb") as file:
            out.results = pickle.load(file)
        return out

    def __getitem__(self, item):
        if len(self.results[item]) > 1:
            return self.results[item]
        elif len(self.results[item]) == 1:
            return self.results[item][ list(self.results[item])[0] ]
        else:
            raise ValueError('%s not set for this output method.'%(item))

