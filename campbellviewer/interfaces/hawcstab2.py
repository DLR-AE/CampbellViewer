"""
Module for reading HAWCStab2 linearization results.
"""

import numpy as np

from campbellviewer.data_storage.data_template import AbstractLinearizationData
from campbellviewer.utilities import AEMode

# WiVis
from hawcstab_interface import read_turbine_mode_shapes

class HAWCStab2Data(AbstractLinearizationData):
    """This is a class for handling HAWCStab2 linearization data.

    Attributes:
        ds (xarray.Dataset): xarray Dataset containing all linearization data

    Args:
        filenamecmb:
            Filename of \*.cmb file.
        filenameamp:
            Filename of \*.amp file.
        filenameopt:
            Filename of \*.opt file.
        filenameopt:
            Filename of \*.bin file.

    """

    def __init__(
        self, filenamecmb:str='', filenameamp:str='', filenameopt:str='',
        filenamebin:str='',
    ):
        super().__init__()

        self.ds.attrs['filenamecmb'] = filenamecmb
        self.ds.attrs['filenameamp'] = filenameamp
        self.ds.attrs['filenameopt'] = filenameopt
        self.ds.attrs['filenamebin'] = filenamebin

    def read_cmb_data(self, filenamecmb:str='', skip_header_lines:int=1):
        """Reads and parse the HS2 result cmb data.

        Two different types do exist based on the analysis.
        Structural analysis:
        The first column is either rotor speed or wind speed followed by columns
        for frequency and damping ratios for each mode, respectively.

        Aeroelastic or aeroservo-elastic analysis:
        The first column is either rotor speed or wind speed followed by columns
        for frequency, damping ratios and real parts for each mode, respectively.

        Args:
            filenamecmb:
                Name of the file containing frequency and damping values.
            skip_header_lines:
                Number of header lines, which will be skipped. Defaults to 1.

        """

        if filenamecmb:
            self.ds.attrs['filenamecmb'] = filenamecmb

        try:
            hs2cmd = np.loadtxt(self.ds.attrs['filenamecmb'],
                                skiprows=skip_header_lines,
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


    def read_amp_data(self, filenameamp:str='', skip_header_lines:int=5):
        """Reads and parse the HS2 result amp data.

            - The first 5 rows contains header text.
            - Column 1 contains wind speeds.
            - Every mode has got 30 columns of sensor data for 15 sensors, each
              sensor has a normalized deflection/rotation and a phase.
              TWR x   [m]     phase [deg]
              TWR y   [m]     phase [deg]
              TWR yaw [rad]   phase [deg]
              SFT x   [m]     phase [deg]
              SFT y   [m]     phase [deg]
              SFT tor [rad]   phase [deg]
              Sym edge[m]     phase [deg]
              BW edge [m]     phase [deg]
              FW edge [m]     phase [deg]
              Sym flap[m]     phase [deg]
              BW flap [m]     phase [deg]
              FW flap [m]     phase [deg]
              Sym tors[rad]   phase [deg]
              BW tors [rad]   phase [deg]
              FW tors [rad]   phase [deg]

        """

        if filenameamp:
            self.ds.attrs['filenameamp'] = filenameamp

        sensor_list = [
            'TWR SS', 'TWR FA', 'TWR yaw', 'SFT x', 'SFT y', 'SFT tor',
            'Sym edge', 'BW edge', 'FW edge', 'Sym flap', 'BW flap', 'FW flap',
            'Sym tors', 'BW tors', 'FW tors'
        ]

        self.ds['participation_modes'] = (
            ['participation_mode_ID'], [AEMode(name=name) for name in sensor_list]
        )
        num_sensors = len(sensor_list)

        # read file
        try:
            hs2part = np.loadtxt(self.ds.attrs['filenameamp'],
                                 skiprows=skip_header_lines,
                                 dtype='float')
        except OSError:
            print(
                f'ERROR: HAWCStab2 amp file {self.ds.attrs["filenameamp"]} '
                f'not found! Abort!'
            )
            return

        # reorder data
        myshape = hs2part.shape
        num_windspeeds = int(myshape[0])
        num_modes = int((myshape[1]-1)/num_sensors/2)
        amp_data = np.zeros([num_windspeeds, num_sensors, num_modes])
        phase_data = np.zeros([num_windspeeds, num_sensors, num_modes])

        i_start = 0
        i_end = 2*num_sensors+1
        for i_mode in range(0, num_modes):
            amp_data[:, :, i_mode] = hs2part[:,i_start:i_end][:,1::2]
            phase_data[:,:, i_mode] = hs2part[:,i_start:i_end][:,2::2]
            i_start = i_end-1
            i_end = i_end + 2*num_sensors

        # reorder data
        myshape_1 = np.shape(hs2part)
        num_windspeeds_1 = int(myshape_1[0])
        num_modes_1 = int((myshape_1[1]-1)/num_sensors/2)
        amp_data_1 = np.zeros([num_windspeeds_1, num_sensors, num_modes_1])
        phase_data_1 = np.zeros([num_windspeeds_1, num_sensors, num_modes_1])

        for i in range(0, num_modes_1):
            for j in range(0, num_sensors):
                amp_index   = i * num_sensors * 2 + 1 + 2 * j
                phase_index = i * num_sensors * 2 + 2 + 2 * j
                amp_data_1[:, j, i] = hs2part[:, amp_index]
                phase_data_1[:, j, i] = hs2part[:, phase_index]

        self.ds['participation_factors_amp'] = (
            ['operating_point_ID', 'participation_mode_ID', 'mode_ID'], amp_data
        )
        self.ds['participation_factors_phase'] = (
            ['operating_point_ID', 'participation_mode_ID', 'mode_ID'], phase_data
        )

        # Determine dominant DOF per mode
        mode_names = []
        for i_mode in range(0, num_modes):
            mean_dof = np.mean(amp_data[:, :, i_mode], axis=0)
            mode_names.append(sensor_list[np.argmax(mean_dof)])

        # Override first tower mode
        if mode_names[2] == sensor_list[0]:
            mode_names[1] = sensor_list[1]

        # Make sure mode names are unique -> mode names are used as indices in xarrays
        # unique_mode_names = []
        # for mode_name in mode_names:
        #     unique_mode_names.append(assure_unique_name(mode_name, unique_mode_names))
        # self.coords["mode_names"] = unique_mode_names
        self.ds['modes'] = (['mode_ID'], [AEMode(name=name) for name in mode_names])

        print(
            f'INFO: HS2 amplitude data loaded successfully:\n'
            f'      - {num_modes} modes\n'
            f'      - {num_windspeeds} wind speeds\n'
        )


    def read_opt_data(self, filenameopt:str='', skip_header_lines:int=1):
        """Reads the operational data from HS2.

        Operational data file contains 5 columns: Wind speed, pitch, rot. speed,
        aero power, aero thrust.

        Args:
            filenameopt:
                File containing operational data
            skip_header_lines:
                Lines to be skipped

        """

        if filenameopt:
            self.ds.attrs['filenameopt'] = filenameopt

        try:
            hs2optdata = np.loadtxt(self.ds.attrs['filenameopt'],
                                    skiprows=skip_header_lines,
                                    dtype='float')
        except OSError:
            print(f'ERROR: HAWCStab2 opt file {self.ds.attrs["filenameopt"]} '
                  f'not found! Abort!')
            return

        self.ds.coords['operating_parameter'] = [
            'wind speed [m/s]', 'pitch [deg]', 'rot. speed [rpm]',
            'aero power [kw]', 'aero thrust [kn]'
        ]
        self.ds['operating_points'] = (
            ['operating_point_ID', 'operating_parameter'],
            hs2optdata
        )


    def read_data(self):
        self.read_cmb_data()
        self.read_amp_data()
        self.read_opt_data()


    def read_bin_file(self, filenamebin:str=''):
        """Reads the mode shape data from binary HS2 file.

        Args:
            filenamebin:
                Binary file containing mode shapes

        Returns:
            Dictionary containing mode shapes.

        """
        self.substructure, _ = read_turbine_mode_shapes(filenamebin)

        return self.substructure


if __name__ == "__main__":
    mytest = HAWCStab2Data(r"./examples/data/modified.cmb",
                           r"./examples/data/modified.amp",
                           r"./examples/data/modified.opt")
    mytest.read_data()
