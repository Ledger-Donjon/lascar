"""
In this script, we show how to perform side-channel characterisation using Welch's T-test to study the behaviour of an Aes Sbox

The characterisation is made with the TTestEngine
Its constructor needs a partition function, which will separate leakages into two classes.

"""
from lascar import *

container = BasicAesSimulationContainer(
    10000, 1
)  # We use the BasicAesSimulationContainer with 10000 traces


def partition_function(
    value,
):  # partition_function must take 1 argument: the value returned by the container at each trace
    return int(value["plaintext"][3] == 0)  # "plaintext[3] == 0" versus "all other values"


ttest_engine = TTestEngine(partition_function)

# We choose here to plot the resulting curve
plot_output = MatPlotLibOutputMethod(ttest_engine)
session = Session(container, output_method=plot_output)
session.add_engine(ttest_engine)

session.run(batch_size=2500)


"""
Now let's compute the 16 ttest of the 16 bytes in //
We choose here to display the 16 curves on the same plot
"""


def get_partition_function(byte):
    def partition_function(value):
        return int(value["plaintext"][byte] == 0)

    return partition_function


ttest_engines = [
    TTestEngine(get_partition_function(i)) for i in range(16)
]

session = Session(
    container,
    engines=ttest_engines,
    output_method=MatPlotLibOutputMethod(*ttest_engines, single_plot=True, legend=True),
)

session.run(batch_size=2500)
