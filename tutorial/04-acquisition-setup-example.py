# In this tutorial we will show how to set up an `AbstractContainer` dedicated
# to emulate a simple (dummy) side-channel acquisition setup. The context here
# is the use of lascar for the acquisition phase.
#
# Say we are targeting a device running an AES, that we can drive through a
# python class `Dut` (for Device Under Test). This class has a method that
# commands the device to run the targeted operation, and returns the
# plaintext/ciphertext.

import numpy as np


class Dut:
    def go(self):
        # Dummy AES, returns the plaintext and the ciphertext, concatenated.
        plaintext = np.random.randint(0, 256, (16,))  # 16 random bytes
        ciphertext = np.random.randint(
            0, 256, (16,)
        )  # 16 random bytes for the ciphertext
        return np.append(plaintext, ciphertext)


# Beside, we have an `Oscilloscope` class, which returns the power measurement
# of the device through the method `get_trace`:


class Oscilloscope:
    def get_trace(self):
        # Return the side-channel leakage: here a vector of 100 floats
        return np.random.rand(100)


# We create an `AcquisitionSetup` class, inheriting from `AbstractContainer`, and
# override the `generate_trace` method which will request both device and
# oscilloscope.

from lascar import AbstractContainer, Trace


class AcquisitionSetup(AbstractContainer):
    def __init__(self, number_of_traces: int):
        """
        :param number_of_traces: Number of traces in the container
        """
        super().__init__(self, number_of_traces)
        self.dut = Dut()
        self.oscilloscope = Oscilloscope()

    def generate_trace(self, index: int):
        """
        Method required by `AcquisitionSetup` to work properly.

        :param index: index of trace, not used here.
        :return: Trace with leakage from oscilloscope, and value from the dut
            plaintext/ciphertext.
        """
        # The container logger can be used!
        self.logger.debug("Generate trace %d", index)
        value = self.dut.go()
        leakage = self.oscilloscope.get_trace()
        return Trace(leakage, value)


# Now everything is ready to create our `AcquisitionSetup`:
acquisition = AcquisitionSetup(100)

# This container is Abstract. Its 100 traces are stored nowhere, yet they can be
# accessed:
print("trace 0:", acquisition_container[0])
print("trace 10:", acquisition_container[10])

# More importantly, this container can be converted to a Hdf5Container, so the
# traces get saved to the disk. The export method takes here all its sense.

from lascar import Hdf5Container

hdf5 = Hdf5Container.export(acquisition, "tmp.h5")
