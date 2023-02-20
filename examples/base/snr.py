"""
In this script, we show how to perform side-channel characterisation with lascar to study the behaviour of an Aes Sbox

The characterisation is made with SnrEngine or NicvEngine, which role is the same.
Specifically, each of them need:
- a partition function, which will separate leakages into classs
- a "number_of_partitions" to indicate the number of possible classes for the partition_function


"""
import matplotlib.pyplot as plt

from lascar import *

container = BasicAesSimulationContainer(
    1000, noise=3
)  # We use the BasicAesSimulationContainer with 2000 traces


def partition_function(
    value,
):  # partition_function must take 1 argument: the value returned by the container at each trace
    return value["plaintext"][
        3
    ]  # here we partition on the value of the 3rd plaintext byte


number_of_partitions = 256  # number of possible classes (~output of the partiton_function) for the partition_function
snr_engine = SnrEngine(
     partition_function, range(number_of_partitions), name="snr_plaintext_3"
)

# We choose here to plot the resulting curve
session = Session(
    container, engine=snr_engine, output_method=MatPlotLibOutputMethod(snr_engine)
)

session.run(batch_size=500)


"""
Now let's compute the 16 snr of the 16 bytes in //
We choose here to display the 16 curves on the same plot
"""


def get_partition_function(byte):
    def partition_function(
        value,
    ):  # partition_function must take 1 argument: the value returned by the container at each trace
        return value["plaintext"][
            byte
        ]  # here we partition on the value of the 3rd plaintext byte

    return partition_function


number_of_partitions = 256  # number of possible classes (~output of the partiton_function) for the partition_function
snr_engines = [
    SnrEngine(
        get_partition_function(i), range(number_of_partitions), name="snr_plaintext_%d" % i
    )
    for i in range(16)
]

session = Session(
    container,
    engines=snr_engines,
    output_method=MatPlotLibOutputMethod(*snr_engines, single_plot=True, legend=True),
)

session.run(batch_size=500)
