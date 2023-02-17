Installation
============

*Lascar* can be installed with pip3:

.. code-block:: bash

    pip3 install "git+https://github.com/Ledger-Donjon/lascar.git"

*Lascar* is not available on pypi yet.

Requirements
------------

*Lascar* requires the following packages:

- click
- h5py
- `keras <https://keras.io/>`_ - for machine learning
- `matplotlib <https://matplotlib.org/>`_ - for curve visualization
- `numba <https://numba.pydata.org/>`_ - for python JIT code compilation
- `numpy <https://numpy.org/>`_
- progressbar2
- psuti
- pytest
- PyQt5
- `scikit-learn <https://scikit-learn.org/>`_ - for machine learning
- `scipy <https://scipy.org/>`_
- `tensorflow <https://www.tensorflow.org/>`_ - keras backend
- `vispy <https://vispy.org/>`_ - for curve visualization

Building the documentation
--------------------------

This documentation can be built using `sphinx <https://www.sphinx-doc.org/>`_
from the repository:

.. code-block:: bash

    git clone https://github.com/Ledger-Donjon/lascar.git
    cd lascar/docs/
    make html

