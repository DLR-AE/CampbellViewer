.. _sec_dev_main_building_blocks:

Main building blocks of the tool
################################

* The GUI mainly contained in the :mod:`main_app <campbellviewer.main_app>` module
* The tree model which allows interaction (enabling/disabling, highlighting,
  deleting) of the loaded datasets
* The most important data structures are defined as :mod:`globals <campbellviewer.settings.globals>`,
  such that they can be accessed easily by all modules

  * ``database`` (:class:`LinearizationDataWrapper <campbellviewer.data_storage.data.LinearizationDataWrapper>`):
    dictionary with the loaded datasets and further methods to load/unload data
  * ``view_cfg`` (:class:`ViewSettings <campbellviewer.settings.view.ViewSettings>`):
    class with information for the GUI/Matplotlib, this can be seen
    as a link between the tree model, the database and the plots. This contains
    information such as 'which datasets should be plotted', 'which datasets are
    selected (and should therefore be highlighted)', 'which Matplotlib artists
    have already been plotted', etc.

* The individual datasets are xarray datasets, an abstract template is given in
  data_template.py
* The interfaces will get information from the GUI such as the paths to result
  files and load data into the xarray dataset convention.
