"""

Now that we are familiar with lascar Container class, it is time to introduce the Session class.

In lascar, every time you want to browse all traces from a Container to make à statistical analysis, you have to use a Session.

Session is the class that will orchestrate (among other things:
- the reading of the Container traces by batch (to avoid loading all in RAM as much as possible)
- all the statisctical computations that you would like to process on them.
- the output that you seek from your analysis (do you want a log file, a binary file, a plot ?)

In this script we will look at the basic functionalities of the Session class.

(For the rest of the tutorial, we will use a BasicAesSimulationContainer as trace Container)

"""

# First we need a Conainer, let's use BasicAesSimulationContainer. Say with 10000 traces, and the noise set to 1.
from lascar import BasicAesSimulationContainer

container = BasicAesSimulationContainer(10000, noise=1)


"""
The only required argument for a Session is the Container it works on.
(Other optional keywords argument will be presented later)
"""
from lascar import Session

session = Session(container)


# Session class implement a logger (like Container), whose level can be set by user:
session.logger.setLevel("WARN")


"""
The main method for Session class is the run() method. It consists in reading traces from the Container by batches.
The size of batches can be specified as an argument. 
Once the run() method is called, all traces are read and processed by the Engines registered by the Session.

Engines are classes dedicated to compute stuffs from side-channel traces. The Session distributes traces batches to all its Engines, for them to do their jobs.
Here a list of Engines already implemented in lascar:
- MeanEngine: compute the mean of all the traces leakages
- VarEngine: compute the varianc of all the traces leakages
- SnrEngine: compute Signal-to-Noise-Ratio from the traces leakages and a partitioning function appllied to the values.
- CpaEngine: compute Correlation Power Analysis from the traces leakages and a guess function appllied to the values.
- TTestEngine: compute Welch's T-Test from the traces leakages and a partitioning function appllied to the value
- ...


By default, a Session only registers MeanEngine and VarEngine.
The Mean/Variance of the leakage is the only thing computed in that very case:
"""

print(
    session.engines
)  # engines is a dict of all the engines registered by the Session, with key equal to the name given

session.run()


# Now that the engines has been fed with all the traces, we can access their results through their finalize() method:
mean = session.engines["mean"].finalize()
mean = session.engines["mean"].finalize()  # shortcut

variance = session["var"].finalize()

print("mean=", mean)
print("variance=", variance)
