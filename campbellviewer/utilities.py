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
    def __init__(self, name='', symmetry_type=None, whirl_type=None, wt_component=None):
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

