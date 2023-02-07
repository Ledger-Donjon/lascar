Session introduction
====================

This tutorial introduces the :class:`Session <lascar.session.Session>` class and
covers some of its basic functionalities. In *Lascar*, when all traces of a
:class:`Container <lascar.container.container.Container>` need to be walked in
order to make a statistical analysis, a
:class:`Session <lascar.session.Session>` must be used.

:class:`Session <lascar.session.Session>` is the class that will orchestrate:

- the reading of the container traces by batch (to avoid loading all in RAM as much as possible),
- all the statistical computations that are being requested,
- the output of the your analysis (log file, a binary file, a plot, etc.).

In this example, a
:class:`BasicAesSimulationContainer <lascar.container.simulation_container.BasicAesSimulationContainer>`
is set up, with 10000 traces, and noise set to 1. A session is then
instanciated, and the container is given as the argument to indicate to the
session that all processing will be done on the traces of this container. Other
optional arguments can be given to the
:meth:`Session.__init__() <lascar.session.Session()>` method; they will
be presented later.

.. code-block:: python

   from lascar import BasicAesSimulationContainer
   from lascar import Session

   container = BasicAesSimulationContainer(10000, noise=1)
   session = Session(container)

The :class:`Session <lascar.session.Session>` class implements a logger (such as
:class:`Container <lascar.container.container.Container>`), whose level can be
defined by the user:

.. code-block:: python

   session.logger.setLevel("WARN")

The main method for :class:`Session <lascar.session.Session>` class is the
:meth:`run() <lascar.session.Session.run>` method. It will read all the traces
from the container by batches, and run the required processing defined by the
list of registered engines.

The size of batches can be specified as an argument in order to chose the right
balance between speed and RAM consumption.

Engines are classes dedicated to compute stuffs from side-channel traces. The
:class:`Session <lascar.session.Session>` distributes trace batches to all its
engines, for them to process the leakage and data.

Here a list of engines already implemented in lascar:

- :class:`MeanEngine <lascar.engine.engine.MeanEngine>`: computes the mean of
  all the traces leakages,
- :class:`VarEngine <lascar.engine.engine.VarEngine>`: computes the variance of
  all the traces leakages,
- :class:`SnrEngine <lascar.engine.snr_engine.SnrEngine>`: computes
  Signal-to-Noise-Ratio from the traces leakages and a partitioning function
  applied to the values.
- :class:`CpaEngine <lascar.engine.cpa_engine.CpaEngine>`: computes Correlation
  Power Analysis from the traces leakages and a guess function applied to the
  values.
- :class:`TTestEngine <lascar.engine.ttest_engine.TTestEngine>`: computes
  Welch's T-Test from the traces leakages and a partitioning function applied to
  the value

By default, a :class:`Session <lascar.session.Session>` only registers
:class:`MeanEngine <lascar.engine.engine.MeanEngine>` and
:class:`VarEngine <lascar.engine.engine.VarEngine>`.
The man/variance of the leakage is the only thing computed in that very case:

.. code-block:: python

   print(session.engines)
   session.run()

Now that the engines has been fed with all the traces, we can access their
results through their :meth:`finalize() <lascar.engine.engine.Engine.finalize>`
method.

.. code-block:: python

   mean = session.engines["mean"].finalize()
   variance = session["var"].finalize()

   print("mean:", mean)
   print("variance:", variance)

The output will be similar to:

.. code-block:: text

   Session |100%|####|10000 trc/10000 | (2 engines, batch_size=100, leakage_shape=(26,)) |Time:  0:00:00
   mean: [ 4.01378799e+00  3.98403005e+00  3.98297528e+00  3.99657352e+00
     4.00586662e+00  3.97684847e+00  3.95978471e+00  4.02742672e+00
     4.00029943e+00  4.02682018e+00  3.97778740e+00  4.01762718e+00
     4.02589835e+00  3.98203469e+00  4.01265012e+00  4.01654189e+00
     7.60099563e-03 -7.55122327e-03 -6.39382980e-03 -2.05647750e-03
    -1.66105664e-03  2.30399416e-03 -7.95356363e-03  4.03680233e-03
     5.08844511e-03  5.51425513e-03]
   variance: [2.9693785  2.90905657 2.98951995 3.03573351 3.05090195 2.9817484
    3.06420924 2.95840147 2.94878337 3.01056054 3.03315488 2.99825641
    2.98852836 2.9348114  2.99989627 3.00595521 1.02142408 1.02028714
    0.98588882 1.00193212 1.00401774 1.00643998 0.98910787 1.00175479
    1.01897284 1.00315619]
