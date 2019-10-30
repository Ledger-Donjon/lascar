"""
lascar on ASCAD Database

(https://github.com/ANSSI-FR/ASCAD)

Objective in this script:
 Use lascar to compute the 5 Signal-to-Noise Ratios (SNRs) described in chapter 2.5.2 of
"Study of Deep Learning Techniques for Side-Channel Analysis and Introduction to ASCAD Database"

In the end of the script, the 5 SNRs are displayed.

The table at chapter 2.5.2 is pasted hereafter:

Name Type Definition of the target variable Z
SNR1 unmasked sbox output sbox(p[3] ⊕ k[3])
SNR2 masked sbox output sbox(p[3] ⊕ k[3]) ⊕ rout
SNR3 common sbox output mask rout
SNR4 masked sbox output in linear parts sbox(p[3] ⊕ k[3]) ⊕ r[3]
SNR5 sbox output mask in linear parts r[3]

(Only 5000 traces are used here)

"""
import sys
from lascar import *
from lascar.tools.aes import sbox

if not len(sys.argv) == 2:
    print("Need to specify the location of ASCAD_DIR.")
    print("USAGE: python3 %s ASCAD_DIR" % sys.argv[0])
    exit()

ASCAD_DIR = sys.argv[1]
filename = ASCAD_DIR + "/ASCAD_data/ASCAD_databases/ATMega8515_raw_traces.h5"

container = Hdf5Container(
    filename, leakages_dataset_name="traces", values_dataset_name="metadata"
)
container.number_of_traces = 5000  # only 5000 traces used over the 60000 available


"""
Building of the SnrEngines: 
For each one we specify:
- the name of the SNR 
- the partition function depending on the table at chapter 2.5.2 
- the partition_values (range(256) for all of them, since we look at byte values)
"""
snr_1_engine = SnrEngine(
    "SNR1: unmasked sbox output",
    lambda value: sbox[value["plaintext"][3] ^ value["key"][3]],  # sbox(p[3] ⊕ k[3])
    range(256),
)

snr_2_engine = SnrEngine(
    "SNR2: masked sbox output",
    lambda value: sbox[value["plaintext"][3] ^ value["key"][3]]
    ^ value["masks"][15],  # sbox(p[3] ⊕ k[3]) ⊕ rout
    range(256),
)

snr_3_engine = SnrEngine(
    "SNR3: common output mask out", lambda value: value["masks"][15], range(256)  # rout
)

snr_4_engine = SnrEngine(
    "SNR4: masked sbox output in linear parts",
    lambda value: sbox[value["plaintext"][3] ^ value["key"][3]]
    ^ value["masks"][1],  # sbox(p[3] ⊕ k[3]) ⊕ r[3]
    range(256),
)

snr_5_engine = SnrEngine(
    "SNR5: sbox output mask in linear parts",
    lambda value: value["masks"][1],  # r[3]
    range(256),
)

engines = [snr_1_engine, snr_2_engine, snr_3_engine, snr_4_engine, snr_5_engine]


output = [
    DictOutputMethod(*engines, filename="SNR.pickle"),
    MatPlotLibOutputMethod(*engines, single_plot=True, legend=True),
]

session = Session(
    container, name="SNRs computing", engines=engines, output_method=output
)  # the results are saved in 'SNR.pickle'
session.run(100)
