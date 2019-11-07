"""
lascar on ASCAD Database

(https://github.com/ANSSI-FR/ASCAD)

Objective in this script:

 - load a neural network (nn) model already precomputed (mlp or cnn)
 - Use it on ASCAD attack traces to recover a key byte
 - Plot the mean rank for the solution.

"""
import sys
from lascar import *
from lascar.tools.aes import sbox
from keras.models import load_model


if not len(sys.argv) == 3:
    print(
        "Need to specify the location of ASCAD_DIR and the type of Neural Network to test: mlp or cnn."
    )
    print("USAGE: python3 %s ASCAD_DIR [mlp,cnn]" % sys.argv[0])
    exit()

ASCAD_DIR = sys.argv[1]
filename = ASCAD_DIR + "/ASCAD_data/ASCAD_databases/ASCAD.h5"

if sys.argv[2] == "mlp":
    model_name = (
        ASCAD_DIR
        + "/ASCAD_data/ASCAD_trained_models/mlp_best_ascad_desync0_node200_layernb6_epochs200_classes256_batchsize100.h5"
    )
elif sys.argv[2] == "cnn":
    model_name = (
        ASCAD_DIR
        + "/ASCAD_data/ASCAD_trained_models/cnn_best_ascad_desync0_epochs75_classes256_batchsize200.h5"
    )


nn = load_model(model_name)

"""
When building the attack_container, take special care of the kind of neural network used.

If using the mlp network, you don't need to process your leakages.
However if using cnn network, you need to process the leakages: they need to be reshaped

Hence the use of leakage_processing=ReshapeProcessing(nn.input_shape[1:])
"""
attack_container = Hdf5Container(
    filename,
    "/Attack_traces/traces",
    "/Attack_traces/metadata",
    leakage_processing=ReshapeProcessing(nn.input_shape[1:]),
)

targeted_byte = 2
solution = attack_container[0].value["key"][
    targeted_byte
]  # The key byte we are looking for


def guess_function(value, guess):
    """
    This function will compute a label under a 'guess' (here the key_byte hypothesis)
    """
    return sbox[value["plaintext"][targeted_byte] ^ guess]


guess_range = range(256)  # The possbles value for the guess

# An engine has to be created, dedicated to use a classifier (here a keras neural network nn) with Side-Channel Traces.
nn_match_engine = MatchEngine(
    "nn_match", nn, guess_function, guess_range, solution=solution
)


# Now, 5 times in a row we randomly take 2000 traces from attack_container, and compute the mean rank of the correct key, every 10 traces.
ranks = []

for i,container in enumerate(split_container(attack_container, size_of_splits=2000)[:5]):

    session = Session(
        container,
        name="run %d" % i,
        engine=nn_match_engine,
        output_method=RankProgressionOutputMethod(nn_match_engine, display=False),
        output_steps=range(0, 2000, 10),
    )
    session.run()

    ranks.append(
        session.output_method.get_scores_solution()["nn_match"]
    )  # ranks is filled with the progression of the rank of the solution for the engine 'nn_match'

import matplotlib.pyplot as plt

_ = plt.plot(session.output_method.get_steps(), np.array(ranks).mean(0))
_ = plt.ylabel("Mean rank")
_ = plt.xlabel("Number of traces")
_ = plt.show()
