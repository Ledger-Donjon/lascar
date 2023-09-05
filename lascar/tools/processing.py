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
processing.py
"""
import itertools
import pickle

import numpy as np
from sklearn.decomposition import FastICA
from sklearn.decomposition import PCA


class Processing:
    """
    Processing is the Base class for implementing processing.

    A Processing can be seen as an object whose role is to modify leakages (or values).
    It has to be callable, and offer some save/load mechanisms.
    """

    def __init__(self, filename=None):
        if filename is not None:
            self.save(filename)

    def __call__(self, leakage):
        return leakage

    def save(self, filename):
        pickle.dump(self, open(filename, "wb"))

    @staticmethod
    def load(filename):
        return pickle.load(open(filename, "rb"))


class CenteredProductProcessing(Processing):
    """
    CenteredProductProcessing is the processing used when performing High-Order Side-Channel Analysis.

    It computes the centered product of "order" leakage samples ("order" being the order chosen by the user).


    Let n be the order of the CenteredProductProcessing.
    n rois are used to indicate which leakage points will be recombinated together.
    If rois is not specified, all possible combinations for the container will be used.
    """

    def __init__(self, container, rois=None, order=2, batch_size=1000, filename=None):
        """

        :param container: targeted container
        :param rois: Regions Of Interest: to be recombined. Optional (if not set, all leakages are recombined to eachother)
        :param order:
        :param batch_size:
        """
        # compute mean:
        from lascar.session import Session

        session = Session(container, name="CenteredProduct:")
        session.run(batch_size)
        self.mean = session["mean"].finalize()
        number_of_leakage_samples = container[0][0].shape[0]

        if rois is None:
            self.order = order
            self.combinations = [
                list(i)
                for i in itertools.combinations(range(number_of_leakage_samples), order)
            ]

        else:

            self.combinations = [list(i) for i in itertools.product(*rois)]
        Processing.__init__(self, filename)

    def __call__(self, leakage):

        leakage = leakage - self.mean
        return np.array([np.prod(leakage[i]) for i in self.combinations])


class PcaProcessing(Processing):
    """
    PcaProcessing is the procesisng used when performing Principal Component Analysis on Side-Channel Traces.
    (based on sklearn.decomposition.PCA)
    """

    def __init__(
        self,
        container,
        number_of_components,
        random_state=0,
        post_section=None,
        filename=None,
    ):
        """
        :param container: the container on which to perform PCA
        :param number_of_components: number of component used for the dimensionality reduction
        :param random_state: optional, for the sklearn object
        :param post_section: optional, when want to oupput only some of the 'number_of_components' components
        """
        self._pca = PCA(n_components=number_of_components, random_state=random_state)

        # compute pca:
        batch = container[: len(container)]
        self._pca.fit(batch.leakages)

        self.post_section = post_section
        Processing.__init__(self, filename)

    def __call__(self, leakage):
        if self.post_section is None:
            return self._pca.transform([leakage])[0]
        else:
            return self._pca.transform([leakage])[0, self.post_section]


class IcaProcessing(Processing):
    """
    IcaProcessing is the procesisng used when performing Independant Component Analysis on Side-Channel traces.
    (based on sklearn.decomposition.ICA)
    """

    def __init__(
        self,
        container,
        number_of_components,
        random_state=0,
        post_section=None,
        filename=None,
    ):
        """
        :param container: the container on which to perform ICA
        :param number_of_components: number of component used for the dimensionality reduction
        :param random_state: optional, for the sklearn object
        """
        self._ica = FastICA(
            n_components=number_of_components, random_state=random_state
        )

        # compute ica:
        batch = container[: len(container)]
        self._ica.fit(batch.leakages)

        self.post_section = post_section
        Processing.__init__(self, filename)

    def __call__(self, leakage):
        if self.post_section is None:
            return self._ica.transform([leakage])[0]
        else:
            return self._ica.transform([leakage])[0, self.post_section]


class StandardScalerProcessing(Processing):
    """
    StandardScalerProcessing is a processing that will Standardize leakages by removing the mean and scaling to unit variance
    """

    def __init__(self, container, filename=None):
        # compute mean/var:
        self.mean, self.std_inv = container.get_leakage_mean_var()

        self.std_inv = 1 / np.sqrt(self.std_inv)
        Processing.__init__(self, filename)

    def __call__(self, leakage):
        return (leakage - self.mean) * self.std_inv


class ReshapeProcessing(Processing):
    """
    ReshapeProcessing is a processing that will reshape leakages with given shape.
    """

    def __init__(self, shape, filename=None):
        self.shape = shape
        Processing.__init__(self, filename)

    def __call__(self, leakage):
        return leakage.reshape(self.shape)


class CascadedProcessing(Processing):
    def __init__(self, *processings, filename=None):
        self.processings = processings
        Processing.__init__(self, filename)

    def __call__(self, leakage):
        res = leakage
        for processing in self.processings:
            res = processing(res)
        return res

    def add_processing(self, processing):
        self.processings.append(processing)
