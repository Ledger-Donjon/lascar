"""

We know how to build Containers and Session, and now we will mount a classical Differential Power Attack (DPA) using lascar.

(see https://www.paulkocher.com/doc/DifferentialPowerAnalysis.pdf)

For that, we will build a DpaEngine, and register it to a Session.

(The folder lascar/examples/base contains examples for different kinds of side-channel attacks/characterization)

"""

# First the Container:
from lascar import BasicAesSimulationContainer

container = BasicAesSimulationContainer(500, noise=1)


"""

Then we build the DpaEngine.

If you take a look at the help for DpaEngine, you'll see that it needs 3 things to be instanciated:
- a name for the engine ("dpa" in our case)
- a selection function (under guess hypothesis): this function will separate the traces into two sets, depending on a hypothesis: "guess". This function will be applied on every trace values, for every possible guess.
- a guess_range: what are the guesses you want to test?

In this example, we will focus on the LSB bit of the 3rd AES sbox. This value is conditioned by a single key byte (256 guesses)

"""

from lascar.tools.aes import sbox


def selection_function(value, guess):
    return sbox[value["plaintext"][3] ^ guess] & 1


guess_range = range(256)


from lascar import DpaEngine

dpa_engine = DpaEngine("dpa", selection_function, guess_range)


# We can now create a Session, register the dpa_lsb_engine, and run it.
from lascar import Session

session = Session(container, engine=dpa_engine)
# session.add_engine( dpa_lsb_engine) # the engine can be added after the session creation

session.run(batch_size=100)  # the session will load traces by batches of 100 traces

"""
Now, to get the result, one solution could be to request the dpa_lsb_engine.finalize() method.
(As most of the engines, the finalize() method returns sca results)

For more option about how to manage results of sca, please follow the next step of the tutorial.

"""
results = dpa_engine.finalize()

print(results.shape)
print("Best Guess is %02X." % results.max(1).argmax())

import matplotlib.pyplot as plt

_ = plt.plot(results.T)
_ = plt.show()
