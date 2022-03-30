###########
#
# Lib for reading Bladed linearization results
#
###########

# global libs
import numpy as np

from data_template import AbstractLinearizationData
from pyBladed.results import BladedResult
from utilities import assure_unique_name, AEMode


class BladedLinData(AbstractLinearizationData):
    """ This is a class for handling Bladed linearization result data """
    
    def __init__(self, result_dir, result_prefix):
        super(BladedLinData, self).__init__()

        self.attrs["result_dir"] = result_dir
        self.attrs["result_prefix"] = result_prefix

    def read_data(self):
        """
        Read all available Campbell diagram data
        """
        print('Start reading Bladed data')

        bladed_result = BladedResult(self.attrs["result_dir"], self.attrs["result_prefix"])
        bladed_result.scan()

        self.read_op_data(bladed_result)
        self.read_coupled_modes(bladed_result)
        # self.read_additional_cmb_data(bladed_result)

    def read_op_data(self, bladed_result):
        """
        Read operational data
        Args:
            bladed_result (obj.): Bladed result reader object
        """
        windspeed = bladed_result['Nominal wind speed at hub position'].squeeze()
        pitch = bladed_result['Nominal pitch angle'].squeeze() * 180/np.pi
        rpm = bladed_result['Rotor speed'].squeeze() * (60 / (2*np.pi))
        power = bladed_result['Electrical power'].squeeze() / 10**3

        self.coords["operating_parameter"] = ['wind speed [m/s]', 'pitch [deg]', 'rot. speed [rpm]', 'Electrical power [kw]']
        self["operating_points"] = (["operating_point_ID", "operating_parameter"],
                                    np.array([windspeed.T, pitch.T, rpm.T, power.T]).T)

    def read_coupled_modes(self, bladed_result):
        """
        Read coupled data (mode tracked frequency and damping curves)
        Args:
            bladed_result (obj.): Bladed result reader object
        """
        frequency, frequency_metadata = bladed_result['Frequency (undamped)']
        damping, damping_metadata = bladed_result['Damping']
        damping = 100 * damping  # damping ratio in %
        mode_names_orig = damping_metadata['AXITICK']
        # make sure mode names are unique -> add numbers if identical names appear
        modes = []
        for mode_name in mode_names_orig:
            modes.append(AEMode(name=mode_name))

        # self.coords["mode_names"] = mode_names
        self["modes"] = (["mode_ID"], modes)
        self["frequency"] = (["operating_point_ID", "mode_ID"], frequency.squeeze())
        self["damping"] = (["operating_point_ID", "mode_ID"], damping.squeeze())

    def read_modal_participations(self, bladed_result):
        """
        Extract the participation factors from the .$shape file

        This method is not finished yet...
        """
        # this is a dictionary with a key for each operating point, a sub-key for each mode and lists for the
        # particip_mode_names, particip_amplitude and particip_phase
        campbell_data_participations = bladed_result['Campbell diagram participations']

        # CampbellViewer format = 3D array with # operating points, participation mode names, modes
        # One issue: a maximum of 10 participation mode names are give per mode per operating point. All other
        # participation modes are given a zero. The participation_factors_amp and participation_factors_phase are padded
        # for each new participation mode name

        participation_factors_amp = np.zeros((len(campbell_data_participations), 0, len(self["modes"])))
        participation_factors_phase = np.zeros((len(campbell_data_participations), 0, len(self["modes"])))
        # copy mode names as a first guess for participation mode names
        all_participation_mode_names = list()

        for op_ID, (op, op_data) in enumerate(campbell_data_participations.items()):
            for mode_name, mode_data in op_data.items():

                # todo: the mode name given in the shape file has to be linked to the mode name of the coupled modes
                # main problem: some mode names seem to disappear for some operating points. Is a one-to-one
                # with the coupled modes even possible?
                # Outdated -> mode_idx = self["mode_names"].values.index(mode_name)

                for particip_mode_iter, particip_mode_name in mode_data['particip_mode_names']:
                    if particip_mode_name not in all_participation_mode_names:
                        print('participation mode name (mode name in participation factor list): {}, could not yet '
                              'be found in the overall mode name list'.format(particip_mode_name))
                        all_participation_mode_names.append(particip_mode_name)
                        participation_factors_amp = np.pad(participation_factors_amp, ((0, 0), (0, 1), (0, 0)),
                                                           mode='constant', constant_values=0)
                        participation_factors_phase = np.pad(participation_factors_phase, ((0, 0), (0, 1), (0, 0)),
                                                             mode='constant', constant_values=0)

                    participation_factors_amp[
                        op_ID, all_participation_mode_names.index(particip_mode_name), mode_idx] = \
                        mode_data['particip_amplitude'][particip_mode_iter]
                    participation_factors_phase[
                        op_ID, all_participation_mode_names.index(particip_mode_name), mode_idx] = \
                        mode_data['particip_phase'][particip_mode_iter]

        #self["participation_modes"] = (["participation_mode_ID"], [AEMode(name=name) for name in all_participation_mode_names])
        #self["participation_factors_amp"] = (
        #    ["operating_point_ID", "participation_mode_names", "mode_names"], participation_factors_amp)
        #self["participation_factors_phase"] = (
        #    ["operating_point_ID", "participation_mode_names", "mode_names"], participation_factors_phase)

    def read_additional_cmb_data(self, bladed_result):
        """
        Read additional Campbell diagram data (participation factors)

        Data is parsed from the .$CM file, which contains a full participation decomposition of each Campbell diagram
        node. Downside is that I have to link each node to the correct tracked mode via the operating point, frequency
        and damping.

        It would have been better to use the .$shape file for this purpose -> TODO
        It turns out the .$shape also has some problems of its own.

        Args:
            bladed_result (obj.): Bladed result reader object
        """
        campbell_data = bladed_result['Campbell diagram participations']

        # for each mode, for each wind speed -> get frequency and damping from mode tracked result, find entry in
        # participation_info with same operating point (= rotational speed), frequency and damping

        rotspeeds = np.array(self['operating_points'].loc[:, "rot. speed [rpm]"]) * 2 * np.pi / 60

        # the number of modes in the participation factor data is variable.
        participation_factors_amp = np.zeros((rotspeeds.size, 0, len(self["modes"])))
        participation_factors_phase = np.zeros((rotspeeds.size, 0, len(self["modes"])))
        # copy mode names as a first guess for participation mode names
        participation_mode_names = list()

        for i_rs, rotspeed in enumerate(rotspeeds):
            for i_mode in range(len(self["modes"])):
                freq = float(self["frequency"].loc[i_rs, i_mode]) * 2 * np.pi
                damp = float(self["damping"].loc[i_rs, i_mode]) / 100

                idx_op_point = np.where(abs(np.array(campbell_data['participation_info']['omega']) - rotspeed) < 0.001)[
                    0]
                idx_freq = np.where(abs(np.array(campbell_data['participation_info']['freq']) - freq) < 0.001)[0]
                idx_damp = np.where(abs(np.array(campbell_data['participation_info']['damp']) - damp) < 0.001)[0]

                unique_idx = np.intersect1d(idx_op_point, np.intersect1d(idx_freq, idx_damp))

                if unique_idx.size == 0:
                    print('Bladed linearization participation factor data could not be linked to coupled mode data for '
                          'rotor speed = {} and mode name = {}'.format(rotspeed, self["modes"].values[i_mode].name))
                elif unique_idx.size > 1:
                    print('Bladed linearization participation factor data could not be UNIQUELY linked to coupled mode '
                          'data for rotor speed = {} and mode name = {}'.format(rotspeed, self["modes"].values[i_mode].name))
                else:
                    particip_str = campbell_data['participation_info']['particip_str'][unique_idx[0]]
                    for p_str in particip_str.strip(', ').split(','):  # first remove possible trailing ',' -> then split
                        sensor_mode_name = ' '.join(p_str.split()[:-2])
                        ampl = float(p_str.split()[-2][:-1]) / 100
                        phase = float(p_str.split()[-1][:-1])
                        if sensor_mode_name not in participation_mode_names:
                            print('Sensor mode name (mode name in participation factor list): {}, could not yet be found '
                                  'in the overall mode name list'.format(sensor_mode_name))
                            participation_mode_names.append(sensor_mode_name)
                            participation_factors_amp = np.pad(participation_factors_amp, ((0, 0), (0, 1), (0, 0)),
                                                               mode='constant', constant_values=0)
                            participation_factors_phase = np.pad(participation_factors_phase, ((0, 0), (0, 1), (0, 0)),
                                                                 mode='constant', constant_values=0)

                        participation_factors_amp[
                            i_rs, participation_mode_names.index(sensor_mode_name), i_mode] = ampl
                        participation_factors_phase[
                            i_rs, participation_mode_names.index(sensor_mode_name), i_mode] = phase

        self["participation_modes"] = (["participation_mode_ID"], [AEMode(name=name) for name in participation_mode_names])
        self["participation_factors_amp"] = (
        ["operating_point_ID", "participation_mode_ID", "mode_ID"], participation_factors_amp)
        self["participation_factors_phase"] = (
        ["operating_point_ID", "participation_mode_ID", "mode_ID"], participation_factors_phase)



if __name__ == "__main__":
    result_dir = r'./example_simple_bladed_data'
    result_prefix = 'lin1'
    Bladed_example = BladedLinData(result_dir, result_prefix)
    Bladed_example.read_data()
