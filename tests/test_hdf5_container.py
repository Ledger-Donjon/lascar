import numpy as np
import pytest
import h5py
from lascar.container import Hdf5Container, TraceBatchContainer

import tempfile

leakages = np.random.rand(100, 200)
values = np.random.randint(0, 256, (100, 16)).astype(np.uint8)


@pytest.mark.parametrize("leakages, values", [(leakages, values)])
class TestHdf5Container:
    def test_constructor(self, leakages, values):

        filename = tempfile.mkdtemp() + "/tmp.h5"
        with h5py.File(filename, "w") as f:
            f["leakages"] = leakages
            f["values"] = values

        container = Hdf5Container(filename)

        for i, trace in enumerate(container):
            assert np.all(trace.leakage == leakages[i])
            assert np.all(trace.value == values[i])

    def test_from_arrays(self, leakages, values):
        filename = tempfile.mkdtemp() + "/tmp.h5"
        container = Hdf5Container.export(
            TraceBatchContainer(leakages, values), filename
        )

        for i, trace in enumerate(container):
            assert np.all(trace.leakage == leakages[i])
            assert np.all(trace.value == values[i])

    def test_export(self, leakages, values):
        filename = tempfile.mkdtemp() + "/tmp.h5"
        with h5py.File(filename, "w") as f:
            f["leakages"] = leakages
            f["values"] = values

        container = Hdf5Container(filename)
        container_bis = Hdf5Container.export(container, tempfile.mkdtemp() + "/tmp.h5")

        for i, trace in enumerate(container_bis):
            assert np.all(trace.leakage == leakages[i])
            assert np.all(trace.value == values[i])
