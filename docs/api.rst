Lascar API Reference
====================

.. toctree::
   :hidden:

   Session <api_session.rst>
   Containers <api_containers.rst>
   Engines <api_engines.rst>
   Output <api_output.rst>
   Plotting <api_plotting.rst>
   Tools <api_tools.rst>

:doc:`api_session` is the main class which leads side-channel operations in lascar. One all side-channel settings are defined (containers, engines, display), the session will perform the analysis, show progress and display the results.

:doc:`api_containers` provide traces and leakages information for a side-channel analysis. It can, for instance, yield traces stored on disk, generate simulated traces on the fly, aggregate data from multiple sources, etc.

:doc:`api_engines` proposes many side-channel analysis techniques, fed by traces from :doc:`api_containers` and run by a :doc:`api_session`.

:doc:`api_output` module is used to define which result should be presented, and how they should be displayed or exported.

:doc:`api_plotting`

:doc:`api_tools`
