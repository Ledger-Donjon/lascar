Acquisition setup example
=========================

In this tutorial we will show how to set up an
:class:`AbstractContainer <lascar.container.container.AbstractContainer>`
dedicated to emulate a simple (dummy) side-channel acquisition setup. The
context here is the use of lascar for the acquisition phase.

Say we are targeting a device running an AES, that we can drive through a python
class :class:`Dut` (for Device Under Test). This class has a method that commands
the device to run the targeted operation, and returns the plaintext/ciphertext.

.. code-block:: python

   import numpy as np

   class Dut:
       def go(self):
           # Dummy AES, returns the plaintext and the ciphertext, concatenated.
           plaintext = np.random.randint(0, 256, (16,))  # 16 random bytes
           ciphertext = np.random.randint(0, 256, (16,))
           return np.append(plaintext, ciphertext)

Beside, we have an :class:`Oscilloscope` class, which returns the power
measurement of the device through the method :meth:`get_trace`:

.. code-block:: python

   class Oscilloscope:
       def get_trace(self):
           # Return the side-channel leakage: here a vector of 100 floats
           return np.random.rand(100)

We create an :class:`AcquisitionSetup` class, inheriting from
:class:`AbstractContainer <lascar.container.container.AbstractContainer>`, and
override the :meth:`generate_trace` method which will request both device and
oscilloscope.

.. code-block:: python

   from lascar import AbstractContainer, Trace

   class AcquisitionSetup(AbstractContainer):
       def __init__(self, number_of_traces: int):
           """
           :param number_of_traces: Number of traces in the container
           """
           self.dut = Dut()
           self.oscilloscope = Oscilloscope()
           super().__init__(number_of_traces)

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

Now everything is ready to create our :class:`AcquisitionSetup`.
This container is Abstract. Its 100 traces are stored nowhere, yet they can be
accessed:

.. code-block:: python

   acquisition = AcquisitionSetup(100)
   print("trace 0:", acquisition_container[0])
   print("trace 10:", acquisition_container[10])

More importantly, this container can be converted to a
:class:`Hdf5Container <lascar.container.hdf5_container.Hdf5Container>`,
so the traces get saved to the disk. The export method takes here all its sense.

.. code-block:: python

   from lascar import Hdf5Container

   hdf5 = Hdf5Container.export(acquisition, "tmp.h5")
