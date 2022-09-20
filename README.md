# CampbellViewer

Unified plotting tool for Campbell diagrams, processing results of wind turbine simulation tools HAWCStab2 and Bladed


## Main building blocks
- The GUI mainly contained in the CampbellViewer module
- The tree model which allows interaction (enabling/disabling, highlighting, deleting) of the loaded datasets
- The most important data structures are defined as globals, such that they can be accessed easily by all modules
  - database = dictionary with the loaded datasets and further methods to load/unload data
  - view_cfg = class with information for the GUI/matplotlib, this can be seen as a link between the tree model, the database and the plots. This contains information such as 'which datasets should be plotted', 'which datasets are selected (and should therefore be highlighted)', 'which matplotlib artists have already been plotted', etc.
- The individial datasets are xarray datasets, an abstract template is given in data_template.py
- The interfaces will get information from the GUI such as the paths to result files and load data into the xarray dataset convention.

## Installation

The ``campbellviewer`` supports Python 3.9 or newer.

You can install the package using

    $ pip install git+https://github.com/DLR-AE/CampbellViewer.git

---
**NOTE**

If you want to install a certain branch add **@<branch_name>** to the end of
the URL.

---

To start the ``campbellviewer`` just type

    $ campbellviewer


Developers can clone the git to a local directory and run the following command
to install the package in development mode.

    $ pip install -e .