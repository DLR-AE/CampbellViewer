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
    """
    while unique_name in occupied_names:
        if bool(re.search('\([0-9]+\)', unique_name)):
            id = re.findall('\([0-9]+\)', unique_name)[-1]
            unique_name = unique_name.replace(id, id[0 ] +str(int(id[1:-1] ) +1 ) +id[-1])
        else:
            unique_name = unique_name + ' (1)'

    return unique_name


class AEMode:
    """ Storage class for aeroelastic modes """
    def __init__(self, name='', symmetry_type='', whirl_type='', wt_component=''):
        self.name = name
        self.symmetry_type = symmetry_type
        self.whirl_type = whirl_type  # BW, FW,
        self.wt_component = wt_component  # blade, tower, drivetrain, ...

    def summary(self):
        """ Return a formatted string with a summary of the mode information (e.g. for tooltip) """
        return 'Name: {}\nSymmetry type: {}\nWhirl type: {}\nWT component: {}'.format(self.name, self.symmetry_type,
                                                                                      self.whirl_type,
                                                                                      self.wt_component)

    def filter(self, filter):
        """
        Check if this AE mode matches with the filter

        Args:
            filter (tuple) : tuple with three entries (symmetry_type, whirl_type, wt_component). 'all' is used as
            wildcard
        """
        if (self.symmetry_type == filter[0] or filter[0] == 'all') and \
           (self.whirl_type == filter[1] or filter[1] == 'all') and \
           (self.wt_component == filter[2] or filter[2] == 'all'):
            return Qt.Checked
        else:
            return Qt.Unchecked

    def to_plain_text(self):
        return self.name + '$' + self.symmetry_type + '$' + self.whirl_type + '$' + self.wt_component

    @classmethod
    def from_plain_text(cls, plain_text):
        return cls(name=plain_text.split('$')[0], symmetry_type=plain_text.split('$')[1],
                   whirl_type=plain_text.split('$')[2], wt_component=plain_text.split('$')[3])

class MPLLinestyle:
    """ Storage class for linestyle selection in the Campbell plot """
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

        self.nr_lines_allocated = 0  # number of lines that already got a linestyle allocated, these lines are not necessarily all visible
        self.colormap = colormap
        self.markersizedefault = markersizedefault
        self.style_sequences = style_sequences
        self.lw = lw
        self.overwrite_cm_color_sequence = overwrite_cm_color_sequence
        self.style_determination_order = style_determination_order

    def new_ls(self):
        """ Get the next linestyle and increase the nr_lines_allocated by one """

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
     store the metadata. This class is just a wrapper around the xarray attributes. """
    def __init__(self, xr_attrs=None):
        self.xr_attrs = xr_attrs

    def summary(self):
        """ Return a formatted string with a summary of the mode information (e.g. for tooltip) """
        summary_str = ''
        for key, value in self.xr_attrs.items():
            if type(value) is not str:
                print('Metadata key {} can not be shown')
            else:
                summary_str += '{}: {}\n'.format(key, value)
        return summary_str