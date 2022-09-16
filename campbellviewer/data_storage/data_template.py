"""
This module contains data storing classes
"""
# Global libs
import xarray as xr  # minimal version 0.20.2 (to have drop_sel function)
from datetime import datetime
import os

# Local libs


class AbstractLinearizationData:
    """Abstract data class for linearization result data

    In the initial implementation, this class was a direct subclass of an xarray dataset. This worked, but subclassing
    of xarray datasets is not supported (https://github.com/pydata/xarray/issues/4660,
    https://github.com/pydata/xarray/issues/3980). So, instead we use the answer given in issue 4660, by creating a
    slot attribute for the dataset.

    The initial idea was to have <mode_names> and <participation mode names> as coordinates, but this idea was
    disregarded in order to have a dedicated aeroelastic mode class. The coordinates are therefore just the indices.
    """
    __slots__ = ("ds",)

    def __init__(self):
        self.__class__.ds.__set__(self, xr.Dataset())

        self.ds["frequency"] = None                     # (["operating_point_ID", "mode_ID"], np.array())
        self.ds["damping"] = None                       # (["operating_point_ID", "mode_ID"], np.array())
        self.ds["realpart"] = None                      # (["operating_point_ID", "mode_ID"], np.array())
        self.ds["participation_factors_amp"] = None     # (["operating_point_ID", "participation_mode_ID", "mode_ID"], np.array())
        self.ds["participation_factors_phase"] = None   # (["operating_point_ID", "participation_mode_ID", "mode_ID"], np.array())
        self.ds["operating_points"] = None              # (["operating_point_ID", "operating_parameter"], np.array())
        self.ds["modes"] = None                         # (["mode_ID"], [])
        self.ds["participation_modes"] = None           # (["participation_mode_ID"], [])
        # self.ds["operating_parameter"] = None           # []
        # self.ds.set_coords(["operating_parameter"])

        # Timestamp and user metadata are saved when the dataset class is initiated
        self.ds.attrs["timestamp"] = datetime.now().strftime("%c")
        self.ds.attrs["user"] = os.getlogin()

    def remove_modes(self, mode_ids):
        """Remove modes (identified by their index) from the database.
        """
        try:
            return self.ds.drop_sel(mode_ID=mode_ids)
        except AttributeError:
            print('Removing data from the xarray dataset did not succeed. '
                  'This could be due to an outdated xarray version'
                  'Please update to version >0.20.2')
            print('Nothing has been removed from the database')