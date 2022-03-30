import re


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

