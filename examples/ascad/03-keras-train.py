"""
lascar on ASCAD Database

(https://github.com/ANSSI-FR/ASCAD)

Objective in this script:

 - Perform neural network training using ASCAD.h5 with keras through lascar
 - Save the model for future usage

"""
import sys
from lascar import *
from lascar.tools.aes import sbox


if not len(sys.argv) == 3:
    print(
        "Need to specify the location of ASCAD_DIR and the type of Neural Network to test: mlp or cnn."
    )
    print("USAGE: python3 %s ASCAD_DIR [mlp,cnn]" % sys.argv[0])
    exit()

ASCAD_DIR = sys.argv[1]
filename = ASCAD_DIR + "/ASCAD_data/ASCAD_databases/ASCAD.h5"


# The following functions are extracted https://github.com/ANSSI-FR/ASCAD/blob/master/ASCAD_train_models.py
from ASCAD_train_models import mlp_best, cnn_best

if sys.argv[2] == "mlp":
    nn = mlp_best()
elif sys.argv[2] == "cnn":
    nn = cnn_best()
else:
    "mlp or cnn only."
    exit()


targeted_byte = 2

"""
When building the profiling_container, take special care of the kind of neural network used.

If using the mlp network, you don't need to process your leakages.
However if using cnn network, you need to process the leakages: they need to be reshaped

Hence the use of leakage_processing=ReshapeProcessing(nn.input_shape[1:])
"""

profiling_container = Hdf5Container(
    filename,
    "/Profiling_traces/traces",
    "/Profiling_traces/metadata",
    leakage_processing=ReshapeProcessing(nn.input_shape[1:]),
)

# Profile:
def partition_function(value):
    """
    This function recreates the label computed in https://github.com/ANSSI-FR/ASCAD/blob/master/ASCAD_generate.py#L37
    :param value: a value isued from a trace (ie a single item from /Profiling_traces/metadata
    :return: the label under study for the trace.
    """
    return sbox[value["plaintext"][targeted_byte] ^ value["key"][targeted_byte]]


partition_values = range(256)  # The range for the labels.


# An engine has to be created, dedicated to the profiling of a classifier (here a keras neural network) with leakages/labels.
nn_profile_engine = ProfileEngine(
    nn,
    partition_function,
    partition_values,
    epochs=5,
    batch_size=200,
    test_size=0.1
)

Session(profiling_container, engine=nn_profile_engine).run()

nn.save("model.h5")
