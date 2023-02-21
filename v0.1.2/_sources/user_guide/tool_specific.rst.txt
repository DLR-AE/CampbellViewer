.. _sec_ug_tool_specific:

Tool specific information
=========================

Bladed
------

The Bladed interface intensively uses the pyBladed package. This package contains functionalities to read Bladed result
binaries: https://github.com/DLR-AE/pyBladed. This works well for the 'standard' Campbell diagram data, i.e. the
frequency and damping curves. However, the more detailed Campbell diagram data (participation factors) is not saved in
the standard Bladed convention. This data has to be parsed from text files. This parsing works well for the tested
models, but it can not be guaranteed that the current implementation works for all versions and all model setups.
The Bladed interface has been tested with the demo_a model for idling, parked and power production linearization, both
with and without MBC transformation. The tests have been done on linearization results with models from version 4.3 up
to 4.11.

HAWCStab2
----------

The HAWCStab2 interface is build on mainly two classes. The class :class:`HAWCStab2Data <campbellviewer.interfaces.hawcstab2.HAWCStab2Data>`
can read results files saved in `\*.cmb`, `\*.amp` and `\*.opt`. In addition, binary results files can be read using
:class:`HS2BINReader <campbellviewer.interfaces.hawcstab2.HS2BINReader>`.
