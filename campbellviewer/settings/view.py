"""
Module for settings of view in the main application.
"""

import matplotlib


class ViewSettings:
    """
    A class to gather all settings which manage the view of the GUI.
    Currently implemented: active_data -> a dictionary with all datasets which have to be shown on the canvas,
    selected_branch -> a list with the 'branch' of the tree view that is selected -> this will be used by the canvas
    to highlight this mode.
    Possible further developments: linestyles, all figure settings, etc.
     """
    def __init__(self):
        """
        Initializes the view settings

        Attributes:
            active_data : dict
                dictionary which mimics the tree model and represents the items in the tree which are active.
                e.g. {'Tool1': {'ds1': [0, 1, 2, 3], 'ds2': [2, 4]}} -> dictionary with tools on the first level ->
                datasets on the second level, mode indices as a list on the third level
            selected_data : list
                list with each individual branch of the tree model which is selected.
                e.g. [['ds1', 'tool1'], [[3], 'ds2', 'tool2'], [[5], 'ds2', 'tool1']]
                -> dataset 1 of tool 1 is completely selected, mode 3 and mode 5 of dataset 2 are individually selected
            lines : dict
                dictionary which contains all artists of the Campbell plot which have been plotted before. They are used
                to plot the artist if it is active and store the information such that the same line is plotted when
                the used disables/enables a dataset
            ls : MPLLinestyle
                definition of the linestyles used in the Campbell plot
            axes_limits : tuple
                tuple with the the axis limits of both the frequency and damping plot
                -> (axes1.get_xlim(), axes1.get_ylim(), axes2.get_ylim())
            auto_scaling_x : boolean
                flag whether xaxis limits have to be adjusted automatically
            auto_scaling_y : boolean
                flag whether yaxis limits have to be adjusted automatically
        """
        self.active_data = {}
        self.selected_data = []
        self.lines = {}
        self.ls = MPLLinestyle()
        self.axes_limits = None
        self.auto_scaling_x = True
        self.auto_scaling_y = True

    def update_lines(self):
        for atool in self.active_data:
            self.ls.nr_lines_allocated[atool] = 0
            for ads in self.active_data[atool]:
                for mode_idx, line in enumerate(self.lines[atool][ads]):
                    if line is not None:
                        ls = self.ls.new_ls(atool)
                        for idx in [0, 1]:
                            self.lines[atool][ads][mode_idx][idx].set_linewidth(self.ls.lw)
                            self.lines[atool][ads][mode_idx][idx].set_linestyle(ls['linestyle'])
                            self.lines[atool][ads][mode_idx][idx].set_color(ls['color'])
                            self.lines[atool][ads][mode_idx][idx].set_marker(ls['marker'])
                            self.lines[atool][ads][mode_idx][idx].set_markersize(self.ls.markersizedefault)
        return self.lines

    def remove_lines(self, branch):
        """
        Remove line2D objects of modes which are being deleted

        Args:
            branch (list): list with mode_idx, dataset, tool that have to be removed. This list will have length 1 if
                a tool has to be removed. It will have length 2 if a dataset has to be removed. And it will have length
                3 if modes have to be removed.
                Examples: branch = ['dataset_name', 'tool_name'] or branch = [[0, 1, 3], 'dataset_name', 'tool_name']
        """
        if len(branch) == 1:
            del self.lines[branch[0]]
        elif len(branch) == 2:
            del self.lines[branch[1]][branch[0]]
        elif len(branch) == 3:
            self.lines[branch[2]][branch[1]] = [line for mode_ID, line in enumerate(self.lines[branch[2]][branch[1]]) if
                                                mode_ID not in branch[0]]
        else:
            print('The list provided can only have 1, 2, or 3 values. Nothing removed from ViewSettings.lines object')
        return

    def reset_all_lines(self):
        """
        Reset all the stored lines.
        This method is currently no longer used, but can be useful later on.
        """
        for tool in self.lines:
            for ds in self.lines[tool]:
                self.lines[tool][ds] = [None]*len(self.lines[tool][ds])
            self.ls.nr_lines_allocated[tool] = 0

    def reset_these_lines(self, tool, ds):
        """
        Reset the lines for this tool and dataset.
        """
        self.lines[tool][ds] = [None]*len(self.lines[tool][ds])

    def xparam2xlabel(self, xaxis_param):
        """
        Some default xlabels
        """
        if xaxis_param == 'rot. speed [rpm]':
            return 'RPM in $1/min$'
        elif xaxis_param == 'wind speed [m/s]':
            return 'Wind Speed in m/s'
        elif xaxis_param == 'pitch [deg]':
            return 'Pitch angle in $^\circ$'
        else:
            return xaxis_param

    def get_axes_limits(self, xlim, ylim, y2lim):
        """
        Get the limits that matplotlib autoscale wants to give to the axes. Decide to use those, user_defined limits or
        limits from previous refresh.
        """
        # some hardcoded limits
        ylim = (max(0, ylim[0]), ylim[1])
        y2lim = (max(-5, y2lim[0]), y2lim[1])

        if self.axes_limits is None or (self.auto_scaling_x is True and self.auto_scaling_y is True):
            self.axes_limits = (xlim, ylim, y2lim)
            self.auto_scaling_x = False
            self.auto_scaling_y = False
        elif self.auto_scaling_x is True:
            self.axes_limits = (xlim, self.axes_limits[1], self.axes_limits[2])
            self.auto_scaling_x = False
        elif self.auto_scaling_y is True:
            self.axes_limits = (self.axes_limits[0], ylim, y2lim)
            self.auto_scaling_y = False

        return self.axes_limits


class MPLLinestyle:
    """Storage class for linestyle selection in the Campbell plot.
    """
    def __init__(self,
                 colormap='tab10',
                 markersizedefault=6,
                 style_sequences={'color': [],
                                  'linestyle': ['-', '--', '-.', ':'],
                                  'marker': ['', 'o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'X']},
                 lw=1.0,
                 overwrite_cm_color_sequence=None,  # ['r','g','b','y','c','m','k']
                 style_determination_order=['color', 'marker', 'linestyle']
                 ):
        """
        Args:
            colormap : string
                name of the matplotlib colormap which will be used to select colors
            markersizedefault : float
                marker size
            style_sequences : dict
                dictionary with lists for the color, linestyle and marker type which will be used to define the
                linestyles
            lw : float
                linewidth
            overwrite_cm_color_sequence : list
                overwrite the color sequence given by the matplotlib colormap
            style_determination_order : list
                order in which new linestyles are chosen -> list with 'color', 'marker', 'linestyle'.
                E.g. if ['color', 'marker', 'linestyle'] -> first the lines will be differentiated by color, then by
                marker, then by linestyle
        """
        self.nr_lines_allocated = {'HAWCStab2': 0, 'Bladed (lin.)':0}
        self.colormap = colormap
        self.markersizedefault = markersizedefault
        self.style_sequences = style_sequences
        self.lw = lw
        self.overwrite_cm_color_sequence = overwrite_cm_color_sequence
        self.style_determination_order = style_determination_order

    def new_ls(self, tool:str) -> dict:
        """Get the next linestyle and increase the nr_lines_allocated by one.

        Args:
            tool:
                Name of the tool for which frequencies and damping ratios are
                plotted.

        Returns:
            linestyle
                Dictionary with keywords 'color', 'marker', 'linestyle' and the
                selected values for each of them.
        """

        if self.overwrite_cm_color_sequence is not None:
            self.style_sequences['color'] = self.overwrite_cm_color_sequence
        else:
            self.style_sequences['color'] = [matplotlib.colors.to_hex(color) for color in matplotlib.cm.get_cmap(self.colormap).colors]

        counter = self.nr_lines_allocated[tool]

        seq_0 = self.style_sequences[self.style_determination_order[0]]
        seq_1 = self.style_sequences[self.style_determination_order[1]]
        seq_2 = self.style_sequences[self.style_determination_order[2]]

        idx_0 = counter % len(seq_0)

        # Fix index 1 for different tools (Markers for default view)
        if tool == 'HAWCStab2':
            idx_1 = 0
        elif tool == 'Bladed (lin.)':
            idx_1 = 1

        idx_2 = int(self.nr_lines_allocated[tool] / len(seq_0)) % len(seq_1)

        self.nr_lines_allocated[tool] += 1

        return {self.style_determination_order[0]: seq_0[idx_0],
                self.style_determination_order[1]: seq_1[idx_1],
                self.style_determination_order[2]: seq_2[idx_2],}

    def verify_inputs(self):
        raise NotImplementedError
