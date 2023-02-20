.. _sec_pg_data_format:

Data Format
===========

The Database
------------

The database concept of the CampbellViewer is simple, because we do not expect
to require a huge or complex database. The database is a dictionary with two 
layers. The first layer specifies the tool, the second layer specifies the
dataset within this tool: :code:`database[<tool_name>][<dataset_name>]`. The 
database is implemented in the LinearizationDataWrapper in 
campbellviewer.data_storage.data. The database has methods to add_data from a
specific tool, remove data, and to save/load to a database file. The datasets
themselves are based on xarrays. An abstract linearization dataset class is 
defined in campbellviewer.data_storage.data_template.AbstractLinearizationData.
The idea was to make this a child class of an xarray dataset. This worked, but
subclassing of xarray datasets is not supported 
(https://github.com/pydata/xarray/issues/4660,
https://github.com/pydata/xarray/issues/3980). So, instead we use the answer 
given in issue 4660, by creating a slot attribute ('ds') for the dataset. This
xarray dataset will contain all linearization data (frequency, damping, etc.).
In the tool interface scripts the AbstractLinearizationData class is 
subclassed (campbellviewer.interfaces.bladed.BladedLinData and 
campbellviewer.interfaces.hawcstab2.HAWCStab2Data). These interfaces contain
methods to parse result files from the tools and fill out the xarray dataset.
The database can be saved to a file for later use. This is done by using the
xarray.to_netcdf method. Each dataset is saved as a separate group in the 
netcdf file with the combined tool and dataset name as group name.

A Dataset
---------
The xarray dataset can contain following variables with corresponding 
dimensions: 

.. list-table:: 
   :widths: 20 10 50
   :header-rows: 1

   * - Variable
     - Dimensions
     - Description
   * - frequency
     - operating_point_ID x mode_ID
     - Frequency in Hz of each mode at each operating point
   * - damping
     - operating_point_ID x mode_ID
     - Damping ratio in % of each mode at each operating point
   * - realpart
     - operating_point_ID x mode_ID
     - Real part of the eigenvalue of each mode at each operating point
       (currently not used)
   * - participation_factors_amp
     - operating_point_ID x participation_mode_ID x mode_ID
     - Magnitude of the participation of a specific an uncoupled mode to
       the fully coupled mode
   * - participation_factors_phase
     - operating_point_ID x participation_mode_ID x mode_ID
     - Phase of the participation of a specific an uncoupled mode to
       the fully coupled mode
   * - operating_points
     - operating_point_ID x operating_parameter
     - Operating points
   * - modes
     - mode_ID
     - List with AEMode instances for each coupled mode
   * - participation_modes
     - participation_mode_ID
     - List with AEMode instances for each uncoupled mode
   * - coordinates: operating_parameter
     - n.a.
     - List with string identification of the operating parameters

The initial idea was to have <mode_names> and <participation mode names> as 
coordinates in the xarray dataset, but this idea was disregarded in order to
have a dedicated aeroelastic mode class. The coordinates (mode_ID, 
operating_point_ID, participation_mode_ID) are therefore just the indices.
