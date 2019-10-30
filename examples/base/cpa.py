"""
In this script, we show how to perform Correlation Power Analysis with lascar to retrieve an AES keybyte.

The engine we need here is the CpaEngine.
It needs:
- a selection function (under guess hypothesis) on the sensitive value (here the output of the sbox at first round):
    This function answers the question: "Under the 'guess' hypothesis', how do I model the behavior with 'value'?
- a "guess_range" which will define what are the guess possible values

"""
from lascar import *
from lascar.tools.aes import sbox


container = BasicAesSimulationContainer(
    200, noise=2
)  # We use the BasicAesSimulationContainer with 2000 traces


def selection_function(
    value, guess
):  # selection_with_guess function must take 2 arguments: value and guess
    """
    What would the hamming weight of the output of the 3rd sbox be if the key was equal to 'guess' ?
    """
    return hamming(sbox[value["plaintext"][3] ^ guess])


guess_range = range(
    256
)  # the guess values: here we make hypothesis on a key byte, hence range(256)

cpa_engine = CpaEngine("cpa_plaintext_3", selection_function, guess_range)

session = Session(
    container, engine=cpa_engine, output_method=MatPlotLibOutputMethod(cpa_engine)
)

session.run(batch_size=200)


"""
Now let's compute the 16 cpa retrieving all key bytes in //
We chose here to display the progression of each attack depending on the number of traces.
"""


def generate_selection_function(byte):
    def selection_with_guess(
        value, guess
    ):  # selection_with_guess function must take 2 arguments: value and guess
        return hamming(sbox[value["plaintext"][byte] ^ guess])

    return selection_with_guess


cpa_engines = [
    CpaEngine(
        "cpa_%02d" % i,
        generate_selection_function(i),
        guess_range,
        solution=container.key[i],
    )
    for i in range(16)
]

session = Session(
    container,
    engines=cpa_engines,
    name="cpa on 16 bytes",
    output_method=ScoreProgressionOutputMethod(*cpa_engines),
    output_steps=10,
).run(batch_size=50)
