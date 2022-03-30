###########
#
# Lib for reading HAWCStab2 linearization results
#
###########

# global libs
import numpy as np

# local libs
from data_template import AbstractLinearizationData
from utilities import assure_unique_name, AEMode


class HAWCStab2Data(AbstractLinearizationData):
    """ This is a class for handling HAWCStab2 linearization data """
    
    def __init__(self, filenamecmb=None, filenameamp=None, filenameopt=None):
        super(HAWCStab2Data, self).__init__()
        
        self.attrs["filenamecmb"] = filenamecmb
        self.attrs["filenameamp"] = filenameamp
        self.attrs["filenameopt"] = filenameopt

    def read_cmb_data(self, filenamecmb=None, skip_header_lines=1):
        """ reads and parse the HS2 result cmb data
        
            There are three blocks for freq./damping/real part.
        """
        if filenamecmb is not None:
            self.attrs["filenamecmb"] = filenamecmb
        # read file
        try:
            hs2cmd = np.loadtxt(self.attrs["filenamecmb"], skiprows=skip_header_lines, dtype='float')
        except OSError:
            print('ERROR: HAWCStab2 cmb file %s not found! Abort!' % self.attrs["filenamecmb"])
            return
        
        # reorder data
        myshape = np.shape(hs2cmd)
        num_windspeeds = int(myshape[0])
        num_modes      = int((myshape[1]-1)/3)
        frequency  = np.zeros([num_windspeeds, num_modes])
        damping    = np.zeros([num_windspeeds, num_modes])
        realpart   = np.zeros([num_windspeeds, num_modes])

        for i_mode in range(0, num_modes):
            frequency[:, i_mode] = hs2cmd[:, i_mode+  1]
            damping  [:, i_mode] = hs2cmd[:, i_mode+ 61]
            realpart [:, i_mode] = hs2cmd[:, i_mode+121]

        ws = hs2cmd[:, 0]
        self["frequency"] = (["operating_point_ID", "mode_ID"], frequency)
        self["damping"] = (["operating_point_ID", "mode_ID"], damping)
        self["realpart"] = (["operating_point_ID", "mode_ID"], realpart)

        print('INFO: HS2 campbell data loaded successfully:')
        print('      - %4i modes' % num_modes)
        print('      - %4i wind speeds' % num_windspeeds)
        
    def read_amp_data(self, filenameamp=None, skip_header_lines=5):
        """ reads and parse the HS2 result amp data

            - The first 5 rows contains header text.
            - Column 1 contains wind speeds.
            - Every mode has got 30 columns of sensor data for 15 sensors, each sensor has a normalized deflection/rotation and a phase.
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

            # Mode number:             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1             1 
            # Column num.:             2             3             4             5             6             7             8             9            10            11            12            13            14            15            16            17            18            19            20            21            22            23            24            25            26            27            28            29            30            31 
            # Wind speed       TWR x [m]   phase [deg]     TWR y [m]   phase [deg] TWR yaw [rad]   phase [deg]     SFT x [m]   phase [deg]     SFT y [m]   phase [deg] SFT tor [rad]   phase [deg]  Sym edge [m]   phase [deg]   BW edge [m]   phase [deg]   FW edge [m]   phase [deg]  Sym flap [m]   phase [deg]   BW flap [m]   phase [deg]   FW flap [m]   phase [deg]Sym tors [rad]   phase [deg] BW tors [rad]   phase [deg] FW tors [rad]   phase [deg] 
                        
        """
        if filenameamp is not None:
            self.attrs["filenameamp"] = filenameamp

        sensor_list = ['TWR SS', 'TWR FA', 'TWR yaw', 'SFT x', 'SFT y', 'SFT tor', 'Sym edge', 'BW edge', 'FW edge', 'Sym flap', 'BW flap', 'FW flap', 'Sym tors', 'BW tors', 'FW tors']
        # self.coords["participation_mode_names"] = sensor_list
        self["participation_modes"] = (["participation_mode_ID"], [AEMode(name=name) for name in sensor_list])
        num_sensors = len(sensor_list)
        
        # read file
        try:
            hs2part = np.loadtxt(self.attrs["filenameamp"], skiprows=skip_header_lines, dtype='float')
        except OSError:
            print('ERROR: HAWCStab2 cmb file %s not found! Abort!' % self.attrs["filenameamp"])
            return
        
        # reorder data
        myshape = np.shape(hs2part)
        num_windspeeds = int(myshape[0])
        num_modes = int((myshape[1]-1)/num_sensors/2)
        amp_data = np.zeros([num_windspeeds, num_sensors, num_modes])
        phase_data = np.zeros([num_windspeeds, num_sensors, num_modes])

        for i in range(0, num_modes):
            for j in range(0, num_sensors):
                amp_index   = i * num_sensors * 2 + 1 + 2 * j
                phase_index = i * num_sensors * 2 + 2 + 2 * j
                amp_data[:, j, i] = hs2part[:, amp_index]
                phase_data[:, j, i] = hs2part[:, phase_index]

        self["participation_factors_amp"] = (
        ["operating_point_ID", "participation_mode_ID", "mode_ID"], amp_data)
        self["participation_factors_phase"] = (
        ["operating_point_ID", "participation_mode_ID", "mode_ID"], phase_data)

        # determine dominant DOF per mode
        mode_names = []
        for i in range(0, num_modes):
            mean_DOF = np.mean(amp_data[:, :, i], axis=0)
            mode_names.append(sensor_list[np.argmax(mean_DOF)])
        
        # override first tower mode
        if mode_names[2] == sensor_list[0]:
            mode_names[1] = sensor_list[1]

        # # make sure mode names are unique -> mode names are used as indices in xarrays
        # unique_mode_names = []
        # for mode_name in mode_names:
        #     unique_mode_names.append(assure_unique_name(mode_name, unique_mode_names))
        # self.coords["mode_names"] = unique_mode_names
        self["modes"] = (["mode_ID"], [AEMode(name=name) for name in mode_names])

        print('INFO: HS2 amplitude data loaded successfully:')
        print('      - %4i modes' % num_modes)
        print('      - %4i wind speeds' % num_windspeeds)

    def read_opt_data(self, filenameopt=None, skip_header_lines=1):
        """ reads the operational data from HS2 """
        if filenameopt is not None:
            self.attrs["filenameopt"] = filenameopt
        try:
            HS2_optdata = np.loadtxt(self.attrs["filenameopt"], skiprows=skip_header_lines, dtype='float')
        except OSError:
            print('ERROR: HAWCStab2 opt file %s not found! Abort!' % self.attrs["filenameopt"])
            return

        self.coords["operating_parameter"] = ['wind speed [m/s]', 'pitch [deg]', 'rot. speed [rpm]', 'aero power [kw]', 'aero thrust [kn]']
        self["operating_points"] = (["operating_point_ID", "operating_parameter"],
                                    HS2_optdata)

    def read_data(self):
        self.read_cmb_data()
        self.read_amp_data()
        self.read_opt_data()


if __name__ == "__main__":
    mytest = HAWCStab2Data(r'./example_data/modified.cmb',
                           r'./example_data/modified.amp',
                           r'./example_data/modified.opt')
    mytest.read_data()
