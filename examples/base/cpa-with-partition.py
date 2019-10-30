"""
In this script, we demonstrate how to use CpaPartitionedEngine. For more detail, please consult the class documentation.

Here, since we focus only on 8bits of 'value', there is only 256 possible inputs.
The CpaPartitionedEngine takes profits of this property, and computes a Cpa more quickly than a CpaEngine would have done.

During the workflow, a partitioning has to be done, and the leakage model is applied in the end, during the finalize() method.

"""

from lascar import *
from lascar.tools.aes import sbox

byte = 3


def partition(value):  # the partition is made on the 3rd byte of plaintext
    return value["plaintext"][byte]


def guess_function(
    sensitive_value, guess
):  # the guess function is applied on the partitioned values
    return hamming(sbox[sensitive_value ^ guess])


partition_size = 256
guess_range = range(256)

leakage_model = HammingPrecomputedModel()

container = BasicAesSimulationContainer(
    1000, 3
)  # We use the BasicAesSimulationContainer with 2000 traces

attack = CpaPartitionedEngine(
    "cpa_partitioned", partition, partition_size, guess_function, guess_range
)

session = Session(container)
session.add_engine(attack)
session.output_method = MatPlotLibOutputMethod(attack)
session.run(1000)
