"""
When performing side-channel Analysis, an user will seek to store its data for further usages.
To our knowledge, every lab has its own format for storing side channel traces.

We, at Ledger, store our traces using hdf5 file format (Hierarchical Data Format: https://www.hdfgroup.org/HDF5/)
For each set of traces, a single hdf5 file is created, implementing 2 datasets: one for leakages, one for values.

We provide within lascar the class Hdf5Container, allowing to transparently handle this format.
This class allows to handle traces without having to load them all in your memory (as a TraceBatchContainer would do)

Hdf5Container implements an export() method, used to convert ANY Container into a Hdf5Container (ie by creating a file containing all its traces)

In the following example, we create a TraceBatchContainer, and convert it into a Hdf5Container.
This feature will be used in other tutorial parts, with other Container than TraceBatchContainer)

If you want to use your own trace format with lascar, you would just have to implement a specific Container class.

"""
from lascar import TraceBatchContainer, Hdf5Container
import numpy as np
leakages = np.random.rand(10, 100)  # 10 fake side-channel leakages, each one with 10 time samples: as a np.ndarray
values = np.random.randint(0, 256, (10, 16,))  # the 10 values associated, each one of as 16 uint8: as a np.ndarray

trace_batch_container = TraceBatchContainer(leakages, values)


"""
The export() method of Hdf5Container takes at least as an input a Container, and a filename (the hdf5 resulting file)
For more options, please take a look at help(Hdf5Container.export)
"""
hdf5_container = Hdf5Container.export(trace_batch_container, "tmp.h5")


"""
Since Hdf5Container is a Container, it implements all the features seen before.
We can check that the traces returned by both trace_batch_container and hdf5_container are the same:
"""
for i in range( len(trace_batch_container)):
    assert trace_batch_container[i] == hdf5_container[i]

