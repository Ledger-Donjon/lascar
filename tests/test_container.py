import numpy as np
import pytest

from lascar import *
import tempfile

leakages = np.random.rand(100, 200)
values = np.random.randint(0, 256, (100, 16)).astype(np.uint8)

trace_batch_container = TraceBatchContainer(leakages, values, copy=True)

hdf5_container = Hdf5Container.export(
    trace_batch_container, tempfile.mkdtemp() + "/tmp.h5"
)

multiple_container = MultipleContainer(
    TraceBatchContainer(leakages[:10], values[:10]),
    TraceBatchContainer(leakages[10:50], values[10:50]),
    TraceBatchContainer(leakages[50:], values[50:]),
)

# randomized_container = RandomizedContainer(trace_batch_container)
# filtered_container = FilteredContainer(trace_batch_container, lambda trace: trace.value[0]&1)

npy_container = NpyContainer.export(
    trace_batch_container,
    tempfile.mkdtemp() + "_leakages.npy",
    tempfile.mkdtemp() + "_values.npy",
)

containers = [trace_batch_container, hdf5_container, multiple_container, npy_container]

get_batch_offsets = [(i, i + 1) for i in range(0, 100, 5)]
get_batch_offsets += [(i, i + 5) for i in range(0, 100, 5)]
get_batch_offsets += [(i, i + 10) for i in range(0, 100, 10)]

leakage_sections = [slice(0), slice(100), range(0, 100, 10), slice(None, None)]

leakage_processings = [
    lambda leakage: leakage,
    lambda leakage: leakage ** 2,
    lambda leakage: leakage[0:2],
    lambda leakage: leakage[0],
    lambda x: x,
]


@pytest.mark.parametrize("container", containers)
class TestContainer:
    def test_container_getter(self, container):
        for i, trace in enumerate(container):
            assert np.all(trace.leakage == leakages[i])
            assert np.all(trace.value == values[i])

    def test_container_setter(self, container):
        pass

    def test_container_section(self, container):
        pass


alls = [(c, o) for c in containers for o in get_batch_offsets]


@pytest.mark.parametrize("container, offset", alls)
class TestContainerGetBatch:
    def test_get_batch(self, container, offset):
        batch = container[offset[0] : offset[1]]

        for i in range(len(batch)):
            assert np.all(batch.leakages[i] == leakages[i + offset[0]])
            assert np.all(batch.values[i] == values[i + offset[0]])


alls = [(c, l) for c in containers for l in leakage_sections]


class TestContainerLeakageSection:
    @pytest.mark.parametrize("container,leakage_section", alls)
    def test_leakage_section_get(self, container, leakage_section):

        container.leakage_section = leakage_section
        for i, trace in enumerate(container):
            assert np.all(trace.leakage == leakages[i, leakage_section])

    @pytest.mark.parametrize("container", containers)
    def test_leakage_section_set_none(self, container):

        container.leakage_section = slice(None, None)
        for i, trace in enumerate(container):
            assert np.all(trace.leakage == leakages[i])


alls = [(c, l) for c in containers for l in leakage_processings]
alls_pca = [(c, l) for c in containers for l in [1, 2, 5, 10]]
alls_centered_product = [(c, o) for c in containers for o in [1, 2, 3]]


class TestContainerLeakageProcessing:
    @pytest.mark.parametrize("container,leakage_processing", alls)
    def test_leakage_processing(self, container, leakage_processing):

        container.leakage_processing = leakage_processing
        for i, trace in enumerate(container):
            assert np.all(trace.leakage == leakage_processing(leakages[i]))

    @pytest.mark.parametrize("container", containers)
    def test_leakage_processing_standard_scaler(self, container):

        container.leakage_processing = lambda x: x

        leakage_processing = StandardScalerProcessing(container)
        container.leakage_processing = leakage_processing

        batch = container[: container.number_of_traces]
        leakages_centered_reduced = (leakages - leakages.mean(0)) / leakages.std(0)
        assert np.all(np.isclose(batch.leakages, leakages_centered_reduced))

    @pytest.mark.parametrize("container,number_of_components", alls_pca)
    def test_leakage_processing_principal_component_analysis(
        self, container, number_of_components
    ):

        container.leakage_processing = lambda x: x
        leakage_processing = PcaProcessing(container, number_of_components)
        container.leakage_processing = leakage_processing

        from sklearn.decomposition import PCA

        pca_offline = PCA(number_of_components)
        pca_offline.fit(leakages)
        leakages_processed = pca_offline.transform(leakages)
        for i, trace in enumerate(container):
            assert np.all(np.isclose(trace.leakage, leakages_processed[i].squeeze()))

    @pytest.mark.parametrize("container, order", alls_centered_product)
    def test_leakage_processing_centered_product(self, container, order):

        container.leakage_section = range(3)
        container.leakage_processing = lambda x: x

        leakage_processing = CenteredProductProcessing(container, order=order)
        container.leakage_processing = leakage_processing
        leakages_centered = leakages - leakages.mean(0)

        batch = container[: container.number_of_traces]
        for i, combination in enumerate(leakage_processing.combinations):
            assert np.all(
                batch.leakages[:, i]
                == np.prod(leakages_centered[:, combination], axis=1)
            )

    # Todo: test_leakage_prodessing_reshape
    # Todo: test_leakage_prodessing_casacaed
