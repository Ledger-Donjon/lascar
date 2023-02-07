# This tutorial introduces the `Session` class and covers some of its basic
# functionalities. In lascar, when all traces of a `Container` need to be walked
# in order to make à statistical analysis, a `Session` must be used.
#
# `Session` is the class that will orchestrate:
# - the reading of the container traces by batch (to avoid loading all in RAM as much as possible),
# - all the statistical computations that are being requested,
# - the output of the your analysis (log file, a binary file, a plot, etc.)

# In this example, a `BasicAesSimulationContainer` is set up, with 10000 traces,
# and noise set to 1. A session is then instanciated, and the container is
# given as the argument to indicate to the session that all processing will be
# done on the traces of this container. Other optional arguments can be given to
# the `Session.__init__()` method; they will be presented later.

from lascar import BasicAesSimulationContainer
from lascar import Session

container = BasicAesSimulationContainer(10000, noise=1)
session = Session(container)

# The `Session` class implements a logger (such as `Container`), whose level can
# be set by the user:
session.logger.setLevel("WARN")

# The main method for `Session` class is the `run()` method. It will read all
# the traces from the container by batches, and run the required processing
# defined by the list of registered engines.
#
# The size of batches can be specified as an argument in order to chose the
# right balance between speed and RAM consumption.
#
# Engines are classes dedicated to compute stuffs from side-channel traces. The
# `Session` distributes trace batches to all its engines, for them to process
# the leakage and data.
#
# Here a list of engines already implemented in lascar:
# - `MeanEngine`: computes the mean of all the traces leakages,
# - `VarEngine`: computes the variance of all the traces leakages,
# - `SnrEngine`: computes Signal-to-Noise-Ratio from the traces leakages and a
#   partitioning function applied to the values.
# - `CpaEngine`: computes Correlation Power Analysis from the traces leakages
#   and a guess function applied to the values.
# - `TTestEngine`: computes Welch's T-Test from the traces leakages and a
#   partitioning function applied to the value
#
# By default, a `Session` only registers `MeanEngine` and `VarEngine`.
# The man/variance of the leakage is the only thing computed in that very case:

print(session.engines)
session.run()

# Now that the engines has been fed with all the traces, we can access their
# results through their finalize() method.

mean = session.engines["mean"].finalize()
variance = session["var"].finalize()

print("mean:", mean)
print("variance:", variance)
