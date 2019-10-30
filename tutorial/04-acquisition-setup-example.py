"""
In this script we will show how to set up an AbstractContainer, dedicated to emulate an (dummy) side-channel acquisition setup.

The context here is the use of lascar for the acquisition phase.

Say we are targeting a device running an AES, that we can drive through a python class Dut (for Device Under Test).
This class has a method that commands the device to run the targeted operation, and returns the plaintext/ciphertext.

Beside, we have an Oscilloscope class, which returns the power measurment of the device through the method.

We create a class AcquisitionSetup, inheriting from AbstractContainer, and override the generate_trace() method which will request both device and oscilloscope.

"""
from lascar import AbstractContainer, Trace
import numpy as np

# First the Device Under Test (Dut):
class Dut:
    def __init__(self):
        # ...dummy initialisation, put here all the communication objects, constants etc...
        self.foo = "foo"
        self.dumb = "dumb"
        # ...

    def go(self):
        # dummy aes, returns the plaintext and the ciphertext, concatenated.

        plaintext = np.random.randint(
            0, 256, (16,)
        )  # 16 random bytes for the plaintext
        # self.aes(plaintext) : request the device to cipher plaintext
        ciphertext = np.random.randint(
            0, 256, (16,)
        )  # 16 random bytes for the ciphertext

        return np.append(plaintext, ciphertext)


# Then the Oscilloscope:
class Oscilloscope:
    def __init__(self):
        # ...dummy initialisation, put here all the communication objects, constants etc...
        self.bar = "bar"
        self.dumb = "dumb"
        # ...

    def get_trace(self):
        # return the side channel leakage: here a vector of 100 float
        return np.random.rand(100)


# Then the AbstractContainer:
class AcquisitionSetup(AbstractContainer):
    def __init__(self, number_of_traces):
        """
        :param number_of_traces: only required argument for the constructor of an AbstractContainer
        """

        self.dut = Dut()
        self.oscilloscope = Oscilloscope()

        AbstractContainer.__init__(self, number_of_traces)

    def generate_trace(self, index):
        """
        generate_trace is the only method needed by AcquisitionSetup to work properly
        :param index: index of trace, not used here.
        :return:  Trace with leakage from oscilloscope, and value from the dut plaintext/ciphertext
        """

        self.logger.debug(
            "Generate trace %d", index
        )  # The container logger can be used!

        value = self.dut.go()
        leakage = self.oscilloscope.get_trace()

        return Trace(leakage, value)


# Now everything is ready to create our AcquisitionContainer:
acquisition_container = AcquisitionSetup(100)
print("acquisition_container:", acquisition_container)


# acquisition_container is Abstract. Its 100 traces are stored nowhere. But they can be accessed:
print("trace 0:", acquisition_container[0])
print("trace 10:", acquisition_container[10])


# But more importantly, acquisition_container can be converted to a Hdf5Container: (the export method takes here all its sense)
from lascar import Hdf5Container

hdf5_container = Hdf5Container.export(acquisition_container, "tmp.h5")
print("hdf5_container:", hdf5_container)
