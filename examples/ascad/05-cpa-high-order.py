"""
In this script, is shown how to perform secon-order Cpa on the traces of ATMega8515_raw_traces.h5

From the SNRs obtained in 02-snr.py,
We can extract the Points of Interest and recombine them with a CenteredProduct.
After that, we apply a classical CPA (Correlation) to the modified traces.

Only 500 traces are used.

At the end of the script, the score of each hypothesis is plotted with trace increments of 10

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

# poi = Points Of Interest.
# We use the SNRs computed before to extract time samples where both mask and masked sensitive variable are used.
snrs = DictOutputMethod.load(
    "SNR.pickle"
)  # we load the snr results computed at 02-snr.py
poi = []
poi += [snrs["SNR4: masked sbox output in linear parts"][5000].argmax()]
poi += [snrs["SNR5: sbox output mask in linear parts"][5000].argmax()]


# Container creation: we take the same file, but set the leakage_section to the computed poi.
container = Hdf5Container(
    filename,
    leakages_dataset_name="traces",
    values_dataset_name="metadata",
    leakage_section=poi,
)

container = container.limited(500)

# Then we make a container that will apply a CenteredProduct to recombine all the points of interest.
container.leakage_processing = CenteredProductProcessing(container)


# Now a classical CPA, targetting the output of the 3rd Sbox:
cpa_engine = CpaEngine(
    lambda value, guess: hamming(sbox[value["plaintext"][3] ^ guess]),
    range(256),
    solution=container[0].value["key"][3],
    name="cpa-high-order",
    jit=False,
)


session = Session(
    container,
    engine=cpa_engine,
    output_method=ScoreProgressionOutputMethod(cpa_engine),
    output_steps=10,
)  # the steps at which the results will be computed

session.run(1000)
