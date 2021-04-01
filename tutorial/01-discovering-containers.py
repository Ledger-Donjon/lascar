from lascar.container import Trace, TraceBatchContainer
import numpy as np

"""
In lascar, side-channel data are represented within a class: Trace .

A side-channel trace (Trace in lascar), is a couple of two items:
- The first item is "leakage" and represents the side-channel observable
- The second item is "value" and represents the handled values during the observation of "leakage".

The only restriction here is that "leakage" and "data" must be numpy.arrays of any shape.

trace = (leakage, value) where leakage and value are numpy.arrays

The __str__ method of Trace displays the shape and dtype for both leakage and value.

"""


leakage = np.random.rand(
    10
)  # fake side-channel leakage as a vector of 10 time samples: as a np.ndarray
value = np.random.randint(
    0, 256, (16,), dtype=np.uint8
)  # the value associated, as 16 uint8: as a np.ndarray

trace = Trace(leakage, value)  # the corresponding Trace
print("Trace example: ", trace)
print()


"""

Now we introduce the notion of Container:
In lascar, a Container is an object whose main role will be to deliver side-channel data.

Most of the time, side-channel data arises from:
- a measurement device coupled to the DUT (a 'classical' acquisition setup)
- an acquisition campaign already saved on hard drive
- simulation of an algorithm on a device (simulated traces)
- arrays of data
- ...

The idea with Container class is to make abstraction of the origin of the side-channel data, provided that you implement
the correct methods, who will represent your data who will be accessed by lascar during the side-channel analysis.


In lascar, there are different classes inheriting from Container.
 
But the more important is TraceBatchContainer, which actually stores in RAM both the leakages and values as np.arrays (sharing the same first dimension: the number of traces of the Container.

In the following, we build a TraceBatchContainer from two np.arrays: 'leakages' and 'values':
"""

print("TraceBatchContainer example of a batch with 10 traces:")
leakages = np.random.rand(
    10, 100
)  # 10 fake side-channel leakages, each one with 10 time samples: as a np.ndarray
values = np.random.randint(
    0, 256, (10, 16,)
)  # the 10 values associated, each one of as 16 uint8: as a np.ndarray

trace_batch = TraceBatchContainer(leakages, values)  # The corresponding TraceBatch
print("trace_batch =", trace_batch)
print()

"""
Containers implements a getter which will return either a Trace, or a TraceBatchContainer (if several Traces are asked).

A TraceBatchContainer is also iterable.
"""

print("trace_batch[0] =", trace_batch[0])
print("trace_batch[:5] =", trace_batch[:5])
print("trace_batch[range(3)] =", trace_batch[range(3)])
print()

for (
    trace
) in trace_batch:  # a container is iterable (it delivers its traces during iteration)
    print("iteration, trace =", trace)
print()


"""
In lascar, all Containers children implement a logger (from the logging module). 
By default, the loglevel is set to INFO. But it can be set at any time, to display more or less informations: 
(other lascar traces implement a logger: Session, Engine, OutputMethod)
"""
trace_batch.logger.setLevel("DEBUG")
print(trace_batch[::2])
trace_batch.logger.setLevel("INFO")


""" 
In lascar Containers offer different mechanisms to modify the data. 

leakage_section, value_section
leakage_processing, value_processing

leakage_section (resp value_section) is an attribute of the Container that will select the specified samples from the original leakage (resp value).
It is supposed to minimize the reading part, by specifying points of interests for instance.
"""

print("leakage_section:")
trace_batch.leakage_section = [
    10,
    15,
]  # if you want to work only on leakage sample 10 and 15
print(trace_batch)
trace_batch.leakage_section = range(
    10
)  # if you want to work only with the first 10 samples
print(trace_batch)
trace_batch.leakage_section = range(
    0, 100, 10
)  # if you want to work only with one tenth of the sample
print(trace_batch)
trace_batch.leakage_section = None  # cancelling leakage_section
print(trace_batch)
print()


"""
leakage_processing  (resp value_processing) is a Container attribute, under the form of a function that will be applied on the leakage (resp value) after leakage_section (resp value_section)

leakage_processing will be used, among other thing:
- for side-channel trace synchronisation
- for leakage modification: see lascar/tools/processing for a list of existing processing
"""
from lascar.tools.processing import *

print("leakage_processing:")
trace_batch.leakage_processing = (
    lambda leakage: leakage ** 2
)  # any function or callable will be accepted, provided it fits with the original leakage shape
print(trace_batch)
trace_batch.leakage_processing = None  # cancelling leakage_procesing
trace_batch.leakage_processing = CenteredProductProcessing(
    trace_batch, [[0, 1, 2], [3, 4, 5]]
)  # CenteredProduct for high-order side-channel-attacks: recombine samples [0,1,2] with [3,4,5]
print(trace_batch)
trace_batch.leakage_processing = None  # cancelling leakage_procesing
trace_batch.leakage_processing = PcaProcessing(
    trace_batch, 3
)  # Principal component analysis on leakage with 3 components.
print(trace_batch)
print()
trace_batch.leakage_processing = None  # cancelling leakage_procesing
print(trace_batch)
print()
