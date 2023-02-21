.. _sec_ug_examples:

Examples
==========

The example results in this repository are produced by using the `15-MW offshore
reference turbine developed within IEA Wind Task 37 <https://github.com/IEAWindTask37/IEA-15-240-RWT>`_
with a fixed substructure.

HAWCStab2
----------

The HAWCStab2 files were created by using the `make_htc.py <https://github.com/IEAWindTask37/IEA-15-240-RWT/blob/master/HAWC2/IEA-15-240-RWT-FixedSubstructure/scripts/make_htc.py>`_
script.
After creating the input files a structural and aeroelastic modal analysis is
performed for the entire turbine using optimal operational data from 1 to 25 m/s
wind speed with 1 m/s steps. The first 60 modes are evaluated.

Bladed
------
The Bladed example simulation is made with the v1 version of the IEA 15 MW turbine. The .prj file can be found here: https://github.com/DLR-AE/CampbellViewer/blob/main/examples/data/bladed/IEA15MW/15MW_NREL_DNV_v1.prj. A Campbell diagram linearisation from 0 to 25 m/s wind speed was performed with 1 m/s steps in the wind speed.
