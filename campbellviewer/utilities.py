"""
Module containing utilities for the campbellviewer.
"""

import re
from PyQt5.QtCore import Qt


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
        if bool(re.search(r'\([0-9]+\)', unique_name)):
            id = re.findall(r'\([0-9]+\)', unique_name)[-1]
            unique_name = unique_name.replace(id, id[0 ] +str(int(id[1:-1] ) +1 ) +id[-1])
        else:
            unique_name = unique_name + ' (1)'

    return unique_name


class AEMode:
    """
    Storage class for aeroelastic modes
    """
    def __init__(self, name='', symmetry_type='', whirl_type='', wt_component='', blade_mode_type=''):
        """
        Initializes aeroelastic mode instance

        Args:
            name : string
                name of the aeroelastic mode (e.g. 1st FW flap, etc.)
            symmetry_type : string
                indication whether this is a symmetrical or asymmetrical mode
            whirl_type : string
                type of whirling motion (FW or BW)
            wt_component : string
                indication which wind turbine component has the main contribution in this mode
            blade_mode_type : string
                type of blade mode (edge, flap, torsion)
        """
        self.name = name
        self.symmetry_type = symmetry_type
        self.whirl_type = whirl_type  # BW, FW,
        self.wt_component = wt_component  # blade, tower, drivetrain, ...
        self.blade_mode_type = blade_mode_type  # edge, flap, torsion

        self.categorize_mode()

    def categorize_mode(self):
        """ Categorize mode

        Define which categories a mode belongs to depending on the mode name (given by the tool interface)
        """
        if self.symmetry_type == '':
            if any(substring in self.name.lower() for substring in ['sym', 'symmetric', 'collective']):
                self.symmetry_type = 'symmetric'
            elif any(substring in self.name.lower() for substring in ['fw', 'bw', 'forward whirl',
                                                                      'backward whirl', 'cyclic']):
                self.symmetry_type = 'asymmetric'

        if self.whirl_type == '':
            if any(substring in self.name.lower() for substring in ['fw', 'forward whirl']):
                self.whirl_type = 'FW'
            elif any(substring in self.name.lower() for substring in ['bw', 'backward whirl']):
                self.whirl_type = 'BW'

        if self.wt_component == '':
            if any(substring in self.name.lower() for substring in ['twr', 'tower']):
                self.wt_component = 'tower'
            elif any(substring in self.name.lower() for substring in ['drivetrain', 'drvtrn']):
                self.wt_component = 'drivetrain'
            elif any(substring in self.name.lower() for substring in ['rotor', 'blade', 'bw', 'fw', 'backward whirl',
                                                                      'forward whirl', 'edge', 'flap', 'edgewise',
                                                                      'flapwise']):
                self.wt_component = 'blade'

        if self.blade_mode_type == '':
            if any(substring in self.name.lower() for substring in ['edge']):
                self.blade_mode_type = 'edge'
            elif any(substring in self.name.lower() for substring in ['flap']):
                self.blade_mode_type = 'flap'
            elif any(substring in self.name.lower() for substring in ['tors']):
                self.blade_mode_type = 'torsion'

    def summary(self):
        """
        Return a formatted string with a summary of the mode information (e.g. for tooltip)

        Returns:
            summary : string
                Formatted string with summary of mode information
        """
        return 'Name: {}\nSymmetry type: {}\nWhirl type: {}\nWT component: {}\nBlade mode type: {}'.format(self.name,
                                                                                                           self.symmetry_type,
                                                                                                           self.whirl_type,
                                                                                                           self.wt_component,
                                                                                                           self.blade_mode_type)

    def filter(self, filter):
        r"""
        Check if this AE mode matches with the filter

        Args:
            filter : tuple
                tuple with three entries (symmetry_type, whirl_type, wt_component, blade_mode_type).
                'all' is used as wildcard

        Returns:
            Qt.Checked if mode matches filter, Qt.Unchecked if mode does not match filter
        """
        if (self.symmetry_type == filter[0] or filter[0] == 'all') and \
           (self.whirl_type == filter[1] or filter[1] == 'all') and \
           (self.wt_component == filter[2] or filter[2] == 'all') and \
           (self.blade_mode_type == filter[3] or filter[3] == 'all'):
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
        return self.name + '$' + self.symmetry_type + '$' + self.whirl_type + '$' + self.wt_component + '$' + self.blade_mode_type

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
        splitted_text = plain_text.split('$')
        if len(splitted_text) == 4:
            return cls(name=splitted_text[0], symmetry_type=plain_text.split('$')[1],
                       whirl_type=plain_text.split('$')[2], wt_component=plain_text.split('$')[3])
        elif len(splitted_text) == 5:
            return cls(name=splitted_text[0], symmetry_type=plain_text.split('$')[1],
                       whirl_type=plain_text.split('$')[2], wt_component=plain_text.split('$')[3],
                       blade_mode_type=plain_text.split('$')[4])


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
