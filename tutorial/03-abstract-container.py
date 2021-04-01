"""
In this script, we will present the notion of AbstractContainer

AbstractContainer is a Container for which every trace is generated from a function: AbstractContainer.generate_trace(index).

Here is a list of some children implemented in lascar:

- BasicAesSimulationContainer: generate simulated traces of the first round of an AES
- MultipleContainer: Container that will 'concatenate' Containers
- FilteredContainer: Container that will select traces from an initial Container
- RandomizedContainer: Container that will randomize the indices of traces of an initial Container

"""


"""
Part 1: BasicAesSimulationContainer

BasicAesSimulationContainer is an AbstractContainer designed to generate simulated side-channel traces during the first SubBytes function of an AES128.
The first 16 time samples of the leakage represent the noisy Hamming weight at the output of the first SubBytes function.
The other time samples are just noise
For further information about BasicAesSimulationContainer, or AbstractContainer in general, see [...]


If you want to implement your own SimulationContainer, take a look at the code of BasicAesSimulationContainer at lascar/container/simulation_container.py
You'll see that it consists in an AbstractContainer whose generate_trace() method has been overridden.
"""

from lascar.container import BasicAesSimulationContainer

container = BasicAesSimulationContainer(
    50, 1.5
)  # container with 5 traces, noise set to 1.5
print("aes_simulation:", container)
print()

trace = container[0]  # getting the first trace of the container
print(trace)
print()
trace_batch = container[0:3]  # getting the first 3 traces as a TraceBatch
print(trace_batch)
print()


"""
Part 2: MultipleContainer

MultipleContainer is used to concatenate Containers.
(It is particularly useful when you have stored your traces in different files, and you want to merge them for your analysis)

In the following example, we use MultipleContainer to concatenate BasicAesSimulationContainer. 
(it doesnt make much sense, but it applies with any type of Container)

"""
from lascar import MultipleContainer

# First we create a tuple of 4 containers with the same leakage/value shape. The number of traces can be anything:
containers_base = [BasicAesSimulationContainer(10, 1.5) for _ in range(3)]
containers_base += [BasicAesSimulationContainer(20, 2)]

# Then we create the MultipleContainer, by passing containers_base as args:
multiple_container = MultipleContainer(*containers_base)
print("multiple_container:", multiple_container)
print()

# Now we can see that the traces inside multiple_container arise from containers_base, but have not been copied elsewhere:
for i in range(10):
    assert multiple_container[i] == containers_base[0][i]
    assert multiple_container[10 + i] == containers_base[1][i]
    assert multiple_container[20 + i] == containers_base[2][i]

for i in range(20):
    assert multiple_container[30 + i] == containers_base[3][i]


"""
Part 3: FilteredContainer

Used to filter a Container, by selecting only some traces.
Two ways of setting up a FilteredContainer:
- using an iterable (tuple, range,...) to indicate directly which traces to keep/throw
- using a boolean function that will be applied on each trace (downside: each trace will be read with this method)

In the following examples we will use both methods to filter a BasicAesSimulationContainer:
- with a list, taking the traces with index even
- with a function, taking only the traces for which the plaintext_0 is equal to 0

"""

from lascar import FilteredContainer

container = BasicAesSimulationContainer(5000, 1)
print("container_base:", container)
print()

container_filtered_from_list = FilteredContainer(container, range(0, 5000, 2))
print("container_filtered_from_list:", container_filtered_from_list)
print()
for i in range(len(container_filtered_from_list)):
    assert container_filtered_from_list[i] == container[2 * i]


# for the filtering from a function, we create a boolean function taking a Trace as input:
filter_function = lambda trace: trace.value["plaintext"][0] == 0

container_filtered_from_function = FilteredContainer(container, filter_function)
print("container_filtered_from_function:", container_filtered_from_function)
print()

for trace in container_filtered_from_function:
    assert trace.value["plaintext"][0] == 0
