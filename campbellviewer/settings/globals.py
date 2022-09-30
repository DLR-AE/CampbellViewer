"""
Module for settings of global variables.
"""

from campbellviewer.data_storage.data import LinearizationDataWrapper
from campbellviewer.settings.view import ViewSettings

global database
database = LinearizationDataWrapper()
global view_cfg
view_cfg = ViewSettings()