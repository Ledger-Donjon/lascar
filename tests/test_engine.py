import pytest

from lascar import *
from lascar.tools.aes import sbox
import tempfile

leakages = np.random.rand(100, 20)
values = np.random.randint(0, 256, (100, 2)).astype(np.uint8)

trace_batch_container = TraceBatchContainer(leakages, values)
hdf5_container = Hdf5Container.export(
    trace_batch_container, tempfile.mkdtemp() + "/tmp.h5"
)
multiple_container = MultipleContainer(
    TraceBatchContainer(leakages[:10], values[:10]),
    TraceBatchContainer(leakages[10:50], values[10:50]),
    TraceBatchContainer(leakages[50:], values[50:]),
)

randomized_container = RandomizedContainer(trace_batch_container)
simulator_container = BasicAesSimulationContainer(
    100, 2, value_section="plaintext", additional_time_samples=4, seed=2
)
npy_container = NpyContainer.export(
    trace_batch_container,
    tempfile.mkdtemp() + "_leakages.npy",
    tempfile.mkdtemp() + "_values.npy",
)

containers = [
    trace_batch_container,
    hdf5_container,
    multiple_container,
    randomized_container,
    simulator_container,
    npy_container,
]


@pytest.mark.parametrize("container", containers)
class TestNonRegressionBasic:
    def test_mean_engine(self, container):
        session = Session(container)
        engine = session["mean"]

        container_bis = container[:]

        session.run()
        assert np.all(np.isclose(engine.finalize(), container_bis.leakages.mean(0)))

    def test_var_engine(self, container):
        session = Session(container)
        engine = session["var"]
        container_bis = container[:]
        session.run()
        assert np.all(np.isclose(engine.finalize(), container_bis.leakages.var(0)))


functions = [
    (lambda value: value[0] % 4, range(4)),
    (lambda value: 3 + (value[-1] % 10), range(3, 13)),
]

functions_ttest = [
    (lambda value: value[0] % 2, 2),
    (lambda value: value[-1] % 2, 2),
]


class TestNonRegressionPartitionerEngine:
    @pytest.mark.parametrize(
        "container,partition,partition_range",
        [(c, f[0], f[1]) for c in containers for f in functions],
    )
    def test_snr_engine(self, container, partition, partition_range):

        session = Session(container)
        engine = SnrEngine("snr", partition, partition_range)
        session.add_engine(engine)
        session.run()

        container_bis = container[:]

        means = np.zeros(
            (len(partition_range),) + container_bis.leakages.shape[1:], dtype=np.double
        )
        vars = np.zeros(
            (len(partition_range),) + container_bis.leakages.shape[1:], dtype=np.double
        )
        nums =[]
        denom =[]
        for i, val in enumerate(partition_range):
            idx = np.where(
                np.apply_along_axis(partition, 1, container_bis.values) == val
            )[0]
            means[i] = container_bis.leakages[idx].mean(0)
            vars[i] = container_bis.leakages[idx].var(0)
            nums += [means[i]]*len(idx)
            denom += [vars[i]]*len(idx)
        snr_numpy = np.array(nums).var(0) / np.array(denom).mean(0)

        assert np.all(np.isclose(snr_numpy, engine.finalize()))

    @pytest.mark.parametrize(
        "container,partition,partition_range",
        [(c, f[0], f[1]) for c in containers for f in functions],
    )
    def test_nicv_engine(self, container, partition, partition_range):
        session = Session(container)
        engine = NicvEngine("nicv", partition, partition_range)
        session.add_engine(engine)
        session.run()

        container_bis = container[:]
        means = np.zeros(
            (len(partition_range),) + container_bis.leakages.shape[1:], dtype=np.double
        )

        nums =[]
        for i, val in enumerate(partition_range):
            idx = np.where(
                np.apply_along_axis(partition, 1, container_bis.values) == val
            )[0]
            means[i] = container_bis.leakages[idx].mean(0)
            
            nums += [means[i]]*len(idx)
        nicv_numpy = np.array(nums).var(0)/ container_bis.leakages.var(0)

        assert np.all(np.isclose(nicv_numpy, engine.finalize()))

    @pytest.mark.parametrize(
        "container,partition", [(c, f[0]) for c in containers for f in functions_ttest]
    )
    def test_ttest_engine(self, container, partition):
        session = Session(container)
        engine = TTestEngine("ttest", partition)
        session.add_engine(engine)
        session.run()

        container_bis = container[:]
        indexes = [
            np.where(np.apply_along_axis(partition, 1, container_bis.values) == val)[0]
            for val in range(2)
        ]

        m0 = container_bis.leakages[indexes[0]].mean(0)
        m1 = container_bis.leakages[indexes[1]].mean(0)
        v0 = container_bis.leakages[indexes[0]].var(0)
        v1 = container_bis.leakages[indexes[1]].var(0)

        ttest_numpy = (m0 - m1) / np.sqrt(
            (v0 / len(indexes[0])) + (v1 / len(indexes[1]))
        )

        assert np.all(np.isclose(ttest_numpy, engine.finalize()))

    @pytest.mark.parametrize(
        "container,partition", [(c, f[0]) for c in containers for f in functions_ttest]
    )
    def test_ttest_higher_order_engine(self, container, partition):
        for d in range(1, 6):
            print(f"{d = }")
            if d == 1:
                self.test_ttest_engine(container, partition)
                continue

            session = Session(container)
            engine = TTestEngine("ttest_higher_order", partition, analysis_order=d)
            session.add_engine(engine)
            session.run()

            container_bis = container[:]
            indexes = [
                np.where(np.apply_along_axis(partition, 1, container_bis.values) == val)[0]
                for val in range(2)
            ]

            l0 = container_bis.leakages[indexes[0]]
            l1 = container_bis.leakages[indexes[1]]
            # Compute mean (used for preprocessing traces)
            m0 = l0.mean(0)
            m1 = l1.mean(0)

            if d == 2:
                # Preprocess traces at order 2: p = (X-m)**2 (almost the variance)
                p0 = np.power(l0 - m0, 2)
                p1 = np.power(l1 - m1, 2)
            else:
                # Variance of original traces (used to preprocess traces for d > 2)
                v0 = l0.var(0)
                v1 = l1.var(0)

                # Preprocess traces at order d > 2: p = ((X - m)/s)**d
                # with s the standard deviation
                p0 = np.power((l0 - m0) / np.sqrt(v0), d)
                p1 = np.power((l1 - m1) / np.sqrt(v1), d)

            # Compute ttest using preprocessed traces
            true_m0 = p0.mean(0)
            true_m1 = p1.mean(0)

            true_v0 = p0.var(0)
            true_v1 = p1.var(0)

            ttest_numpy = (true_m0 - true_m1) / np.sqrt(
                    (true_v0 / len(indexes[0])) + (true_v1 / len(indexes[1]))
                    )

            assert np.all(np.isclose(ttest_numpy, engine.finalize()))

functions = [
    lambda value: hamming(value[0]),
    lambda value: hamming_weight(value[-1]),
]


guess_functions = [
    (lambda value, guess: hamming(value[0] ^ guess), range(4)),
    (lambda value, guess: hamming(sbox[value[-1] ^ guess]), range(4, 14)),
]

leakage_models = [HammingPrecomputedModel()] + [BitLeakageModel(i) for i in range(2)]


guess_functions_for_partition = [
    ((lambda sensitive_value, guess: sensitive_value ^ guess), range(4)),
    ((lambda sensitive_value, guess: sbox[sensitive_value ^ guess]), range(4)),
]


class TestNonRegressionCpa:
    @pytest.mark.parametrize(
        "container,guess_function, guess_range, jitv",
        [
            (c, f[0], f[1], j)
            for c in containers
            for f in guess_functions
            for j in [True, False]
        ],
    )
    def test_cpa_engine(self, container, guess_function, guess_range, jitv):

        session = Session(container)
        engine = CpaEngine("cpa", guess_function, guess_range, jit=jitv)
        session.add_engine(engine)
        session.run()

        container_bis = container[:]
        cpa_np = np.zeros((len(guess_range), container_bis.leakages.shape[1]))

        for i, guess in enumerate(guess_range):
            model = np.array([guess_function(d, guess) for d in container_bis.values])
            cpa_np[i] = np.array(
                [
                    np.corrcoef(model, container_bis.leakages[:, j])[0, 1]
                    for j in range(cpa_np.shape[1])
                ]
            )

        assert np.all(
            np.isclose(engine.finalize(), cpa_np)
        ), "cpa non_regression test not passed."

    @pytest.mark.parametrize(
        "container, partition, partition_size, guess_function, guess_range, leakage_model",
        [
            (c, p, range(256), f[0], f[1], l)
            for c in containers
            for p in functions
            for f in guess_functions_for_partition
            for l in leakage_models
        ],
    )
    def test_cpa_partitioned_engine(
        self,
        container,
        partition,
        partition_size,
        guess_function,
        guess_range,
        leakage_model,
    ):

        f = lambda v, s: leakage_model(guess_function(v, s))
        session = Session(container)
        engine = CpaPartitionedEngine("cpa", partition, partition_size, f, guess_range,)
        session.add_engine(engine)
        session.run()

        container_bis = container[:]

        cpa_np = np.zeros((len(guess_range), container_bis.leakages.shape[1]))

        for i, guess in enumerate(guess_range):
            model = np.array(
                [
                    leakage_model(guess_function(partition(d), guess))
                    for d in container_bis.values
                ]
            )
            cpa_np[i] = np.array(
                [
                    np.corrcoef(model, container_bis.leakages[:, j])[0, 1]
                    for j in range(cpa_np.shape[1])
                ]
            )

        assert np.all(
            np.isclose(engine.finalize(), cpa_np)
        ), "cpa non_regression test not passed."
