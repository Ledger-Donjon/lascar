
[![Ledger Logo](images/logo_ledger)](https://www.ledger.com/)&emsp;[![Ledger Logo](images/logo_donjon_l)](https://www.ledger.fr/tag/donjon/)

[![Gitter](https://badges.gitter.im/lascar-dev/community.svg)](https://gitter.im/lascar-dev/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![Documentation Status](https://readthedocs.org/projects/lascar/badge/?version=latest)](https://lascar.readthedocs.io/en/latest/?badge=latest) [![Join the chat at https://gitter.im/Ledger-Donjon/lascar](https://badges.gitter.im/Ledger-Donjon/lascar.svg)](https://gitter.im/Ledger-Donjon/lascar?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# LASCAR

**L**edger's **A**dvanced **S**ide **C**hannel **A**nalysis **R**epository

A fast, versatile, and open source python3 library designed to facilitate Side-Channel Analysis.

*lascar* is intended to be used by seasoned side-channel attackers as well as laymen who would like to get a feel of side-channel analysis.

From side-channel acquisitions to results management, passing by signal synchronisation, custom attacks, *lascar* provides classes/functions to solve most of the obstacles an attacker would face, when needed to perform sound, state-of-the-art side-channel analysis.

This project has been developed in parallel of the activities done by Ledger Donjon (Ledger's security team), to fully match our needs regarding side-channel evaluation.


## Main features

The philosophy behind *lascar* is to simplify for the end user the process of a side-channel analysis.
It provides many classes and functions that you can accomodate with, or inherit from to do the job you need.

- **Openness**: *lascar* library is open source and is intended to facilitate attack implementations, and exchange between users. Contributing to *lascar* is **strongly encouraged.**
- **Simplicity**: For **basic** state of the art attacks, the corresponding *lascar* script shall stay **basic**
- **Compatibility**: Since *lascar* relies on mainstream python libraries (numpy, sklearn, keras): *lascar* is easily deployable
- **Flexibility**: Implement your own classes (for your already existing trace format, your specific attacks, the way you want your output to be...), use different languages (provided that you bind them with python),...

Please note that performance has not yet been challenged.

The [tutorial](tutorial/)/[examples](examples/) folders of the library provide basic scripts solving the most frequent use-cases of side-channel analysis.


## Installation

Clone the repository then use the setup.py file, based on setuptools:

```
python3 setup.py install --user
```

Build the doc:

```
cd docs/
make html
```

## Requirements

This library requires the following packages:

- numpy
- scipy
- matplotlib: for curve visualization
- vispy: for curve visualization
- sklearn: for machine learning
- keras: for deep learning
- tensorflow: keras backend
- h5py: for data storage
- progressbar2
- pytest
- numba

## Tutorial

The [tutorial](tutorial/) folder contains commented scripts to understand how to handle the core classes behind *lascar* (Container, Session, Engine, OutputMethod)

- [01-discovering-containers.py](tutorial/01-discovering-containers.py)
- [02-store_containers.py](tutorial/02-store_containers.py)
- [03-abstract-container.py](tutorial/03-abstract-container.py)
- [04-acquisition-setup-example.py](tutorial/04-acquisition-setup-example.py)
- [05-synchronization-example.py](tutorial/05-synchronization-example.py)
- [06-session-introduction.py](tutorial/06-session-introduction.py)
- [07-session-dpa-example.py](tutorial/07-session-dpa-example.py)
- [08-session-manage-outputs.py](tutorial/08-session-manage-outputs.py)


## Examples

See [examples.md](examples/examples.md)


## ![Ledger Donjon Logo](images/logo_donjon) About Ledger Donjon ![Ledger Donjon Logo](images/logo_donjon)
Created in 2018, Ledger Donjon (Ledger security team) regroups experts in security with a wide range of expertise (such as software, perturbation and side-channel attacks, secured development, reverse engineering, ...). Based in Paris, Ledger's Donjon tends to shift the paradigm of security through obscurity. Take a look at our [blogposts](https://www.ledger.fr/category/security/) and the [detailed introduction](https://www.ledger.fr/2018/11/12/introducing-ledger-donjon/)!



## Acknowledgerments

Ledger's Donjon would like to thank the people behind [ASCAD](https://github.com/ANSSI-FR/ASCAD), for making available real side-channel traces and scripts for analysis.
Their traces have been used in examples/ascad/ folder to illustrate how to use *lascar* to reproduce (part of) their study.
