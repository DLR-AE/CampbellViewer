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
        self.read_cmb_data(bladed_result)

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

        self["modes"] = (["mode_ID"], modes)
        self["frequency"] = (["operating_point_ID", "mode_ID"], frequency.squeeze())
        self["damping"] = (["operating_point_ID", "mode_ID"], damping.squeeze())

    def read_cmb_data(self, bladed_result):
        """
        Read Campbell diagram data (participation factors)

        Data is parsed from the .$CM file, which contains all Campbell diagram data. This file contains frequency,
        damping and participation factor results for all coupled modes. Unfortunately, it can happen that a specific
        mode could not be found for some operating points. The only link between the freq/damp/part. factor
        data and the operating point is the rotational speed, which is not a unique identifier. Therefore we need the
        'coupled modes' results of the .$02 file, which contains frequency and damping progression for all operating
        points. In this format, the operating points which did not create a result for a specific mode get a -1 value,
        so it the link between the freq. and damping progression and the operating points is unique.

        Therefore a link with the frequency and damping progression of file .$02 is made to uniquely determine for
        which operating points the coupled mode of the .$CM file has valid entries.

        Args:
            bladed_result (obj.): Bladed result reader object
        """
        # coupled modes and operating points have to be read before
        if self["modes"] is None:
            self.read_coupled_modes(bladed_result)
        if self["operating_points"] is None:
            self.read_op_data(bladed_result)

        campbell_data, coupled_mode_names = bladed_result['Campbell diagram']

        if len(coupled_mode_names) != len(self["modes"]):
            print('! Number of coupled modes  from .$CM file does not match with number of coupled modes from .$02 file')
            return

        # obtain a list of all uncoupled modes in the bladed model. A list is given in the .$01 file. Unfortunately,
        # this list does not seem to be fully consistent with the naming of the uncoupled modes in the .$CM file...
        # So, instead all participation strings are read and all uncoupled mode names are gathered
        uncoupled_mode_names_with_duplicates = list()
        for i_mode, mode_cmb in enumerate(campbell_data):
            for particip_str in mode_cmb['particip_str']:
                for p_str in particip_str.strip(', ').split(','):
                    uncoupled_mode_names_with_duplicates.append(' '.join(p_str.split()[:-2]))
        uncoupled_mode_names = list(dict.fromkeys(uncoupled_mode_names_with_duplicates))

        # initialize matrices for participation factors amplitude and phase
        participation_factors_amp = np.zeros((len(self.operating_point_ID), len(uncoupled_mode_names), len(self["modes"])))
        participation_factors_phase = np.zeros((len(self.operating_point_ID), len(uncoupled_mode_names), len(self["modes"])))

        for i_mode, mode_cmb in enumerate(campbell_data):
            # CHECK THAT COUPLED MODE (MODE TRACK) (FILE .$CM) MATCHES WITH THE COUPLED MODE OUTPUT (FILE .$02)
            used_operating_points = np.where(self["frequency"][:, i_mode].values != -1)[0]
            if -1 in self["frequency"][:, 0].values:
                print('The tracked coupled mode is not complete for all operating points')

            if not np.allclose(np.array(mode_cmb['freq']), self["frequency"][used_operating_points, i_mode].values * 2 * np.pi, rtol=1e-02):
                print('\nThe frequencies of the mode read from the .$CM file do not match with the frequencies from the '
                      'coupled modes in the .$02 file')

            # ADD THE PARTICIPATION DATA
            for particip_str, operating_point_id in zip(mode_cmb['particip_str'], used_operating_points):
                for p_str in particip_str.strip(', ').split(','):  # first remove possible trailing ',' -> then split
                    uncoupled_mode_name = ' '.join(p_str.split()[:-2])
                    ampl = float(p_str.split()[-2][:-1]) / 100
                    phase = float(p_str.split()[-1][:-1])

                    if uncoupled_mode_name not in uncoupled_mode_names:
                        print('Uncoupled mode name in the participation string (from .$CM file): {}, could not be found '
                              'in the overall list of uncoupled mode names (from .$01 file)'.format(uncoupled_mode_name))
                    else:
                        participation_factors_amp[
                            operating_point_id, uncoupled_mode_names.index(uncoupled_mode_name), i_mode] = ampl
                        participation_factors_phase[
                            operating_point_id, uncoupled_mode_names.index(uncoupled_mode_name), i_mode] = phase

        self["participation_modes"] = (
            ["participation_mode_ID"], [AEMode(name=name) for name in uncoupled_mode_names])
        self["participation_factors_amp"] = (
            ["operating_point_ID", "participation_mode_ID", "mode_ID"], participation_factors_amp)
        self["participation_factors_phase"] = (
            ["operating_point_ID", "participation_mode_ID", "mode_ID"], participation_factors_phase)


if __name__ == "__main__":
    result_dir = r'./example_simple_bladed_data'
    result_prefix = 'lin1'
    Bladed_example = BladedLinData(result_dir, result_prefix)
    Bladed_example.read_data()
