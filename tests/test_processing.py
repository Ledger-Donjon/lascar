import pytest
import itertools
from lascar.container import TraceBatchContainer
from lascar.tools.processing import *
from sklearn.decomposition import PCA, FastICA
import tempfile

leakages = np.random.rand(500, 100)
values = np.random.randint(0, 256, (500, 16)).astype(np.uint8)
container = TraceBatchContainer(leakages, values, copy=True)

functions = [
    lambda x: -x,
    lambda x: x[::2],
    lambda x: -x[0],
]



@pytest.mark.parametrize('container, function', [(container, f) for f in functions])
def test_function(container, function):
    container.leakage_processing = function
    for i, trace in enumerate(container):
        assert np.all(trace.leakage == function(leakages[i]))

rois = [
    [[2], [3]],
    [[0, 1], [2, 3] ],
    [[0, 1], [2, 3], [4, 5] ],
]

@pytest.mark.parametrize('container, roi', [(container, roi) for roi in rois])
def test_centered_product(container, roi):

    container.leakage_processing = lambda x:x
    centered_product = CenteredProductProcessing(container,roi)

    filename = tempfile.mkdtemp() + "/tmp.pickle"
    centered_product.save(filename)
    centered_product_bis = Processing.load(filename)

    combinations = [list(i) for i in itertools.product(*roi)]
    m = leakages.mean(0)

    for i, trace in enumerate(container):

        x=np.array(  [ np.prod((leakages[i]-m)[u]) for u in combinations])
        assert np.all(np.isclose(centered_product_bis(trace.leakage), x))


numbers_of_components = range(1,20,5)

@pytest.mark.parametrize('container, n', [(container, n) for n in numbers_of_components])
def test_pca(container, n):

    container.leakage_processing = lambda x:x
    pca_processing = PcaProcessing(container, n)

    filename = tempfile.mkdtemp() + "/tmp.pickle"

    pca_processing.save(filename)
    pca_processing_bis = Processing.load(filename)

    pca = PCA(n).fit_transform(leakages)
    for i, trace in enumerate(container):
        x = pca[i]
        assert np.all(np.isclose(pca_processing_bis(trace.leakage), x))

numbers_of_components = range(1,20,5)

@pytest.mark.parametrize('container, n', [(container, n) for n in numbers_of_components])
def test_ica(container, n):

    container.leakage_processing = lambda x:x
    ica_processing = IcaProcessing(container, n)

    filename = tempfile.mkdtemp() + "/tmp.pickle"

    ica_processing.save(filename)
    ica_processing_bis = Processing.load(filename)

    ica = FastICA(n, random_state=0).fit_transform(leakages)
    for i, trace in enumerate(container):
        x=ica[i]
        assert np.all(np.isclose(ica_processing_bis(trace.leakage), x))



@pytest.mark.parametrize('container', [container])
def test_standard_scaler(container):

    container.leakage_processing = lambda x:x
    standard_scaler = StandardScalerProcessing(container)

    filename = tempfile.mkdtemp() + "/tmp.pickle"
    standard_scaler.save(filename)
    standard_scaler_bis = Processing.load(filename)


    m = leakages.mean(0)
    for i, trace in enumerate(container):

        x= (leakages[i]-leakages.mean(0))/leakages.std(0)
        assert np.all(np.isclose(standard_scaler_bis(trace.leakage), x))



# processings = []
# processings += [CenteredProductProcessing(container, roi) for roi in rois]
#
#
#
#
# @pytest.mark.parametrize('container,processing', [(container,p) for p in processings])
# def test_load_save(container,processing):
#
#     container.leakage_processing = lambda x:x
#     filename = tempfile.mkdtemp() + "/tmp.pickle"
#     processing.save(filename)
#
#     processing_bis = Processing.load(filename)
#
#     for i, trace in enumerate(container):
#         assert np.all(np.isclose(processing(trace.leakage), processing_bis(trace.leakage)))
#
#
