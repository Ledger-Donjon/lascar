import numpy as np
from rainbow.devices.stm32 import rainbow_stm32f215
from lascar import (
    AbstractContainer,
    Trace,
    CpaEngine,
    Session,
    MatPlotLibOutputMethod,
    ScoreProgressionOutputMethod,
)
from lascar.tools.leakage_model import hamming_weight
from lascar.tools.aes import sbox


class RainbowSubBytesContainer(AbstractContainer):
    """
    RainbowSubBytesContainer is a class that will define a lascar container using a rainbow device.

    We choose in this example to study a basic implementation of a toy AES subbytes function.
    
    The following C code was compiled with arm resulting into the code.elf file:

            void subbytes(uint8_t *buffer, int length)
            {
                for(int i=0;i<length;i++){ 
                    buffer[i] = sbox[buffer[i] ^ buffer[i+length]];
                }
            }

    As an AbstractContainer, RainbowSubBytesContainer must implement a generate_trace() method
    which will generate at each call a lascar Trace 
    (ie a couple of leakage/value) resulting  from a subbyte execution by rainbow.


    (the binary file used here can be loaded on a scaffold board to validate actual behavior, see the scaffold/ folder in lascar examples)

    """

    def __init__(
        self, number_of_traces, key=[42] * 16, noise=2, binary_file="code.elf", **kwargs
    ):
        """
        :param number_of_traces: how many traces for the lascar container
        :param key: key to be used by the subbytes function. Can be set to "random"
        :param noise: Noise added to the simulated leakage
        :param binary_file: the file used by rainbow. Must be an arm compiled .elf file containing a "subbytes" function.
        """

        # Initialize rainbow device:
        # we use a precompiled with arm code.elf file, which contains the targeted function: subbytes
        self.device = rainbow_stm32f215(sca_mode=1)
        self.device.load(binary_file)

        # This part is lascar dependent:
        # We define what will be the type of the value generated at each trace
        # (here, 16 bytes of plaintext + 16 bytes of key)
        value_dtype = np.dtype(
            [("plaintext", np.uint8, (16,)), ("key", np.uint8, (16,)),]
        )

        self.value = np.zeros((), value_dtype)
        if key is not "random":
            self.random_key = False
            self.value["key"] = key
        else:
            self.random_key = True

        self.noise = noise
        self.seed = 42
        AbstractContainer.__init__(self, number_of_traces, **kwargs)

    def generate_trace(self, idx):

        np.random.seed(seed=self.seed ^ idx)  # for reproducibility

        # We prepare the value for this trace:
        self.value["plaintext"] = np.random.randint(0, 256, (16,), np.uint8)
        if self.random_key:
            self.value["key"] = np.random.randint(0, 256, (16,), np.uint8)

        self.device.reset()  # device must be reset/parametred at each function execution
        self.device.trace_regs = 1

        address_for_input_buffer = (
            0xCAFE00  # arbitrary value chosen for the input buffer address
        )
        self.device[address_for_input_buffer] = bytes(self.value["plaintext"]) + bytes(
            self.value["key"]
        )  # we build the input buffer for the subbytes function
        self.device[
            "r0"
        ] = address_for_input_buffer  # first argument of the subbytes function
        self.device["r1"] = 16  # second argument of the subbytes function

        self.device.start(
            self.device.functions["subbytes"], 0
        )  # rainbow launch the "subbytes" function

        # we prepare the leakage for this trace:
        leakage = np.fromiter(
            map(hamming_weight, self.device.sca_values_trace), dtype=np.uint8
        )  # a hamming_weight model is applied to the rainbow-generated leakage
        leakage = (
            np.random.normal(0, self.noise, len(leakage)) + leakage
        )  # artificial noise is added to the leakage

        return Trace(leakage, self.value)


if __name__ == "__main__":

    container = RainbowSubBytesContainer(250)
    engine = CpaEngine(
        lambda value, secret: sbox[value["plaintext"][5] ^ secret],
        range(256),
        solution=42,
    )
    session = Session(
        container,
        engine,
        output_method=ScoreProgressionOutputMethod(engine),
        output_steps=20,
    ).run()
