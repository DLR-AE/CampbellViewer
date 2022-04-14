"""
This module contains data storing classes
"""
# global libs
import xarray as xr  # minimal version 0.20.2 (to have drop_sel function)

# local libs


class AbstractLinearizationData(xr.Dataset):
    """
    Abstract data class for linearization result data

    The initial idea was to have <mode_names> and <participation mode names> as coordinates, but this idea was
    disregarded in order to have a dedicated aeroelastic mode class. The coordinates are therefore just the indices.
    """

    def __init__(self, ):
        super(AbstractLinearizationData, self).__init__()

        self["frequency"] = None                     # (["operating_point_ID", "mode_ID"], np.array())
        self["damping"] = None                       # (["operating_point_ID", "mode_ID"], np.array())
        self["realpart"] = None                      # (["operating_point_ID", "mode_ID"], np.array())
        self["participation_factors_amp"] = None     # (["operating_point_ID", "participation_mode_ID", "mode_ID"], np.array())
        self["participation_factors_phase"] = None   # (["operating_point_ID", "participation_mode_ID", "mode_ID"], np.array())
        self["operating_points"] = None              # (["operating_point_ID", "operating_parameter"], np.array())
        self["modes"] = None                         # (["mode_ID"], [])
        self["participation_modes"] = None           # (["participation_mode_ID"], [])
        # self["operating_parameter"] = None           # []
        # self.set_coords(["operating_parameter"])

    def remove_modes(self, mode_ids):
        """
        Remove modes (identified by their index) from the database
        """
        try:
            return self.drop_sel(mode_ID=mode_ids)
        except AttributeError:
            print('Removing data from the xarray dataset did not succeed. '
                  'This could be due to an outdated xarray version'
                  'Please update to version >0.20.2')
            print('Nothing has been removed from the database')