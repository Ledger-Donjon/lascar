Store containers
================

When performing side-channel analysis, a user will seek to store its data for
further usages. To our knowledge, every lab has its own format for storing
side-channel traces.

The probably most popular traces storage file format is
`hdf5 (Hierarchical Data Format) <https://www.hdfgroup.org/HDF5/>`_. For each
set of traces, a single hdf5 file is created, implementing two datasets: the
first one for leakages, and the second for values.

*Lascar* provides the class
:class:`Hdf5Container <lascar.container.hdf5_container.Hdf5Container>` which
allows handling this format transparently. This enables working on traces
without having to load them all in memory (as a
:class:`TraceBatchContainer <lascar.container.container.TraceBatchContainer>`
would do).

The 
:meth:`Hdf5Container.export <lascar.container.hdf5_container.Hdf5Container.export>`
method can be used to convert any container into a
:class:`Hdf5Container <lascar.container.hdf5_container.Hdf5Container>` (i.e. by
creating a file containing all its traces). In the following example, a
:class:`TraceBatchContainer <lascar.container.container.TraceBatchContainer>`
is created, and converted into a
:class:`Hdf5Container <lascar.container.hdf5_container.Hdf5Container>`.

.. code-block:: python

   from lascar import TraceBatchContainer, Hdf5Container
   import numpy as np

   leakages = np.random.rand(10, 100)  # 10 leakages, 100 time samples each.
   values = np.random.randint(0, 256, (10, 16))  # 10 associated values, 16 bytes each.
   batch = TraceBatchContainer(leakages, values)
   hdf5 = Hdf5Container.export(batch, "tmp.h5")

Since :class:`Hdf5Container <lascar.container.hdf5_container.Hdf5Container>` is
a :class:`Container <lascar.container.container.Container>`, it implements all
the features seen before. This can be verified as follows:

.. code-block:: python

   for (a, b) in zip(batch, hdf5, strict=True)
       assert a == b

