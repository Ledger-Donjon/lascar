# In this script we will demonstrate how to use lascar to perform leakage
# synchronisation.
#
# In side-channel, leakages need to be slightly "stackable". It is very common
# that, from a trace to another, physical behaviors induce temporal shifting in
# the leakage.
#
# Leakage Synchronisation is the name given to the post-processing method you
# apply on it to make all leakages "stackable", or aligned.
#
# In the following example we will design an `AbstractContainer` that will
# generate fake "desynchronized" traces. We will then design a synchronisation
# method, which will consist in a `leakage_processing` applied to the
# `AbstractContainer`, so that it will deliver synchronized traces.

from lascar import AbstractContainer, Trace
import numpy as np

# First the SimulatedContainer, on which we will set up the synchronisation:
class SimulatedContainer(AbstractContainer):
    def generate_trace(self, idx: int):
        # Our leakage will consist in 100 time samples, with a peak randomly
        # inserted. Imagine this peak contains the side-channel information.
        leakage = np.random.rand(100)
        # The offset where the peak will be inserted
        offset = np.random.randint(20, 80)
        leakage[offset : offset + 11] += np.hanning(11) * 4
        value = np.zeros(())  # the value wont be used in here...
        return Trace(leakage, value)

# Lets create a container with 100 generated traces.
container = SimulatedContainer(100)

# We can use the `plot_leakage()` method to display the first traces, and note
# that the leakages are not stackable, as expected.
container.plot_leakage(range(3))

# Now the synchronisation process. `leakage_procesing` will be used, so we need
# to design a function, that takes a leakage as input and returns a transformed
# leakage.
#
# Actually, we won't use a function, but a callable class (see.
# https://docs.python.org/3/glossary.html#term-callable). The reason why we do
# that, is that our synchronisation process will attempt to overlay leakages
# based on a reference trace leakage.
#
# The synchronisation strategy will find the peak in each trace (`argmax` in
# this case) and roll the leakages to match the first peak.
#
# Another more sound strategy would have been to shift the leakage until we
# minimize the distance between leakages, but the soundness of the
# synchronisation is not the point here.

class Synchronisation:
    def __init__(self, leakage_ref):
        self.ref_offset = leakage_ref.argmax()

    def __call__(self, leakage):
        # We need to find the peak in each leakage, and roll it to match the ref_peak
        peak_offset = leakage.argmax()
        return np.roll(leakage, self.ref_offset - peak_offset)

# Now we can instantiate a `Synchronisation`, using the leakage of the first
# trace as a reference.
# As seen in the first tutorial, we just have to set the container
# `leakage_processing` attribute:
ref_leakage = container[0].leakage
container.leakage_processing = Synchronisation(ref_leakage)

# Once again, we can plot the leakages, to realize that they have been
# transformed, and should match more:
container.plot_leakage(range(3))

# Don't forget that you always have the possibility to store your synchronized
# traces on disk:

from lascar import Hdf5Container

hdf5_container = Hdf5Container.export(container, "tmp.h5")

