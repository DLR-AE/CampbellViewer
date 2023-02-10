.. _sec_ug_data_handling:

Data handling
=============

Adding data
------------

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
---------------------------------------

If the data has been loaded in the GUI, it can be saved to a CampbellViewer
specific file format (netcdf4) by **File -> Save to Database**. This will
automatically save all data which has been loaded to the same file. Data which
has been stored in these files can be reloaded by **File -> Load Database**. It
is possible to load a database from the command line with the `-d` argument, e.g.

.. code-block:: console

    campbellviewer -d .\examples\data\example_database\example_database.nc

Example data
------------

Example HAWCStab2 and Bladed linearization data can be found in the examples
directory. Note that this data is just for testing purposes.
