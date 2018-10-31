"""

In side-channel, ouptut managment is crucial.

You process large ammount of data, compute statistics on them, and then ...

Then ... what to do with the results?
- extract only the most substantial info (ie the secret key)
- extract the info for all guesses
- monitor the progression of your attack
- visualize the results?
- write them into a file?
- what kind of visualization? what kind of file format?

In lascar, whenever you want to deal with results management, you have to go through an OutputMethod.

An OutputMethod is an object used by the Session to indicate how an user would want to process its results.

An other Session parameter for managing output is 'output_steps", used to indicate at which numbers of traces the engine should compute their results

Every time your engines has results to deliver (through the .finalize() method), it goes by the OutputMethod.

lascar already implements a few OutputMethods that will be presented in this scripts (and in the examples/ folder).

We will here demonstrate how to use:

- DictOutputMethod: the results are all stored inside a python dict, with the possibility to save it using pickle
- Hdf5OutputMethod: the resullts are stored inside a hdf5 file, all attacks are groups, and datasets for each output_steps
- MatPlotLibOutputMethod: the results are displayed on a matplotlib plot, with parameters to indicate the layout (in case of multiple attacks)
- ScoreProgressionOutputMethod: the results are parsed, and the best scores are extracted, and displayed in function of the number of trace
- RankProgressionOutputMethod: the results are parsed, and the rank of the best scores are extracted, and displayed in function of the number of trace

using the previous script of a DPA on simulated AES traces.
This time we will perform 2 DPA in //: one on the lsb of the output of the 3rd sbox, the other on the msb

"""

from lascar import *
from lascar.tools.aes import sbox

container = BasicAesSimulationContainer(500,noise=0.01)

#We set up the two dpa_engines first:
guess_range= range(256)

def selection_function_lsb(value,guess):
    return sbox[ value['plaintext'][3] ^ guess] & 1

def selection_function_msb(value,guess):
    return (sbox[ value['plaintext'][3] ^ guess]>>7) & 1

dpa_lsb_engine = DpaEngine('dpa_lsb', selection_function_lsb, guess_range, solution=container.key[3])
dpa_msb_engine = DpaEngine('dpa_msb', selection_function_lsb, guess_range, solution=container.key[3])



"""

Around the DictOutputMethod:

"""
dict_output_method = DictOutputMethod(dpa_lsb_engine,dpa_msb_engine) # the engine you want to output have to be passed as *args
dict_output_method = DictOutputMethod(dpa_lsb_engine,dpa_msb_engine,filename="dict_output_method.pickle") # If a filename is specified, DictOutputMethod will be saved using pickle


session = Session(container, engines=[dpa_lsb_engine,dpa_msb_engine], output_method=dict_output_method).run(batch_size=50) # the session registers the instanciated OutputMethod
# here dict_outut_method has been updated:
print(dict_output_method['dpa_lsb'].shape)
# dict_output_method['dpa_lsb'] contains here only the dpa_lsb_engine.finalize() return:
assert np.all(dict_output_method['dpa_lsb'] == dpa_lsb_engine.finalize())
assert np.all(dict_output_method['dpa_msb'] == dpa_msb_engine.finalize())


dict_output_method_bis = DictOutputMethod.load('dict_output_method.pickle') # DictOutputMethod has a static method to load a dict_output_method
assert np.all(dict_output_method_bis['dpa_lsb'] == dpa_lsb_engine.finalize())


# Now if we want to add output_steps:
session = Session(container, engines=[dpa_lsb_engine, dpa_msb_engine], output_method=dict_output_method, output_steps= [10, 20, 50]).run(batch_size=50) # the session also registers the output_steps you want
# At the specified output_steps, the output_method is updated. So that we now have

# dict_output_method['dpa_lsb'][10] contains results for dpa_lsb after 10 traces
# dict_output_method['dpa_msb'][20] contains results for dpa_msb after 100 traces
# dict_output_method['dpa_lsb'][50] contains results for dpa_lsb after 150 traces
# dict_output_method['dpa_msb'][100] contains results for dpa_msb after 200 traces




"""

Around the Hdf5OutputMethod:
(very similar to the DictOutputMethod except that the filename is mandatory during the constructor)

"""

hdf5_output_method = Hdf5OutputMethod("hdf5_output.h5", "dpa_lsb_engine", dpa_lsb_engine, dpa_msb_engine) # for Hdf5OutputMethod, a filename has to be specified

session = Session(container, engines=[dpa_lsb_engine,dpa_msb_engine], output_method=hdf5_output_method, output_steps= [10, 20, 50]).run(batch_size=50) # the session also registers the output_steps you want

# $ h5ls -r hdf5_output.h5
# /                        Group
# /dpa_lsb                 Group
# /dpa_lsb/100             Dataset {256, 26}
# /dpa_lsb/1000            Dataset {256, 26}
# /dpa_lsb/1500            Dataset {256, 26}
# /dpa_lsb/200             Dataset {256, 26}
# /dpa_lsb/2000            Dataset {256, 26}
# /dpa_lsb/500             Dataset {256, 26}
# /dpa_msb                 Group
# /dpa_msb/100             Dataset {256, 26}
# /dpa_msb/1000            Dataset {256, 26}
# /dpa_msb/200             Dataset {256, 26}
# /dpa_msb/500             Dataset {256, 26}


# At the specified output_steps, the output_method is updated. So that we now have
# hdf5_output_method['dpa_lsb/10'] is the datasets containing results for dpa after 10 traces
# hdf5_output_method['dpa_lsb/20'] is the datasets containing results for dpa after 100 traces
# hdf5_output_method['dpa_lsb/50'] is the datasets containing results for dpa after 150 traces
# hdf5_output_method['dpa_lsb/100'] is the datasets containing results for dpa after 200 traces

# IMPORTANT: To access a hdf5 dataset value, use .value attribute


hdf5_output_method_bis = Hdf5OutputMethod.load('hdf5_output.h5') # Hdf5OutputMethod has a static method to load a hdf5_output_method
assert np.all(hdf5_output_method_bis['dpa_lsb/500'].value == dpa_lsb_engine.finalize())


"""

Arround MatPlotLibOutputMethod

"""

mpl_output_method = MatPlotLibOutputMethod(dpa_lsb_engine, dpa_msb_engine)
session = Session(container, engines=[dpa_lsb_engine,dpa_msb_engine], output_method=mpl_output_method).run(batch_size=50) # the session registers the instanciated OutputMethod
#As you can see, if a solution has been set to the dpa_engines, it is displayed in a special font


# a filename can be specified to save the plot into a png:
mpl_output_method = MatPlotLibOutputMethod(dpa_lsb_engine, dpa_msb_engine, filename='foo.png')
session = Session(container, engines=[dpa_lsb_engine,dpa_msb_engine], output_method=mpl_output_method).run(batch_size=50) # the session registers the instanciated OutputMethod


"""

Arround ScoreProgressionOutputMethod and ScoreProgressionOutputMethod
 
We monitor the progression of the scores of our 2 attacks, every 10 traces: 
 
"""

score_progression_output_method = ScoreProgressionOutputMethod(dpa_lsb_engine, dpa_msb_engine)
session = Session(container, engines=[dpa_lsb_engine,dpa_msb_engine], output_method=score_progression_output_method, output_steps=10).run(batch_size=50) # the session registers the instanciated OutputMethod

# scores and steps can be accessed:

# score_progression_output_method.get_scores()
# score_progression_output_method.get_scores_solution()
# score_progression_output_method.get_steps()



# The same goes for RankProgressionOutputMedhod:
rank_progression_output_method = RankProgressionOutputMethod(dpa_lsb_engine, dpa_msb_engine)
session = Session(container, engines=[dpa_lsb_engine,dpa_msb_engine], output_method=rank_progression_output_method, output_steps=10).run(batch_size=50) # the session registers the instanciated OutputMethod



"""
Last, but not least:

It is possible to register several OutputMethod to the session:

"""

session = Session(container, engines=[dpa_lsb_engine,dpa_msb_engine], output_method=[DictOutputMethod(dpa_msb_engine),ScoreProgressionOutputMethod(dpa_msb_engine), RankProgressionOutputMethod(dpa_msb_engine)], output_steps=10).run(batch_size=50) # the session registers the instanciated OutputMethod


"""
The tutorial is for now done.
Take a look at the examples/ folder
"""