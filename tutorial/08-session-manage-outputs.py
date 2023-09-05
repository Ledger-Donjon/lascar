# In side-channel analysis, output management is a crucial final step.
#
# During processing, a large amount of data is manipulated and many statistics
# are computed. It must be decided which information can be extracted and what
# measures should be presented:
#
# - extract only the most substantial info (i.e. the secret key)?
# - extract the info for all guesses?
# - monitor the progression of the attack?
# - visualize the results?
# - write the results into a file?
# - what kind of visualization?
# - what kind of file format?
#
# In Lascar, dealing with results is achieved using `OutputMethod`.
# An `OutputMethod` is an object used by the `Session` to define how the results
# must be processed.
#
# Also, the `output_steps` parameter of the `Session` class can be used to
# indicate at which number of traces the engine should compute their results.
#
# Every time an engine has results to deliver (through the `finalize()`
# method), it goes by the `OutputMethod`.
#
# Lascar already implements a few output methods that will be presented in this
# tutorial (and in the examples/ folder):
#
# - `DictOutputMethod`: results are all stored inside a python dictionnary, with
#   the possibility to save it using pickle.
# - `Hdf5OutputMethod`: results are stored inside a hdf5 file, all attacks are
#   groups, and datasets for each output step.
# - `MatPlotLibOutputMethod`: results are displayed on a matplotlib plot, with
#   parameters to indicate the layout (in case of multiple attacks).
# - `ScoreProgressionOutputMethod`: results are parsed, and the best scores are
#   extracted, and displayed in function of the number of trace.
# - `RankProgressionOutputMethod`: results are parsed, and the rank of the best
#   scores are extracted, and displayed in function of the number of trace.
#
# The previous script of the DPA example tutorial, which runs on simulated AES
# traces, is reused here. This time, two DPA are run in parallel: one on the LSB
# of the output of the 3rd sbox, the other on the MSB.

from lascar import *
from lascar.tools.aes import sbox

container = BasicAesSimulationContainer(500, noise=0.01)
guess_range = range(256)


def selection_function_lsb(value, guess):
    return sbox[value["plaintext"][3] ^ guess] & 1


def selection_function_msb(value, guess):
    return (sbox[value["plaintext"][3] ^ guess] >> 7) & 1


dpa_lsb_engine = DpaEngine(
    selection_function_lsb, guess_range, solution=container.key[3], name="dpa_lsb"
)
dpa_msb_engine = DpaEngine(
    selection_function_msb, guess_range, solution=container.key[3], name="dpa_msb"
)

# DictOutputMethod:

# Accepts any number of engine arguments
dict_output_method = DictOutputMethod(dpa_lsb_engine, dpa_msb_engine)
# If a filename is specified, DictOutputMethod will save them using pickle
dict_output_method = DictOutputMethod(
    dpa_lsb_engine, dpa_msb_engine, filename="dict_output_method.pickle"
)

session = Session(
    container,
    engines=[dpa_lsb_engine, dpa_msb_engine],
    output_method=dict_output_method,
).run(batch_size=50)

# Here dict_outut_method has been updated. It contains the results of the
# engines, which can be verified like this:
assert np.all(dict_output_method["dpa_lsb"] == dpa_lsb_engine.finalize())
assert np.all(dict_output_method["dpa_msb"] == dpa_msb_engine.finalize())

# Results have also been saved to an output pickle file:
assert np.all(
    DictOutputMethod.load("dict_output_method.pickle")["dpa_lsb"]
    == dpa_lsb_engine.finalize()
)

# To add multiple output steps during the analysis, the `output_steps` parameter
# can be issued as in the following example:
session = Session(
    container,
    engines=[dpa_lsb_engine, dpa_msb_engine],
    output_method=dict_output_method,
    output_steps=[10, 20, 50],
).run(batch_size=50)

# With this feature, it possible to retrieve intermediate results using
# indexing, such as:
dict_output_method["dpa_lsb"][10]  # Result for dpa_lsb after 10 traces
dict_output_method["dpa_lsb"][20]  # Result for dpa_lsb after 20 traces
dict_output_method["dpa_lsb"][50]  # Result for dpa_lsb after 50 traces

# Hdf5OutputMethod is very similar to the DictOutputMethod. With this class, the
# result are exported to a file in HDF5 format. Unlike DictOutputMethod, the
# output filename is mandatory here.
hdf5_output_method = Hdf5OutputMethod("hdf5_output.h5", dpa_lsb_engine, dpa_msb_engine)

session = Session(
    container,
    engines=[dpa_lsb_engine, dpa_msb_engine],
    output_method=hdf5_output_method,
    output_steps=[10, 20, 50],
).run(batch_size=50)

# `h5ls` can be used to inspect the content of the generated HDF5 output file.
# In particular, we can observe that there is a dataset containing the results
# for the intermediate steps:
#
# $ h5ls -r hdf5_output.h5
# /                        Group
# /dpa_lsb                 Group
# /dpa_lsb/10              Dataset {256, 26}
# /dpa_lsb/20              Dataset {256, 26}
# /dpa_lsb/50              Dataset {256, 26}
# /dpa_lsb/500             Dataset {256, 26}
# /dpa_msb                 Group
# /dpa_msb/10              Dataset {256, 26}
# /dpa_msb/20              Dataset {256, 26}
# /dpa_msb/50              Dataset {256, 26}
# /dpa_msb/500             Dataset {256, 26}
# /mean                    Group
# /mean/10                 Dataset {26}
# /mean/20                 Dataset {26}
# /mean/50                 Dataset {26}
# /mean/500                Dataset {26}
# /var                     Group
# /var/10                  Dataset {26}
# /var/20                  Dataset {26}
# /var/50                  Dataset {26}
# /var/500                 Dataset {26}
#
# Note: To access a HDF5 dataset value, use .value attribute

# `Hdf5OutputMethod` has a static method to load a hdf5_output_method:
hdf5_output_method_bis = Hdf5OutputMethod.load("hdf5_output.h5")
assert np.all(hdf5_output_method_bis["dpa_lsb/500"][()] == dpa_lsb_engine.finalize())

# The results can also be plotted using matplotlib, using
# `MatPlotLibOutputMethod`. If a solution has been set to the `dpa_engines`, the
# corresponding plot is highlighted. The `filename` parameter, which is
# optional, enables exporting the figure to an image file.
mpl_output_method = MatPlotLibOutputMethod(
    dpa_lsb_engine, dpa_msb_engine, filename="foo.png"
)
session = Session(
    container, engines=[dpa_lsb_engine, dpa_msb_engine], output_method=mpl_output_method
).run(batch_size=50)

# Around ScoreProgressionOutputMethod and RankProgressionOutputMethod
# The following example shows how to monitor the progression of the scores of
# our 2 attacks, every 10 traces. You'll observe in particular that multiple
# output methods can be given to a session:

score_progression_output_method = ScoreProgressionOutputMethod(
    dpa_lsb_engine, dpa_msb_engine
)
rank_progression_output_method = RankProgressionOutputMethod(
    dpa_lsb_engine, dpa_msb_engine
)
session = Session(
    container,
    engines=[dpa_lsb_engine, dpa_msb_engine],
    output_method=[score_progression_output_method, rank_progression_output_method],
    output_steps=10,
).run(batch_size=50)

# Scores and steps can be accessed:
score_progression_output_method.get_scores()
score_progression_output_method.get_scores_solution()
score_progression_output_method.get_steps()
