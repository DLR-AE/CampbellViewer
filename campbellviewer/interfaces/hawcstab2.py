"""
Module for reading HAWCStab2 linearization results.
"""

import numpy as np

from campbellviewer.data_storage.data_template import AbstractLinearizationData
from campbellviewer.utilities import AEMode


class HAWCStab2Data(AbstractLinearizationData):
    """This is a class for handling HAWCStab2 linearization data.

    Attributes:
        ds (dict): Dictionary containing filenames of the \*.cmb, \*.amp, and \*.opt files.

    Args:
        filenamecmb (str):
            Filename of \*.cmb file.
        filenameamp (str):
            Filename of \*.amp file.
        filenameopt (str):
            Filename of \*.opt file.

    """

    def __init__(self, filenamecmb=None, filenameamp=None, filenameopt=None):
        super().__init__()

        self.ds.attrs["filenamecmb"] = filenamecmb
        self.ds.attrs["filenameamp"] = filenameamp
        self.ds.attrs["filenameopt"] = filenameopt

    def read_cmb_data(self, filenamecmb=None, skip_header_lines=1):
        """ reads and parse the HS2 result cmb data

            There are three blocks for freq./damping/real part.
        """
        if filenamecmb is not None:
            self.ds.attrs["filenamecmb"] = filenamecmb
        # read file
        try:
            hs2cmd = np.loadtxt(self.ds.attrs["filenamecmb"], skiprows=skip_header_lines, dtype='float')
        except OSError:
            print('ERROR: HAWCStab2 cmb file %s not found! Abort!' % self.ds.attrs["filenamecmb"])
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
        self.ds["frequency"] = (["operating_point_ID", "mode_ID"], frequency)
        self.ds["damping"] = (["operating_point_ID", "mode_ID"], damping)
        self.ds["realpart"] = (["operating_point_ID", "mode_ID"], realpart)

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
            self.ds.attrs["filenameamp"] = filenameamp

        sensor_list = ['TWR SS', 'TWR FA', 'TWR yaw', 'SFT x', 'SFT y', 'SFT tor', 'Sym edge', 'BW edge', 'FW edge', 'Sym flap', 'BW flap', 'FW flap', 'Sym tors', 'BW tors', 'FW tors']
        # self.coords["participation_mode_names"] = sensor_list
        self.ds["participation_modes"] = (["participation_mode_ID"], [AEMode(name=name) for name in sensor_list])
        num_sensors = len(sensor_list)

        # read file
        try:
            hs2part = np.loadtxt(self.ds.attrs["filenameamp"], skiprows=skip_header_lines, dtype='float')
        except OSError:
            print('ERROR: HAWCStab2 cmb file %s not found! Abort!' % self.ds.attrs["filenameamp"])
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

        self.ds["participation_factors_amp"] = (
        ["operating_point_ID", "participation_mode_ID", "mode_ID"], amp_data)
        self.ds["participation_factors_phase"] = (
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
        self.ds["modes"] = (["mode_ID"], [AEMode(name=name) for name in mode_names])

        print('INFO: HS2 amplitude data loaded successfully:')
        print('      - %4i modes' % num_modes)
        print('      - %4i wind speeds' % num_windspeeds)

    def read_opt_data(self, filenameopt=None, skip_header_lines=1):
        """ reads the operational data from HS2 """
        if filenameopt is not None:
            self.ds.attrs["filenameopt"] = filenameopt
        try:
            HS2_optdata = np.loadtxt(self.ds.attrs["filenameopt"], skiprows=skip_header_lines, dtype='float')
        except OSError:
            print('ERROR: HAWCStab2 opt file %s not found! Abort!' % self.ds.attrs["filenameopt"])
            return

        self.ds.coords["operating_parameter"] = ['wind speed [m/s]', 'pitch [deg]', 'rot. speed [rpm]', 'aero power [kw]', 'aero thrust [kn]']
        self.ds["operating_points"] = (["operating_point_ID", "operating_parameter"],
                                    HS2_optdata)

    def read_data(self):
        self.read_cmb_data()
        self.read_amp_data()
        self.read_opt_data()



########
# Basic Turbine Classes
########
class SubstructureDataClass(object):
    """ Main class for substructure data

    Attributes:
        bodies(list) : list of element properties of type of a body
        opstate(list): list of operational state data
    """
    def __init__(self):
        super(SubstructureDataClass, self).__init__()

        # define list for data
        self.bodies  = []
        self.opstate = {}

    def numbody(self):
        return len(self.bodies)


class BodyDataClass(object):
    """Main class for body element data.

    Attributes:
        s(ndarry) :(N,1) arc length position of end nodes of an element
    """
    def __init__(self):
        super(BodyDataClass, self).__init__()

        # define list for data
        self.s = None

    def numele(self):
        if not self.s is None:
            return len(self.s)
        else:
            return 0


class OpstatesClass(object):
    """ Main class for operational point data

    Attributes:
        bodies(list) : list of bodies
    """
    def __init__(self):
        super(OpstatesClass, self).__init__()

        # define list for data
        self.bodies = []

    def num(self):
        if not self.bodies is None:
            return len(self.bodies)
        else:
            return 0

class ModesClass(object):
    """ Main class for operational point data modes

    Attributes:
        modes(list) : list of modes
    """
    def __init__(self):
        super(ModesClass, self).__init__()

        # define list for data
        self.modes = []

    def num(self):
        if not self.modes is None:
            return len(self.modes)
        else:
            return 0

class ModeClass(object):
    """ Main class for operational point data modes

    Attributes:
        modes(list) : list of modes
    """
    def __init__(self):
        super(ModeClass, self).__init__()

        # define data
        self.ua0 = None
        self.ua1 = None
        self.ub1 = None

    #~ def num(self):
        #~ if not self.bodies is None:
            #~ return len(self.bodies)
        #~ else:
            #~ return 0

#########
#
#########
class HS2BINReader(object):
    """Extract mode shapes out of HAWCStab2 binary files.

    The HAWCStab2 model is set up hierarchically in this way:

    .. code-block:: text

        TURBINE
            |
            --> substructure i
                    |
                    |
                    --> bodies
                    |   |
                    |   --> body ii
                    |   |        |
                    |   |        --> body data s (arc position for each element)
                    |   |
                    |   --> body ii + 1
                    |       |
                    |       --> body data s (arc position for each element, 1d array)
                    |
                    --> opstate jj (states, dictionary)
                        |
                        --> bodies (list)
                            |
                            --> body jjj
                                |
                                --> mode jjjj
                                |   |
                                |   --> ua0 (2d array)
                                |
                                --> mode jjjj + 1
                                    |
                                    --> ua0 (2d array)

    Matlab struct: self.substructure[i_subs].opstate[istate].body_result(ibody).mode(imode).ua0

    Attributes:
        substructure(list)      : list of substructures present in a turbine
        num_modes(int)          : number of modes stored in the binary file
        num_steps(int)          : number of state points e.g. wind steps/ rpm steps
        operational_data(ndarry): (N,3) map of operational data
                                  i = operation point, j = 0 -> wind speed, j = 1 -> pitch, j = 2 -> power
        __offset(int)           : current offset of bytes in bin file, position in file/cached string
        __buff(bytes)           : cached binary file
        __num_DOF(int)          : parameter for the number of DOFs = u_x, u_y, u_z, theta_x, theta_y, theta_z

    """

    def __init__(self, file: str, parent=None):
        """
        Args:
            file(str): file name of the bin file
        """
        super(HS2BINReader, self).__init__()

        self.__file = file

        # init attributes
        self.substructure     = []
        self.num_modes        = 0
        self.num_steps        = 0
        self.operational_data = None
        self.__offset         = 0
        self.__num_DOF        = 6

        # read the binary into the buffer
        self.__read_file()

        # read the turbine data from buffer
        self.__read_turbine()

        # read the operational modal state data from buffer
        # these data follow directly the turbine data
        self.__read_opstate()

    ###
    # private methods
    def __read_file(self):
        """reads the bin file as binary data into a buffer object
        """
        with open(self.__file, 'br') as f:
            self.__buff = f.read()


    def __read_data(self, dtype, count: int):
        """
        Args:
            dtype()   : numpy data type
            count(int): number of byted to read
        """
        data = None

        num_bytes = np.frombuffer(self.__buff, dtype=np.int32, count=1, offset=self.__offset).squeeze()
        #~ print(num_bytes)

        # offset the first 32bit int == 4 bytes
        self.__offset += 4

        # decide on data type
        current_dtype = None
        byte_offset   = None
        if dtype == int:
            if num_bytes == 4*count:
                # 32 bit int
                current_dtype = np.int32
                byte_offset   = 4
            elif num_bytes == 8*count:
                # 64 bit int
                current_dtype = np.int64
                byte_offset   = 8
            elif num_bytes == 16*count:
                # 128 bit int
                current_dtype = np.int128
                byte_offset   = 16
        elif dtype == float:
            if num_bytes == 4*count:
                # 32 bit real
                current_dtype = np.float32
                byte_offset   = 4
            elif num_bytes == 8*count:
                # 64 bit real
                current_dtype = np.float64
                byte_offset   = 8
            elif num_bytes == 16*count:
                # 128 bit real
                current_dtype = np.float128
                byte_offset   = 16

        # read the data
        data = np.frombuffer(self.__buff, dtype=current_dtype, count=count, offset=self.__offset)
        self.__offset += byte_offset * count

        # finally spool forward another 32 bits = 4 bytes
        self.__offset += 4

        return data.squeeze()


    def __read_turbine(self):
        """ read the hierarchical structure data and save
            it in internal data structure.
        """

        # read substructure
        num_subs = self.__read_data(dtype=int,count=1)
        for isub in range(num_subs):
            self.substructure.append(SubstructureDataClass())

            # read bodies
            num_bodies = self.__read_data(int,1)
            for ibody in range(num_bodies):
                self.substructure[isub].bodies.append(BodyDataClass())

                # read elements
                num_elements = self.__read_data(int, 1)
                self.substructure[isub].bodies[ibody].s = np.empty([num_elements])
                for iele in range(num_elements):
                    self.substructure[isub].bodies[ibody].s[iele] = self.__read_data(float,1)


    def __read_opstate(self):
        """read the modal operational state data from buffer
        """

        # read operation information
        opstate_info = self.__read_data(dtype=int,count=2)
        self.num_modes = opstate_info[0]
        self.num_steps = opstate_info[1]
        print(self.num_modes, self.num_steps)

        # read operation data map (N,3)
        self.operational_data = np.zeros([self.num_steps,3])

        # loop over states
        for i_state in range(self.num_steps):
            dummy = self.__read_data(dtype=float,count=1)
            self.operational_data[i_state,:] = self.__read_data(dtype=float,count=3)

            # loop over substructures
            for i_subs in range(self.numsubstr()):

                #
                self.substructure[i_subs].opstate[i_state] = OpstatesClass()

                # allocate data
                for i_body in range(self.substructure[i_subs].numbody()):
                    self.substructure[i_subs].opstate[i_state].bodies.append(ModesClass())

                # one have to know, which number the three-bladed substructure is!
                # This is not covering the general case! Be careful!
                if i_subs < 2:    # ground_fixed_substructure and rotating_axissym_substructure


                    # loop over modes
                    for i_mode in range(self.num_modes):


                        #loop over bodies
                        for i_body in range(self.substructure[i_subs].numbody()):
                            self.substructure[i_subs].opstate[i_state].bodies[i_body].modes.append(ModeClass())
                            num_elements = self.substructure[i_subs].bodies[i_body].numele()
                            count = 2*self.__num_DOF*(num_elements+1)
                            data = -self.__read_data(dtype=float,count=count)
                            self.substructure[i_subs].opstate[i_state].bodies[i_body].modes[i_mode].ua0 = data.reshape([2,int(data.size/2)]).T

                else:    # rotating_threebladed_substructure
                    # loop over modes
                    for i_mode in range(self.num_modes):


                        self.substructure[i_subs].opstate[i_state].bodies[i_body].modes.append(ModeClass())

                        #loop over bodies
                        for i_body in range(self.substructure[i_subs].numbody()):
                            self.substructure[i_subs].opstate[i_state].bodies[i_body].modes.append(ModeClass())
                            num_elements = self.substructure[i_subs].bodies[i_body].numele()

                            data = -self.__read_data(dtype=float,count=2*self.__num_DOF*(num_elements+1))
                            self.substructure[i_subs].opstate[i_state].bodies[i_body].modes[i_mode].ua0 = data.reshape([2,int(data.size/2)]).T
                            data = -self.__read_data(dtype=float,count=2*self.__num_DOF*(num_elements+1))
                            self.substructure[i_subs].opstate[i_state].bodies[i_body].modes[i_mode].ua1 = data.reshape([2,int(data.size/2)]).T
                            data = -self.__read_data(dtype=float,count=2*self.__num_DOF*(num_elements+1))
                            self.substructure[i_subs].opstate[i_state].bodies[i_body].modes[i_mode].ub1 = data.reshape([2,int(data.size/2)]).T



        #~ self.operational_data[0,:] = self.__read_data(dtype=float,count=3)

        # switch sign for pitch and convert to degree
        self.operational_data[:,1] = np.rad2deg(-self.operational_data[:,1])
        print(self.operational_data)


    ###
    # public methods
    def numsubstr(self):
        return len(self.substructure)


if __name__ == "__main__":
    mytest = HAWCStab2Data(r"./examples/data/modified.cmb",
                           r"./examples/data/modified.amp",
                           r"./examples/data/modified.opt")
    mytest.read_data()


    print("########## HAWCStab2 binary result reader ##########\n")
    file = "IWT_7.5-164_Rev-2.5.2_HS2_coarse.bin"
    MyTurbine = HS2BINReader(file)

    num_subs = MyTurbine.numsubstr()
    print("number of substructures:", num_subs)
    for i in range(num_subs):
        print(f"substructure {i+1}:")
        num_bodies = MyTurbine.substructure[i].numbody()
        print("    number of bodies       :", num_bodies)
        for ii in range(num_bodies):
            print(f"    body {ii+1}:")
            num_elements = MyTurbine.substructure[i].bodies[ii].numele()
            print("        number of elements     :", num_elements)
            print(f"        {MyTurbine.substructure[i].bodies[ii].s}")
