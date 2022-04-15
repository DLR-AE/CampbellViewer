from data_lib import LinearizationDataWrapper


class ViewSettings:
    """
    A class to gather all settings which manage the view of the GUI.
    Currently implemented: active_data -> a dictionary with all datasets which have to be shown on the canvas,
    selected_branch -> a list with the 'branch' of the tree view that is selected -> this will be used by the canvas
    to highlight this mode.
    Possible further developments: linestyles, all figure settings, etc.
     """
    def __init__(self):
        self.active_data = {}
        self.selected_data = []


global database
database = LinearizationDataWrapper()
global view_cfg
view_cfg = ViewSettings()