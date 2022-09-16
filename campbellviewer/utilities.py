"""
Module containing utilities for the campbellviewer.
"""

import re
from PyQt5.QtCore import Qt
import matplotlib


def assure_unique_name(unique_name, occupied_names):
    """
    Modify unique name until no duplicate exists in occupied_names. Modification is done by adding (1), (2), etc.

    Args:
        unique_name : string
            string which should be unique
        occupied_names : array-like
            names which are already in use

    Returns:
        unique_name : string
            Modified unique_name if original unique_name was already available in occupied_names
    """
    while unique_name in occupied_names:
        if bool(re.search('\([0-9]+\)', unique_name)):
            id = re.findall('\([0-9]+\)', unique_name)[-1]
            unique_name = unique_name.replace(id, id[0 ] +str(int(id[1:-1] ) +1 ) +id[-1])
        else:
            unique_name = unique_name + ' (1)'

    return unique_name


class AEMode:
    """
    Storage class for aeroelastic modes
    """
    def __init__(self, name='', symmetry_type='', whirl_type='', wt_component=''):
        """
        Initializes aeroelastic mode instance

        Args:
            name : string
                name of the aeroelastic mode (e.g. 1st FW flap, etc.)
            symmetry_type : string
                indication whether this is a symmetrical or asymmetical model
            whirl_type : string
                type of whirling motion (FW or BW)
            wt_component : string
                indication which is the wind turbine component has the main contribution in this mode
        """
        self.name = name
        self.symmetry_type = symmetry_type
        self.whirl_type = whirl_type  # BW, FW,
        self.wt_component = wt_component  # blade, tower, drivetrain, ...

    def summary(self):
        """
        Return a formatted string with a summary of the mode information (e.g. for tooltip)

        Returns:
            summary : string
                Formatted string with summary of mode information
        """
        return 'Name: {}\nSymmetry type: {}\nWhirl type: {}\nWT component: {}'.format(self.name, self.symmetry_type,
                                                                                      self.whirl_type,
                                                                                      self.wt_component)

    def filter(self, filter):
        """
        Check if this AE mode matches with the filter

        Args:
            filter : tuple
                tuple with three entries (symmetry_type, whirl_type, wt_component). 'all' is used as wildcard

        Returns:
            Qt.Checked if mode matches filter, Qt.Unchecked if mode does not match filter
        """
        if (self.symmetry_type == filter[0] or filter[0] == 'all') and \
           (self.whirl_type == filter[1] or filter[1] == 'all') and \
           (self.wt_component == filter[2] or filter[2] == 'all'):
            return Qt.Checked
        else:
            return Qt.Unchecked

    def to_plain_text(self):
        """
        The AEmode instance has to be converted to a plain text to be saved to a database file

        Returns:
            plain_text_string : string
                AEMode instance condensed into a single string
        """
        return self.name + '$' + self.symmetry_type + '$' + self.whirl_type + '$' + self.wt_component

    @classmethod
    def from_plain_text(cls, plain_text):
        """
        Initializing the class from a plain_text string

        Args:
            plain_text : string
                AEMode instance condensed into a single string

        Returns:
            AEMode instance
        """
        return cls(name=plain_text.split('$')[0], symmetry_type=plain_text.split('$')[1],
                   whirl_type=plain_text.split('$')[2], wt_component=plain_text.split('$')[3])


class MPLLinestyle:
    """
    Storage class for linestyle selection in the Campbell plot
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
        self.nr_lines_allocated = 0  # number of lines that already got a linestyle allocated, these lines are not necessarily all visible
        self.colormap = colormap
        self.markersizedefault = markersizedefault
        self.style_sequences = style_sequences
        self.lw = lw
        self.overwrite_cm_color_sequence = overwrite_cm_color_sequence
        self.style_determination_order = style_determination_order

    def new_ls(self):
        """
        Get the next linestyle and increase the nr_lines_allocated by one

        Returns:
            linestyle : dict
                Dictionary with keywords 'color', 'marker', 'linestyle' and the selected values for each of them
        """
        if self.overwrite_cm_color_sequence is not None:
            self.style_sequences['color'] = self.overwrite_cm_color_sequence
        else:
            self.style_sequences['color'] = [matplotlib.colors.to_hex(color) for color in matplotlib.cm.get_cmap(self.colormap).colors]

        counter = self.nr_lines_allocated

        seq_0 = self.style_sequences[self.style_determination_order[0]]
        seq_1 = self.style_sequences[self.style_determination_order[1]]
        seq_2 = self.style_sequences[self.style_determination_order[2]]

        idx_0 = counter % len(seq_0)
        idx_1 = int(counter / len(seq_0)) % len(seq_1)
        idx_2 = int(counter / (len(seq_0) * len(seq_1))) % len(seq_2)

        self.nr_lines_allocated += 1

        return {self.style_determination_order[0]: seq_0[idx_0],
                self.style_determination_order[1]: seq_1[idx_1],
                self.style_determination_order[2]: seq_2[idx_2],}

    def verify_inputs(self):
        raise NotImplementedError


class DatasetMetaData:
    """
    Storage class for dataset metadata. The initial idea was to have a dedicated storage class for metadata with
     attributes for all metadata, but this requires the metadata of different tools to be in an identical format
     (e.g. input data file names). This was not convenient. Instead, the xarray dataset attributes are directly used to
     store the metadata. This class is just a wrapper around the xarray attributes.
    """
    def __init__(self, xr_attrs=None):
        """
        Args:
            xr_attrs : dict
                dictionary with the attributes of an xarray
        """
        self.xr_attrs = xr_attrs

    def summary(self):
        """
        Return a formatted string with a summary of dataset metadata (e.g. for tooltip)

        Returns:
            summary_str : string
                Formatted string with metadata of a dataset
        """
        summary_str = ''

        for key, value in self.xr_attrs.items():
            if type(value) is not str:
                print('Metadata key {} can not be shown')
            else:
                summary_str += '{}: {}\n'.format(key, value)

        return summary_str
