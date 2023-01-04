.. _sec_users-guide:

User Guide
==========

User guide for the unified plotting tool for Campbell diagrams, processing
results of wind turbine simulation tools HAWCStab2 and Bladed. This user guide
contains a section for users who just want to use the tool and a section with
more detailed information for users who would like to modify or contribute to
the tool.

Installation
############

Information w.r.t the installation is given in the README

Adding data
############

CampbellViewer can visualize Campbell diagrams made by HAWCStab2 or a Bladed
linearization simulation. The tool has interface scripts which can read
HAWCStab2 and Bladed specific data files and transform it into a CampbellViewer
convention.
To load new data go to **File -> Add New Dataset**, select from which tool data will
be read, and give a name for the dataset. Note that this dataset name has to be
unique. If the name already exists, it will be made unique automatically. For
HAWCStab2 data, you will have to navigate to the \*.cmb, \*.amp and
(\*.opt or \*.op) file of your simulation. For Bladed linearization data, you have
to navigate to the .$PJ file of your simulation. It is assumed that all Bladed
result files can be found in the same directory.

Saving and loading data from a database
#######################################

If the data has been loaded in the GUI, it can be saved to a CampbellViewer
specific file format (netcdf4) by **File -> Save to Database**. This will
automatically save all data which has been loaded to the same file. Data which
has been stored in these files can be reloaded by **File -> Load Database**. It
is possible to load a database from the command line with the `-d` argument, e.g.
::

    campbellviewer -d .\examples\data\example_database\example_database.nc

Example data
#############

Example HAWCStab2 and Bladed linearization data can be found in the examples
directory. Note that this data is just for testing purposes.

Functionalities of the tool
############################

The main functionality of the tool is to interactively visualize Campbell
diagrams. Modes can be added or removed to the plot through the data tree.
Highlighting modes is possible by clicking on the line in the matplotlib diagram
or by selecting the field in the data tree. A second main functionality is a
plot of the participation factors.
This can be started by **Tools -> Plot amplitudes of modes**, **Tools -> Plot
amplitudes of highlighted mode**, or through the context menu of the data tree.
The context menu of the data tree can also be used to select specific modes or
filter modes based on specific characteristics.

Developer Guide
###############
TBD


Main building blocks of the tool
################################
* The GUI mainly contained in the main_app module
* The tree model which allows interaction (enabling/disabling, highlighting,
  deleting) of the loaded datasets
* The most important data structures are defined as globals, such that they can
  be accessed easily by all modules

  * database = dictionary with the loaded datasets and further methods to
    load/unload data
  * view_cfg = class with information for the GUI/matplotlib, this can be seen
    as a link between the tree model, the database and the plots. This contains
    information such as 'which datasets should be plotted', 'which datasets are
    selected (and should therefore be highlighted)', 'which matplotlib artists
    have already been plotted', etc.

* The individial datasets are xarray datasets, an abstract template is given in
  data_template.py
* The interfaces will get information from the GUI such as the paths to result
  files and load data into the xarray dataset convention.
