import numpy as np
import pytest
import h5py
from lascar.container import TraceBatchContainer

import tempfile

leakages = np.random.rand(100, 200)
values = np.random.randint(0, 256, (100, 16)).astype(np.uint8)

@pytest.mark.parametrize('leakages, values', [(leakages,values)])
class TraceBatchContainer:

    def test_constructor(self, leakages, values):


        container = TraceBatchContainer(leakages, values, copy=True)

        for i, trace in enumerate(container):
            assert np.all(trace.leakage == leakages[i])
            assert np.all(trace.value == values[i])


    def test_save_load(self, leakages, values):

        filename = tempfile.mkdtemp() + "/tmp.npy"

        container = TraceBatchContainer(leakages, values, copy=True)
        container.save(filename)

        container_bis = TraceBatchContainer.load(filename)

        for i, trace in enumerate(container_bis):
            assert np.all(trace.leakage == leakages[i])
            assert np.all(trace.value == values[i])
