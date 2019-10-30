"""
In this script we will demonstrate how to use lascar to perform leakage synchronisation.

In side-channel, your leakage needs to be slightly "stackable":
It is very common that, from a trace to another, physical behaviors induce temporal shifting in the leakage.
Leakage Synchronization is the name given to the post-processing method you apply on it to make all leakages "stackable"

In the following example we will design an AbstractContainer that will generate fake traces "desynchronized"
We will then design a Synchronization method, which will consist in a leakage_processing applied to the AbstractContainer, so that it will deliver synchronized traces.

"""

from lascar import AbstractContainer, Trace
import numpy as np

"""
First the SimulatedContainer, on which we will set up the synchronization:
"""


class SimulatedContainer(AbstractContainer):
    def generate_trace(self, idx):
        """
        our leakage will consist in 100 time samples, with a peak randomly inserted.
        Imagine this peak contains the side-channel information.
        """

        leakage = np.random.rand(100)
        random_offset = np.random.randint(
            20, 80
        )  # the offset where the peak will be inserted
        leakage[random_offset : random_offset + 11] += np.hanning(11) * 4

        value = np.zeros(())  # the value wont be used in here...

        return Trace(leakage, value)


simulated_container = SimulatedContainer(
    100
)  # 100 is the number of traces for the SimulatedContainer, needed by the AbstractContainer constructor.


# We can use the plot_leakge() method to display the first traces, and note that the leakages are not stackable, as expected
simulated_container.plot_leakage(range(3))


"""
Now the synchtonization process.

leakage_procesing will be used, so we need to design a function, that takes a leakage as input and returns a transformed leakage.
Actually, we wont use a function, but a callable class (ie a class that implements the __call__ method, and hence behaves as a function, once instanciated.
The reason why we do that, is that our synchronization process will attempt to overlay leakages based on a reference trace leakage

The synchronization strategy will find the peak in each trace (argmax in this case) and roll the leakages to match the first peak.

(another more sound strategy would have been to shift the leakage until we minimize the distance between leakages, 
but the soundness of the synchronization is not the point here)

"""


class Synchronization:
    def __init__(self, leakage_ref):
        self.ref_peak_offset = leakage_ref.argmax()

    def __call__(self, leakage):
        """
        We need to find the peak in each leakage, and roll it to match the ref_peak
        """
        peak_offset = leakage.argmax()

        return np.roll(leakage, self.ref_peak_offset - peak_offset)


# Now we can instatiate a Synchronisation, using the leakage of the first trace as a reference:
ref_leakage = simulated_container[0].leakage
synchronization = Synchronization(ref_leakage)

# As seen in the first tutorial, we just have to set the simulated_container leakage_processing attribute:
simulated_container.leakage_processing = synchronization


# Once again, we can plot the leakages, to realize that they have been transformed, and should match more:
simulated_container.plot_leakage(range(3))

# Dont forget that you always have the possibility to store your synchronized traces:
from lascar import Hdf5Container

hdf5_container = Hdf5Container.export(simulated_container, "tmp.h5")
