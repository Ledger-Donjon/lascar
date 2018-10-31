"""
This script demonstrates how to use sklearn classifiers and keras model within lascar to perform profiled SCA.

Profiled SCA means that the attacker has access to an sample of the Device Under Test with known guess.
He can hence learn how the DUT behave, and build a classifier which will after be applied on a device with unknown guess

In this example, QuadraticDiscriminantAnalysis is performed on simulated AES traces.
Two steps:

1 - Use ProfileEngine to learn on traces with known guess
2 - Use of MatchEngine to apply the classifier on traces with unknown guess.

This can be used with all classifier provided by sklearn
(see http://scikit-learn.org/stable/auto_examples/classification/plot_classifier_comparison.html for a list of classifiers)

And with all keras Neural Network inherating from keras.Model

The ProfileEngine is actually a PartitionerEngine (such as SnrEngine, NicvEngine, TTestEngine...)
Specifically it needs:
- a sklearn Classifier instantiated (such as QuadraticDiscriminantAnalysis) or a keras neural network compiled
- a partition function, which will separate leakages into classes
- a "number_of_partitions" to indicate the number of possible classes for the partition_function


The ProfileEngine is actually a GuessEngine (such as CpaHypothesisEngine)
Specifically it needs:
- a classifier which has been already trained (with ProfileEngine)
- a selection function (under guess hypothesis) on the sensitive value (here the output of the sbox at first round)
- a "guess_range" which will define what are the guess possible values

"""

import matplotlib.pyplot as plt
import numpy as np

from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis


from lascar import *
from lascar.tools.aes import *

byte = 3  # key byte to be attacked. In BasicAesSimulationContainer, k_3 = 3

"""
# Part 1: Profiling Phase: Building the classifier from simulated traces with kown keys inside partition function
"""
container_profile = BasicAesSimulationContainer(5000, 0.5)  # 5000 traces for profiling
container_profile.leakage_section = [
    byte]  # POI selection: trivial here since on BasicAesSimulationContainer, the 3rd byte leaks on the third sample

solution = container_profile[0].value['key'][byte]

# partition_function must take 1 argument: the value returned by the container at each trace
def partition_function(value):
    return sbox[value['plaintext'][3] ^ value['key'][3]]  # here we partition on the output of the 3rd sbox


number_of_partitions = 256  # number of possible classes (~values) for the partition_function

classifier_qda = QuadraticDiscriminantAnalysis()

from lascar.tools.keras_neural_networks import mlp_best
classifier_keras = mlp_best(container_profile._leakage_abstract.shape, number_of_classes=number_of_partitions, nodes=[100,50], dropout=0.2)


classifier_profile_engine_qda =   ProfileEngine("profile qda", classifier_qda, partition_function, number_of_partitions)
classifier_profile_engine_keras = ProfileEngine("profile keras", classifier_keras, partition_function, number_of_partitions, epochs=20)

session = Session(container_profile, engines=[classifier_profile_engine_qda, classifier_profile_engine_keras]).run()

save_classifier(classifier_qda, "classifier_qda.save")  # The classifier can be saved for further usage
save_classifier(classifier_keras, "classifier_keras.save")


"""
# Part 2: Attack Phase: Apply the prebuilt-classifier on traces with unknown key
"""


# The sensitive value with guess hypothesis
def sensitive_value_with_guess(data, guess):
    return sbox[data['plaintext'][byte] ^ guess]


guess_range = range(256)  # what are the hypothesis for the guess

container_attack = BasicAesSimulationContainer(50, 1, seed=12)  # 200 traces for attack (different seed used for having different traces)
container_attack.leakage_section = [byte]  # Same POI-selection than for profiling phase

classifier_qda = load_classifier("classifier_qda.save")  # the classifier is imported from a file
classifier_keras = load_classifier("classifier_keras.save")

classifier_match_engine_qda = MatchEngine("match qda", classifier_qda, sensitive_value_with_guess, guess_range, solution=container_attack.key[byte])
classifier_match_engine_keras = MatchEngine("match keras", classifier_keras, sensitive_value_with_guess, guess_range, solution=container_attack.key[byte])

engines = [classifier_match_engine_qda,classifier_match_engine_keras]

session = Session(container_attack, engines=engines, output_method=ScoreProgressionOutputMethod(*engines), output_steps=range(0, 50, 5))

session.run()
