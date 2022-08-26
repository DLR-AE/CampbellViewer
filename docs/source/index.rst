.. CampbellViewer documentation master file, created by
   sphinx-quickstart on Fri Aug 26 16:03:42 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

CampbellViewer's documentation
==============================

Unified plotting tool for Campbell diagrams, processing results of wind turbine simulation tools HAWCStab2 and Bladed.


Main building blocks
----------------------

- The GUI mainly contained in the CampbellViewer module
- The tree model which allows interaction (enabling/disabling, highlighting, deleting) of the loaded datasets
- The most important data structures are defined as globals, such that they can be accessed easily by all modules
  - database = dictionary with the loaded datasets and further methods to load/unload data
  - view_cfg = class with information for the GUI/matplotlib, this can be seen as a link between the tree model, the database and the plots. This contains information such as 'which datasets should be plotted', 'which datasets are selected (and should therefore be highlighted)', 'which matplotlib artists have already been plotted', etc.
- The individial datasets are xarray datasets, an abstract template is given in data_template.py
- The interfaces will get information from the GUI such as the paths to result files and load data into the xarray dataset convention.


Modules
-------

.. note::
   After packaging the CampbellViewer, modules should go to API reference.

- CampbellViewer.py
  - Main script of the GUI. Contains all QT5 Widgets.

- globals.py
  - The database and some settings which are used by the figures are stored in global variables. These are defined here.

- model_lib.py
  - This module contains the functional description of the tree model which is used to interact with the data.

- data_lib.py
  - This is our description of a database. In the end it is just a dictionary with different datasets. Data can be added through the interfaces of the different tools, data can be removed, databases can be saved to a file and databases can be loaded from these files.

- data_template.py
  - This module contains the abstract linearization data class.

- BladedLin_lib.py
  - Interface for parsing results made with Bladed

- HAWCStab2_lib.py
  - Interface for parsing results made with hs2

- read_hs2turbine_mode_shapes.py
  - Interface for parsing hs2 mode shapes

- utilities.py
  - Some useful methods and classes


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
