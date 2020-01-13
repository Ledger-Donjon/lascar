# lascarctl: lascar command-line tool


*lascarctl* is a command-line tool used to implement repetitive actions that are needed when doing side-channel analysis.

```
spo@zen:~$ lascarctl --help
Usage: lascarctl [OPTIONS] COMMAND [ARGS]...

  lascarctl.

  lascar scripting commands.

Options:
  --help  Show this message and exit.

Commands:
  acquisition  Acquire side-channel data.
  info         Get information on an Hdf5Container
  processing   Process (modify) a container, and output to a new one.
  run          Run a lascar session on a container.
  ttest        Compute Welch-ttest on containers.

```

For now, only a few commands are available and will be described in this document.

Please note that for the moment, *lascarctl* commands works with `Hdf5Container`

## `lascarctl acquisition` command

With this command, you can easily setup your acquisitions.

For the purpose of the command explanation, let's say we have an oscilloscope connected to a smartcard reader on which we launch some crypto for side-channel evaluation.

With the `lascarctl acquisition` command, you can set up your aquisition toolchain. For that, you'll need to implement a *leakage getter* and a *value getter*

Nevermind what type of source it is, a *getter* is a python class such that:
- the class implements a get() method,
- the get() method does not need argument (except the self),
- the get() method returns a np.array

Now, for our example, imagine the python module `acquisition_smartcard.py`:

```
class MyOscilloscope:
    def __init__(self, foo):
        self.scope = foo
        ...
    def get(self):
        return self.scope.get_trace(channel=1)
    
class MySmartReader: 
    def __init__(self, bar):
        self.smartcard = bar
        ...
    def get(self):
        plaintext = np.random.randint(0,256,16)
        self.smartcard.encrypt(plaintext)
        return plaintext
```
where you implement the correct getters class/methods to communicate with both the smartcard and the oscilloscope.

Then the command:

```
lascarctl acquisition --value_getter acquisition_smartcard.py MySmartReader --leakage_getter acquisition_smartcard.py MyOscilloscope --number_of_traces 1000 --output filename.h5
```
will process to an acquisition of 1000 traces throught the oscilloscope/smartreader into a hdf5 file.


## `lascarctl info` command

The `lascarctl info` provides information on an `Hdf5Container`.
For instance:

```
spo@zen:~$ lascarctl info foo.h5 
Container with 10 traces. leakages: [(26,), float64], values: [(), [('plaintext', 'u1', (16,)), ('key', 'u1', (16,))]]. 
```
The displayed info is:
- number of traces: 10
- leakage shape/dtype: each leakage has 26 float64
- value shape/dtype: each value is a singleton of a [special numpy datatype](https://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html). Each value is composed of 16 bytes under `plaintext` field, and of 16 bytes under `key` field


## `lascarctl processing` command

The `lascarctl processing` command is used to modify the traces from a `Hdf5Container`, and to store them into a new `Hdf5Container`.

This command is used when you want to reshape, chunk and most of all resynchronize your side-channel traces.

```
spo@zen:~$ lascarctl processing --help
Usage: lascarctl processing [OPTIONS] [NAME_IN]...

  Process (modify) a container, and output to a new one. (ie apply a
  function on leakages and/or values of the container)

  - names_in : names of the container you want to process

Options:
  -o, --name_out TEXT             indicate the name for the output file (hdf5
                                  for now).
  -l, --leakage_processing TEXT...
                                  indicate leakage_processing module_name and
                                  object_name
  -v, --value_processing TEXT...  indicate value_processing module_name and
                                  object_name
  -b, --batch_size INTEGER        set the batch_size for lascar session
  -p, --plot                      boolean to plot traces while acquisition
  -n, --number_of_traces INTEGER  indicate the number of traces you wish to
                                  process
  --help  
  ```

  The user must indicate a filename for the input `Hdf5Container`.
  If he/she wants to modify the leakages and/or the values, the user can implement a python function inside a module and use this an an argument of `--leakage_processing` and/or `--value_processing`.

  For instance, imagine that we want to take the traces from an existing `Hdf5Container` (say `foo.h5`), and modify them such that we will square all the leakages.
  
  We first write a `bar.py` file such this one:

  ```
  def square(leakage):
    return leakage**2
  ```

Then we can use the command:

```
lascarctl processing foo.h5 -l bar.py square -o bar.h5
```
At the end, we get a new `Hdf5Container` `bar.h5` such that all the leakages from `bar.h5` are the square of the leakages from `foo.h5`

Of course this is a very simple example.
But imagine a much more sophisticated synchronization function. It could be use in the very same manner to apply a synchronization to a large set of traces.

A few words about the `-p --plot` option. It can be used to plot the processed leakages.
You can then use it to check that your processing is consistant (for debug/test purpose)

For intance:
```
lascarctl processing foo.h5 -p -n 3
```
will plot the first 3 leakages from `foo.h5`.

But more interesting:
```
lascarctl processing foo.h5 -l bar.py square -p -n 3
```
will takes the 3 first leakages from `foo.h5`, apply the `square` function defined, and plot the resulting leakages on the screen, without saving anything.


## `lascarctl run` command

The `run` command is used when you want to launch a lascar `Session` with engines/output_method that you indicate through the command line.

```
Usage: lascarctl run [OPTIONS] [NAME_IN]... MODULE

  Run a lascar session on a container.

  Must specify: 
  - name_in : the name of the container file (hdf5 for now) -
  - module : path to a python module containing engines/output_method
  definition

Options:
  -e, --engines TEXT              specify engines name within module
  -o, --output_method TEXT        specify output_method name within module
  -b, --batch_size INTEGER        set the batch_size for lascar session
  -n, --number_of_traces INTEGER  indicate the number of traces you wish to
                                  use
  --help                          Show this message and exit.
```

For instance, if I want to compute two simple SNRs on side-channel traces stored inside a `foo.h5` `Hdf5Container`.
I have to create a python module, say `bar.py`, that defines:
- `engines`: what will be the engines to be computed by the `Session`
- `output_method`: how the `Session` will output the results of the `engines`


```
from lascar import *

engines = [  #define all your engines here:
    SnrEngine("snr byte 8", lambda value:value["plaintext"][8], range(256)),
    SnrEngine("snr byte 12", lambda value:value["plaintext"][12], range(256))
    ]

output_method = MatPlotLibOutputMethod(*engines) # define your output_method here
```

Now the command 
```
lascarctl run foo.h5 bar.py
```
will perform the defined SNRs on the traces from `foo.h5`, and use matplotlib to display the results.


## `lascarctl ttest` command

The `ttest` command is used  to compute Welsh's t-test using pre-sorted sets (plural) of side-channel traces.

```
spo@zen:~$ lascarctl ttest --help
Usage: lascarctl ttest [OPTIONS] [NAMES_IN]...

  Compute Welch-ttest on containers.

  Each set of trace represent a different class for the ttest. (no
  partitioning done)

  For each pair of set of trace, a ttest is computed.

Options:
  -b, --batch_size INTEGER  set the batch_size for lascar session
  -o, --name_out TEXT       npy.save the ttests to name_out
  -p, --plot                plot the computed ttests with matplotlib
  --help                    Show this message and exit.
```

When using Welsh's t-test on side-channel traces, we define a criterion dividing the traces between 2 batches.
For instance:
- fixed_plaintext versus random_plaintext
- fixed_plaintext versus fixed2_plaintext
- ...

Now, if during your acquisition you have several set of traces, such that, for instance:
- `fixed_plaintext.h5` is a `Hdf5Container` with traces such that the plaintext is fixed
- `random_plaintext.h5` is a `Hdf5Container` with traces such that the plaintext is random
- `fixed2_plaintext.h5` is a `Hdf5Container` with traces such that the plaintext is fixed to a different value than `fixed_plaintext.h5`

Then you can use the `lascarctl ttest` command to compute the Welsh's ttest of all the couples described berfore:
- fixed_plaintext versus random_plaintext
- fixed2_plaintext versus random_plaintext
- fixed_plaintext versus fixed2_plaintext

The command:
```
lascarctl ttest fixed_plaintext.h5 random_plaintext.h5 fixed2_plaintext.h5 -o result_ttest.save 
```
will compute the 3 ttests, and output them into a npy file.
The `--plot` option will also use matplotlib to display the 3 ttest curves.