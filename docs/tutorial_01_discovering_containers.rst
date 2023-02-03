Discovering containers
======================

This tutorial will introduce traces and containers, which are base classes used
to store the experimental measurement in *Lascar*.

The complete source of this tutorial is available at
`01-discovering-containers.py <https://github.com/Ledger-Donjon/lascar/blob/master/tutorial/01-discovering-containers.py>`_.

Trace
-----

In *Lascar*, side-channel data are stored within
:class:`Trace <lascar.container.container.Trace>` instances. This class is a
named tuple with two attributes:

- The first item is :code:`leakage` and represents the observable side-channel, such
  as a power trace.
- The second item is :code:`value` and represents the handled values during the
  observation of the leakage.

Both attributes must always be `numpy.ndarray` of any shape.

The :code:`__str__` method of :class:`Trace <lascar.container.container.Trace>`
displays the :code:`shape` and :code:`dtype` for both leakage and value.

The following creates a trace with (fake) side channel leakage and associated
data. The leakage is a vector of 10 time samples, stored in a :class:`numpy.ndarray`.
The value is an array of 16 bytes, which can represent for instance a key.

.. code-block:: python

   from lascar.container import Trace
   import numpy as np

   leakage = np.random.rand(100)
   value = np.random.randint(0, 256, (16,), dtype=np.uint8)
   trace = Trace(leakage, value)
   print("Trace:", trace)

This will output:

.. code-block:: text

   Trace: Trace with leakage:[(100,), float64] value:[(16,), uint8]

Container
---------

Most of time, side-channel analysis requires multiple traces. In *Lascar*,
containers are used to group all the traces as a collection. Side-channel data
can arises from:

- a measurement device coupled to the device under test,
- an acquisition campaign already saved on hard drive,
- the simulation of an algorithm on a device,
- or any other source of leakage information.

The :class:`Container <lascar.container.container.Container>` class provides an
interface for accessing the traces (leakage and values). A class may implement
this interface to adapt to any source of leakage and provide the traces when
requested by the *Lascar* processing pipeline.

*Lascar* already defines multiple
:class:`Container <lascar.container.container.Container>` implementations, and
the most important is
:class:`TraceBatchContainer <lascar.container.container.TraceBatchContainer>`,
which stores in RAM both the leakages and values as :class:`numpy.ndarray`,
sharing the same first dimension: the number of traces in the container.

In the following, a
:class:`TraceBatchContainer <lascar.container.container.TraceBatchContainer>` is
instanciated from two :class:`numpy.ndarray`: :code:`leakages` and :code:`values`:

.. code-block:: python

   leakages = np.random.rand(10, 100)  # 10 leakages, 100 time samples each.
   values = np.random.randint(0, 256, (10, 16))  # 10 associated values, 16 bytes each.
   batch = TraceBatchContainer(leakages, values)
   print("Batch:", batch)

This will output:

.. code-block:: text

   Batch container: Container with 10 traces. leakages: [(100,), float64], values: [(16,), int64].

Indexing and iteration
----------------------

Containers implement the index operator, which returns either a
:class:`Trace <lascar.container.container.Trace>` when an index is given, or a
:class:`TraceBatchContainer <lascar.container.container.TraceBatchContainer>`
with multiple traces when a slice is given. Furthermore, containers are
iterable.

.. code-block:: python

   print("batch[0]:", batch[0])
   print("batch[:5]:", batch[:5])
   print("batch[range(3)]:", batch[range(3)])

   for trace in batch:
       print("Batch iteration:", trace)

This will output:

.. code-block:: text

   batch[0]: Trace with leakage:[(100,), float64] value:[(16,), int64]
   batch[:5]: Container with 5 traces. leakages: [(100,), float64], values: [(16,), int64]. 
   batch[range(3)]: Container with 3 traces. leakages: [(100,), float64], values: [(16,), int64]. 
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]
   Batch iteration: Trace with leakage:[(100,), float64] value:[(16,), int64]

Data subsets
------------

Containers offer different mechanisms to limit the data to subsets.
:attr:`leakage_section <lascar.container.container.Container.leakage_section>`
(resp.
:attr:`value_section <lascar.container.container.Container.value_section>`) is a
:class:`Container <lascar.container.container.Container>` attribute that will
select the specified samples from the original leakage (resp. value). It is
supposed to minimize the reading part, by specifying points of interests for
instance.

.. code-block:: python

   # To work only on leakage sample 10 and 15:
   batch.leakage_section = [10, 15]
   print(batch)
   
   # To work only with the first 10 samples:
   batch.leakage_section = range(10)
   print(trace_batch)
   
   # To work with only with one tenth of the sample:
   batch.leakage_section = range(0, 100, 10)
   print(trace_batch)
   
   # To cancel `leakage_section`:
   batch.leakage_section = None  # cancelling leakage_section
   print(trace_batch)

This will output:

.. code-block:: text

   Container with 10 traces. leakages: [(2,), float64], values: [(16,), int64]. leakage_section set to [10, 15]. 
   Container with 10 traces. leakages: [(10,), float64], values: [(16,), int64]. leakage_section set to range(0, 10). 
   Container with 10 traces. leakages: [(10,), float64], values: [(16,), int64]. leakage_section set to range(0, 100, 10). 
   Container with 10 traces. leakages: [(100,), float64], values: [(16,), int64]. 


Data processing
---------------

:attr:`leakage_processing <lascar.container.container.Container.leakage_processing>`
(resp. :attr:`value_processing <lascar.container.container.Container.value_processing>`)
is a `Container` attribute which can be a function that will be applied on the
leakage (resp. value) after
:attr:`leakage_section <lascar.container.container.Container>` (resp. value_section).
Leakage processing can be used for instance for side-channel trace
resynchronisation, signal filtering, etc.
See :code:`lascar/tools/processing` for a list of existing processing.

.. code-block:: python

   from lascar.tools.processing import *

   # Any function or callable is accepted, provided it fits with the original
   # leakage shape.
   batch.leakage_processing = lambda leakage: leakage**2

   # Centered product for high-order side-channel attacks: recombine samples
   # [0, 1, 2] with [3, 4, 5]
   batch.leakage_processing = CenteredProductProcessing(
       batch, [[0, 1, 2], [3, 4, 5]]
   )

   # Principal component analysis on leakage with 3 components
   batch.leakage_processing = PcaProcessing(trace_batch, 3)

   # No leakage processing
   batch.leakage_processing = None


Logging
-------

All container children implement a logger (from the logging module). By default,
the loglevel is set to `INFO`, but it can be set at any time to display more or
less informations.

.. code-block:: python

   batch.logger.setLevel("DEBUG")
   print(batch[::2])
   batch.logger.setLevel("INFO")

This will output:

.. code-block:: text

   2023-02-02 11:05:10,032 - lascar.container.container - DEBUG - __getitem__ with key slice(None, None, 2) <class 'slice'>
   2023-02-02 11:05:10,032 - lascar.container.container - DEBUG - Setting leakage_section to None
   2023-02-02 11:05:10,032 - lascar.container.container - DEBUG - Setting value_section to None
   2023-02-02 11:05:10,032 - lascar.container.container - DEBUG - Setting leakage_processing to None
   2023-02-02 11:05:10,032 - lascar.container.container - DEBUG - Setting value_processing to None
   Container with 5 traces. leakages: [(100,), float64], values: [(16,), int64].

.. note::

   Note: other lascar classes implement a logger as well:
   :class:`Session <lascar.session.Session>`,
   :class:`Engine <lascar.engine.engine.Engine>`,
   :class:`OutputMethod <lascar.output.output_method.OutputMethod>`.

