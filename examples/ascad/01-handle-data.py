"""
lascar on ASCAD Database

(https://github.com/ANSSI-FR/ASCAD)

Objective in this script:

- Translate the ASCAD trace files into a lascar Container.

- Expose lascar features to simplify the generation the ASCAD.h5 file from ATMega8515_raw_traces.h5
    (as it is done in https://github.com/ANSSI-FR/ASCAD/blob/master/ASCAD_generate.py#L42)


lascar includes many features to handle side-channel data.
It all starts with the `Container` class.

In this script we will need :

 - `FilteredContainer` : to indicate that we will split the 60000 traces from ATMega8515_raw_traces.h5 into subfiles of traces.
The original container will be filtered using traces indices.

 - `leakage_section` : as a kwarg to the Container constructor, is use to indicate which leakage time samples will be used
the poi (Points Of Interest)

- `leakage_processing` : as a kwarg to the Container constructor, it is a function applied to the leakage, to modify it.
(usualy it is used as a synchronisation tool, but here we want to DEsynchronise the traces)

- `Hdf5Container.export` : static method used to convert a container into a `Hdf5Container`

"""
from lascar import *
import sys

if not len(sys.argv) == 2:
    print("Need to specify the location of ASCAD_DIR.")
    print("USAGE: python3 %s ASCAD_DIR"% sys.argv[0])
    exit()

ASCAD_DIR = sys.argv[1]
filename = ASCAD_DIR + "/ASCAD_data/ASCAD_databases/ATMega8515_raw_traces.h5"

"""
The trace format used by ASCAD is very similar to lascar's Hdf5Container.
The only difference is in the naming of the datasets.
Instead of (leakages, values), ASCAD uses (traces, metadata).
"""

container = Hdf5Container(filename, leakages_dataset_name="traces", values_dataset_name="metadata")

trace = container[0] # The first trace
print(trace)

#container.plot_leakage(range(10)) # plot the 10 first leakages

poi = range(45400, 46100) # poi for the byte 2 of the AES first round stats
profiling_index = range(500) # the first 500 traces are used for the profiling traces
attack_index = range(500,600) # the 100 following traces are used for the attack
# the other traces are ignored for this demo


def leakage_desynchro(offset):
    """
    leakage_desynchro outputs a function, to be applied to each leakage, that will randomly shift them by a step within [-offset/2, offset/2]
    :param offset:
    :return: function to be applied on the leakages, for desynchronisation
    """
    if offset == 0:
        return lambda leakage:leakage
    return lambda leakage: np.roll(leakage, np.random.randint(-offset//2, offset//2))

for filename, desynchro in [("ASCAD.h5", 0), ("ASCAD_desync50.h5", 50), ("ASCAD_desync100.h5", 100)]: 

    print("\n--- Creating %s ---"%filename)

    profile_container = FilteredContainer(  container, 
                                            profiling_index, 
                                            leakage_section=poi, 
                                            leakage_processing=leakage_desynchro(desynchro)
                                          )

    Hdf5Container.export(   profile_container,
                            filename, 
                            leakages_dataset_name="/Profiling_traces/traces", 
                            values_dataset_name="/Profiling_traces/metadata"
                            )


    attack_container = FilteredContainer(   container, 
                                            attack_index, 
                                            leakage_section=poi, 
                                            leakage_processing=leakage_desynchro(desynchro)
                                            )

    Hdf5Container.export(   attack_container,
                            filename,
                            leakages_dataset_name="/Attack_traces/traces", 
                            values_dataset_name="/Attack_traces/metadata"
                        )
