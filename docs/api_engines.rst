Engines
=======

.. note::

   Since lascar 2.0, pickle is no longer used: loading a pickle file can execute arbitrary code.
   Classifiers are saved to ``.keras`` files (Keras, loaded with ``safe_mode=True``) or ``.skops``
   files (scikit-learn). Types not trusted by default must be passed in the ``trusted`` argument of
   ``load_classifier`` or ``Processing.load``. Old ``.save`` and ``.pickle`` files can no longer be loaded.

.. automodule:: lascar.engine.engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.chi2test_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.classifier_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.cpa_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.dom_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.dpa_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.guess_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.lra_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.nicv_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.partitioner_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.snr_engine
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: lascar.engine.ttest_engine
    :members:
    :undoc-members:
    :show-inheritance:
