from lascar.container import Trace, TraceBatchContainer
import numpy as np

# In lascar, side-channel data are stored within `Trace` instances. This class
# is a named tuple with two attributes:
#
# - The first item is `leakage` and represents the observable side-channel, such
#   as a power trace.
# - The second item is `value` and represents the handled values during the
#   observation of "leakage".
#
# Both attributes must always be `numpy.ndarray` of any shape.
#
# The `__str__` method of Trace displays the `shape` and `dtype` for both
# leakage and value.
#
# The following creates a trace with (fake) side channel leakage and associated
# data. The leakage is a vector of 10 time samples, stored in a `np.ndarray`.
# The value is an array of 16 bytes, which can represent for instance a key.

leakage = np.random.rand(100)
value = np.random.randint(0, 256, (16,), dtype=np.uint8)
trace = Trace(leakage, value)
print("Trace:", trace)


# Most of time, side-channel analysis requires multiple traces. In Lascar,
# containers are used to group all the traces as a collection. Side-channel data
# can arises from:
#
# - a measurement device coupled to the device under test,
# - an acquisition campaign already saved on hard drive,
# - the simulation of an algorithm on a device,
# - or any other source of leakage information.
#
# The `Container` class provides an interface for accessing the traces (leakage
# and values). A class may implement this interface to adapt to any source of
# leakage and provide the traces when requested by the *Lascar* processing
# pipeline.
#
# Lascar already defines multiple `Container` implementations, and the most
# important is `TraceBatchContainer`, which stores in RAM both the leakages and
# values as `numpy.ndarray`, sharing the same first dimension: the number of
# traces in the container.
#
# In the following, a `TraceBatchContainer` is instanciated from two
# `numpy.ndarray`: `leakages` and `values`.

leakages = np.random.rand(10, 100)  # 10 leakages, 100 time samples each.
values = np.random.randint(0, 256, (10, 16))  # 10 associated values, 16 bytes each.
batch = TraceBatchContainer(leakages, values)
print("Batch container:", batch)


# Containers implement the index operator, which returns either a `Trace` when
# an index is given, or a `TraceBatchContainer` with multiple traces when a
# slice is given. Furthermore, containers are iterable.

print("batch[0]:", batch[0])
print("batch[:5]:", batch[:5])
print("batch[range(3)]:", batch[range(3)])

for trace in batch:
    print("Batch iteration:", trace)

print()


# Containers offer different mechanisms to limit the data to subsets.
# `leakage_section` (resp. `value_section`) is a `Container` attribute
# that will select the specified samples from the original leakage
# (resp. `value`). It is supposed to minimize the reading part, by specifying
# points of interests for instance.

print("Leakage section example:")
# To work only on leakage sample 10 and 15:
batch.leakage_section = [10, 15]
print(batch)

# To work only with the first 10 samples:
batch.leakage_section = range(10)
print(batch)

# To work with only with one tenth of the sample:
batch.leakage_section = range(0, 100, 10)
print(batch)

# To cancel `leakage_section`:
batch.leakage_section = None  # cancelling leakage_section
print(batch)
print()


# `leakage_processing` (resp. `value_processing`) is a `Container` attribute,
# which can be a function that will be applied on the leakage (resp. value)
# after `leakage_section` (resp. value_section).
#
# Leakage processing can be used for instance for side-channel trace
# resynchronisation, signal filtering, etc.
#
# See lascar/tools/processing for a list of existing processing.

from lascar.tools.processing import *

print("Leakage processing example:")
# Any function or callable is accepted, provided it fits with the original
# leakage shape.
batch.leakage_processing = lambda leakage: leakage**2
print(batch)

# Centered product for high-order side-channel attacks: recombine samples
# [0, 1, 2] with [3, 4, 5]
batch.leakage_processing = CenteredProductProcessing(batch, [[0, 1, 2], [3, 4, 5]])
print(batch)

# Principal component analysis on leakage with 3 components
batch.leakage_processing = PcaProcessing(batch, 3)
print(batch)

# No leakage processing
batch.leakage_processing = None
print()

# All container children implement a logger (from the logging module).
# By default, the loglevel is set to `INFO`, but it can be set at any time to
# display more or less informations.
# Note: other lascar classes implement a logger as well: Session, Engine,
# OutputMethod.

batch.logger.setLevel("DEBUG")
print(batch[::2])
batch.logger.setLevel("INFO")
