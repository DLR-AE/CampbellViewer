"""
Module for reading alaska/Wind linearization results.
"""

import numpy as np

from campbellviewer.data_storage.data_template import AbstractLinearizationData
from campbellviewer.utilities import AEMode



class AlaskaWindData(AbstractLinearizationData):
    r"""This is a class for handling alaska/Win linearization results, which is based on a implicit Floquet analysis.

    Attributes:
        ds (xarray.Dataset): xarray Dataset containing all linearization data

    Args:
        input_file_results (str):
            Filename of \*.xlsx file containing the alaska/Wind implicit Floquet analyses results.
        input_file_op (str):
            Filename of \*.xml file containing the operations data from alaska/Wind

    """

    def __init__(
        self, input_file_results: None|str, input_file_op: None|str) -> None:
        super().__init__()

        self.ds.attrs['input_file_results'] = input_file_results
        self.ds.attrs['input_file_op'] = input_file_op


    def read_cmb_data(self, input_file_results: None|str=None,):
        """Reads and parse the alaska/Wind result data.

        Args:
            input_file_results:
                Name of the file containing frequency and damping values.

        """

        if input_file_results:
            self.ds.attrs['input_file_results'] = input_file_results

        try:
            hs2cmd = np.loadtxt(self.ds.attrs['filenamecmb'],
                                skiprows=1,
                                dtype='float')
        except OSError:
            print(f'ERROR: HAWCStab2 cmb file {self.ds.attrs["filenamecmb"]} '
                  f'not found! Abort!')
            return

        # reorder data
        myshape = hs2cmd.shape
        num_windspeeds = int(myshape[0])
        # Check file structure
        if np.mod((myshape[1]-1)/2,3) == 0:
            # Aeroelastic analysis
            num_modes = int((myshape[1]-1)/3)
            frequency  = hs2cmd[:,1:num_modes+1]
            damping    = hs2cmd[:,num_modes+1:2*num_modes+1]
            realpart   = hs2cmd[:,2*num_modes+1::]
            self.ds['frequency'] = (['operating_point_ID', 'mode_ID'], frequency)
            self.ds['damping'] = (['operating_point_ID', 'mode_ID'], damping)
            self.ds['realpart'] = (['operating_point_ID', 'mode_ID'], realpart)
        else:
            # Structural analysis
            num_modes = int((myshape[1]-1)/2)
            frequency  = hs2cmd[:,1:num_modes+1]
            damping    = hs2cmd[:,num_modes+1:2*num_modes+1]
            self.ds['frequency'] = (['operating_point_ID', 'mode_ID'], frequency)
            self.ds['damping'] = (['operating_point_ID', 'mode_ID'], damping)

        print(
            f'INFO: HS2 campbell data loaded successfully: \n'
            f'      - {num_modes} modes\n'
            f'      - {num_windspeeds} wind speeds\n'
        )
