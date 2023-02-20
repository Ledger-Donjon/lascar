from lascar import *
from lascar.tools.aes import *

#from lascar import *
#from lascar.tools.aes import *

container = BasicAesSimulationContainer(
    300, noise=3
)  # We use the BasicAesSimulationContainer with 300 traces


def generate_guess_function(byte):
    def guess_function(value, guess):
        return hamming(sbox[value.plaintext[byte]^guess])
    return guess_function

CPAengs = [CpaEngine(generate_guess_function(byte), range(256), name="CpaSbox{}".format(byte), solution=container.key[byte]) for byte in range(16) ]
engGroup = GroupedEngines('CPAgroup', *CPAengs)
CPAsession = Session(
    container,
    engine=engGroup,
    output_steps=range(0,300,10),
    output_method=FullRankProgressionOutputMethod(engGroup,legend=True, bin_width=0.005)
    )
CPAsession.run()
