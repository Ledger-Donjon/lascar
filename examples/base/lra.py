from lascar import *
from lascar.tools.aes import sbox

byte = 3


def partition(value):  # the partition is made on the 3rd byte of plaintext
    return value["plaintext"][byte]


def guess_function(
    sensitive_value, guess
):  # the guess function is applied on the partitioned values
    return sbox[sensitive_value ^ guess]


partition_size = 256
guess_range = range(256)

leakage_model = HammingPrecomputedModel()
container = BasicAesSimulationContainer(5000, 0)
attack = LraEngine("lra", partition, partition_size, guess_function, guess_range)

session = Session(container)
session.add_engine(attack)
session.output_method = MatPlotLibOutputMethod(attack)
session.run(1000)
