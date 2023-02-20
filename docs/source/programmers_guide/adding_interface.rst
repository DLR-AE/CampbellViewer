.. _sec_pg_adding_interface:

Adding an Interface
===================

The Interface Script
--------------------

If you want to visualize data from your own tool with the GUI, the preferred
way is to setup an interface script, similar to the existing interfaces to 
Bladed and HAWCStab2. You should create a child class of the 
AbstractLinearizationData and implement methods to parse data from your result
files and transform them into the CampbellViewer format. 

Please add an example dataset for your tool in the CampbellViewer/examples/data
directory. Please also consider adding testing routines for your interface in 
CampbellViewer/tests/interfaces.

Further required modifications in the main_app and data_storage.data
--------------------------------------------------------------------

Further modifications which have to be made:

* In the campbellviewer.data_storage.data.LinearizationDataWrapper.add_data
  method you will have to add an additional if-statement which will initialize
  the new dataset and call the method to read the data.
* In the campbellviewer.dialogs.SettingsPopupDataSelection initialization,
  you have to add the name of your tool to the __ToolSelection ComboBox
* In the campbellviewer.main_app.ApplicationWindow.dataSelection, you have
  to add an if-statement which opens the file name dialog for your tool.
* In the campbellviewer.main_app.ApplicationWindow, you have to add an
  open filename dialog (similar to openFileNameDialogHAWCStab2) to find your
  result file and to call the database.add_data method.