"""
In this script, we show how to perform second-order Correlation Power Analysis with lascar to retrieve an AES keybyte.

Second-order means that the sensitive value is masked.

We first create a ToyAesSecondOrderContainer designed to simulate the leakage of a masked sbox.
Behind that, we show how to use the CenteredProductProcessing to recombine time samples
Finaly, a classical CPA is used to retrieve the key.

"""
from lascar import *
from lascar.tools.aes import sbox


class ToyAesSecondOrderContainer(AbstractContainer):
    """

    For second order side-channel analysis:

    simulate the behavior of a masked sbox.

    Computes sbox[ y^key ] ^ mask
    where key is fixed, y is the "plaintext", and mask is random/unknown

    """

    def __init__(self, number_of_traces, noise=1, key=42, **kwargs):

        value_dtype = np.dtype(
            [("y", np.uint8), ("mask", np.uint8), ("key", np.uint8),]
        )

        self.value = np.zeros((), value_dtype)
        self.value["key"] = key
        self.noise = noise
        AbstractContainer.__init__(self, number_of_traces, **kwargs)

    def generate_trace(self, idx):

        np.random.seed(seed=idx)  # for reproducibility

        # for each trace, both y and mask values are random
        self.value["y"] = np.random.randint(0, 256)
        self.value["mask"] = np.random.randint(0, 256)

        # the leakage consists in 15 random value (with chosen noise),
        # on the sample with index [5], the hamming weight of the mask
        # on the sample with index [10], the hamming weight of the masked output of the sbox.
        leakage = np.random.normal(0, self.noise, (15,))
        leakage[5] += hamming_weight(np.uint8(self.value["mask"]))
        leakage[10] += hamming_weight(
            sbox[self.value["y"] ^ self.value["key"]] ^ self.value["mask"]
        )

        return Trace(leakage, self.value)


container = ToyAesSecondOrderContainer(1000)

"""
To mount a second-order cpa, leakage samples have to be recombinated, using a leakage processiNg: CenteredProductProcessing.
It takes as input the samples to be recombinated: the time sample where the mask is maniulated (5), and the time sample where the masked value is manipulates (10).
It results of a leakage processing which, when appliied to the container, produces leakages with a centered product of time sample 5 with time sample 10.

Instead of singletons, we could have rebombinated multiple points of interests.

For instance, applying CenteredProductProcessing(container, ([4,5], [10,11,12])) would have produced a container with 6 recombinated samples 
(4 with 10, 4 with 11, 4 with 12, 5 with 10, 5 with 11, 5 with 12)

But in this simple case, we know exactly when occurs the relevant events ([5] and [10])

"""
container.leakage_processing = CenteredProductProcessing(container, ([5], [10]))

cpa_engine = CpaEngine(
    "cpa-high-order",
    lambda value, guess: hamming(sbox[value["y"] ^ guess]),
    range(256),
    solution=42,
)


session = Session(
    container,
    engine=cpa_engine,
    output_method=ScoreProgressionOutputMethod(cpa_engine),
    output_steps=50,
)  # the steps at which the results will be computed

session.run(100)
