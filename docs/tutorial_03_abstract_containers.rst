Abstract containers
===================

:class:`AbstractContainer <lascar.container.container.AbstractContainer>` is a
:class:`Container <lascar.container.container.Container>` for which every trace
is generated from the function
:meth:`AbstractContainer.generate_trace(index) <lascar.container.container.AbstractContainer.generate_trace>`.

*Lascar* proposes some implementations of
:class:`AbstractContainer <lascar.container.container.AbstractContainer>`:

- :class:`BasicAesSimulationContainer <lascar.container.simulation_container.BasicAesSimulationContainer>`:
  generates simulated traces of the first round of an AES,
- :class:`MultipleContainer <lascar.container.multiple_container.MultipleContainer>`:
  container that will 'concatenate' containers,
- :class:`FilteredContainer <lascar.container.filtered_container.FilteredContainer>`:
  selects traces from an initial container,
- :class:`RandomizedContainer <lascar.container.filtered_container.RandomizedContainer>`:
  randomizes the indices of traces of an initial container

If you want to implement your own simulation container take a look at the code
of
:class:`BasicAesSimulationContainer <lascar.container.simulation_container.BasicAesSimulationContainer>`
at
`simulation_container.py <https://github.com/Ledger-Donjon/lascar/blob/master/lascar/container/simulation_container.py#L31>`_.
You'll see that it consists in an AbstractContainer whose
:meth:`generate_trace <lascar.container.container.AbstractContainer.generate_trace>`
method has been overridden.

AES simulation container
------------------------

:class:`BasicAesSimulationContainer <lascar.container.simulation_container.BasicAesSimulationContainer>`
is an :class:`AbstractContainer <lascar.container.container.AbstractContainer>`
designed to generate simulated side-channel traces during the first `SubBytes`
function of an AES-128.

The first 16 time samples of the leakage represent the noisy
`Hamming weight <https://en.wikipedia.org/wiki/Hamming_weight>`_ at the output
of the first `SubBytes` function. The other time samples are just noise.

.. code-block:: python

   from lascar.container import BasicAesSimulationContainer

   # Container with 5 traces, noise set to 1.5.
   container = BasicAesSimulationContainer(50, 1.5)
   trace = container[0]  # Get the first trace of the container
   print(trace)
   trace_batch = container[0:3]  # Get the first 3 traces as a TraceBatch
   print(trace_batch)

Containers concatenation
------------------------

:class:`MultipleContainer <lascar.container.multiple_container.MultipleContainer>`
is used to concatenate containers. It is particularly useful when you have
stored your traces in different files, and you want to merge them for your
analysis.

In the following example, we use
:class:`MultipleContainer <lascar.container.multiple_container.MultipleContainer>`
to concatenate a few
:class:`BasicAesSimulationContainer <lascar.container.simulation_container.BasicAesSimulationContainer>`.

.. code-block:: python

   from lascar import MultipleContainer

   # First we create a tuple of 4 containers with the same leakage/value shape.
   # The number of traces can be anything.
   containers = [BasicAesSimulationContainer(10, 1.5) for _ in range(3)]
   containers += [BasicAesSimulationContainer(20, 2)]
   # Then we create the `MultipleContainer`, by passing containers as args:
   multiple = MultipleContainer(*containers)
   print(multiple)

Now we can see that the traces inside :code:`multiple` arise from
:code:`containers`, but have not been copied elsewhere:

.. code-block:: python

   for i in range(10):
       assert multiple[i] == containers[0][i]
       assert multiple[10 + i] == containers[1][i]
       assert multiple[20 + i] == containers[2][i]

   for i in range(20):
       assert multiple[30 + i] == containers[3][i]

Containers filtering
--------------------

:class:`FilteredContainer <lascar.container.filtered_container.FilteredContainer>`
is used to filter a container, by selecting a subset of the traces.

There are two ways of setting up a
:class:`FilteredContainer <lascar.container.filtered_container.FilteredContainer>`:

- using an iterable (tuple, range,...) to indicate directly which traces to
  keep or discard,
- using a boolean predicate function that will be applied on each trace
  (downside: each trace will be read with this method)

In the following examples we will use both methods to filter a
:class:`BasicAesSimulationContainer <lascar.container.simulation_container.BasicAesSimulationContainer>`:

- with a list, taking the traces with index even,
- with a function, taking only the traces for which the plaintext_0 is equal
  to 0

.. code-block:: python

   from lascar import FilteredContainer

   container = BasicAesSimulationContainer(5000, 1)
   filtered_from_list = FilteredContainer(container, range(0, 5000, 2))
   print(filtered_from_list)
   for i in range(len(filtered_from_list)):
       assert filtered_from_list[i] == container[2 * i]

   # For the filtering with predicate, we create a boolean function taking a
   # `Trace` as input:
   predicate = lambda trace: trace.value["plaintext"][0] == 0
   filtered_from_function = FilteredContainer(container, predicate)
   print(filtered_from_function)

   for trace in filtered_from_function:
       assert trace.value["plaintext"][0] == 0
