"""
Module for reading Bladed linearization results.
"""

import numpy as np
import os
import scipy

from campbellviewer.data_storage.data_template import AbstractLinearizationData
from campbellviewer.utilities import AEMode


class SSIData(AbstractLinearizationData):
    """This is a class for handling Bladed linearization result data.

    Attributes:
        ds (xarray.Dataset): xarray Dataset containing all linearization data

    Args:
        result_dir: Path to directory with Bladed Linearization results
        result_prefix: Name of the Bladed output files
    """

    def __init__(self, result_file: str=None):
        super(SSIData, self).__init__()

        self.matlab_idenfication_file = result_file
        self.ds.attrs["matlab_idenfication_file"] = result_file

    def read_data(self):
        """ Read all available Campbell diagram data. """

        self.ds.coords["operating_parameter"] = ['wind speed [m/s]', 'rot. speed [rpm]']
        self.ds["operating_points"] = (["operating_point_ID", "operating_parameter"], [[10, 10]])

        matlab_data = scipy.io.loadmat(self.matlab_idenfication_file)
        frequency = matlab_data['freq'].squeeze()
        damping = matlab_data['damp'].squeeze()

        # make sure mode names are unique -> add numbers if identical names appear
        mode_names_orig = ['Mode {}'.format(i+1) for i in range(np.size(frequency))]
        modes = []
        for mode_name in mode_names_orig:
            modes.append(AEMode(name=mode_name))

        self.ds["modes"] = (["mode_ID"], modes)
        self.ds["frequency"] = (["operating_point_ID", "mode_ID"], [frequency])
        self.ds["damping"] = (["operating_point_ID", "mode_ID"], [damping])


if __name__ == "__main__":
    pass
