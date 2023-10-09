"""
Module for reading Bladed linearization results.
"""

import numpy as np
import os
from pyBladed.results import BladedResult

from campbellviewer.data_storage.data_template import AbstractLinearizationData
from campbellviewer.utilities import AEMode


class BladedLinData(AbstractLinearizationData):
    """This is a class for handling Bladed linearization result data.

    Attributes:
        ds (xarray.Dataset): xarray Dataset containing all linearization data

    Args:
        result_dir: Path to directory with Bladed Linearization results
        result_prefix: Name of the Bladed output files
    """

    def __init__(self, result_dir: str=None, result_prefix: str=None):
        super(BladedLinData, self).__init__()

        self.ds.attrs["result_dir"] = result_dir
        self.ds.attrs["result_prefix"] = result_prefix

        if result_dir is not None and result_prefix is not None:
            self.ds.attrs["bladed_version"] = self.extract_bladed_version()

    def extract_bladed_version(self) -> str:
        """ Get the Bladed version from the header in the .$PJ file """
        with open(os.path.join(self.ds.attrs["result_dir"], self.ds.attrs["result_prefix"]+'.$PJ'), errors='ignore') as f:
            for line in f:
                if 'ApplicationVersion' in line:
                    version = line.split("\"")[1]
                    return version
        return None

    def scan_bladed_results(self) -> BladedResult:
        """ Scan the available Bladed results """
        bladed_result = BladedResult(self.ds.attrs["result_dir"], self.ds.attrs["result_prefix"])
        try:
            bladed_result.scan()
        except FileNotFoundError:
            print('WARNING: There are no result files in the same directory as the .$PJ file. So no Bladed results '
                  'can be loaded.')
            raise
        return bladed_result

    def read_data(self):
        """ Read all available Campbell diagram data. """

        bladed_result = self.scan_bladed_results()

        if int(self.ds.attrs["bladed_version"].split('.')[1]) <= 6:
            self.read_coupled_modes_pre4p7(bladed_result)
        elif 6 < int(self.ds.attrs["bladed_version"].split('.')[1]) <= 8:
            self.read_op_data_4p7_4p8(bladed_result)
            self.read_coupled_modes(bladed_result)
            if int(self.ds.attrs["bladed_version"].split('.')[1]) == 7:
                # v4.7 has the rotor harmonics ('Rotor speed (1P)' '2P' '3P' '4P' '5P' '6P' '9P' '12P') in the $02 file
                # -> remove them
                n = len(self.ds.mode_ID)
                self.ds = self.ds.drop_sel(mode_ID=[n-1, n-2, n-3, n-4, n-5, n-6, n-7, n-8])
            self.read_cmb_data(bladed_result)
        else:
            self.read_op_data(bladed_result)
            self.read_coupled_modes(bladed_result)
            self.read_cmb_data(bladed_result)

    def read_op_data(self, bladed_result: BladedResult):
        """ Read operational data

        Read the operational data from the BladedResult object and insert it in the xarray dataset

        Args:
            bladed_result: Bladed result reader object
        """
        windspeed = bladed_result['Nominal wind speed at hub position'].squeeze()
        pitch = np.array(bladed_result['Nominal pitch angle'].squeeze() * 180/np.pi)
        rpm = np.array(bladed_result['Rotor speed'].squeeze() * (60 / (2*np.pi)))
        power = np.array(bladed_result['Electrical power'].squeeze() / 10**3)

        # The operating points have to be put in an array with at least 2 dimensions, even if there is only 1 op point
        op_point_arr = np.array([windspeed.T, pitch.T, rpm.T, power.T]).T
        if op_point_arr.ndim == 1:
            op_point_arr = op_point_arr.reshape(1, op_point_arr.size)

        self.ds.coords["operating_parameter"] = ['wind speed [m/s]', 'pitch [deg]', 'rot. speed [rpm]', 'Electrical power [kw]']
        self.ds["operating_points"] = (["operating_point_ID", "operating_parameter"], op_point_arr)

    def read_coupled_modes(self, bladed_result: BladedResult):
        """ Read coupled data (mode tracked frequency and damping curves).

        Args:
            bladed_result: Bladed result reader object
        """
        frequency, frequency_metadata = bladed_result['Frequency (undamped)']
        damping, damping_metadata = bladed_result['Damping']
        damping = 100 * damping  # damping ratio in %
        mode_names_orig = damping_metadata['AXITICK']

        # It seems to happen that the number of mode names does not match the size of the frequency and damping array
        # add some random names for the last modes
        if len(mode_names_orig) < frequency.shape[1]:
            mode_names_orig = mode_names_orig + ['...'] * (frequency.shape[1] - len(mode_names_orig))

        # make sure mode names are unique -> add numbers if identical names appear
        modes = []
        for mode_name in mode_names_orig:
            modes.append(AEMode(name=mode_name))

        self.ds["modes"] = (["mode_ID"], modes)
        self.ds["frequency"] = (["operating_point_ID", "mode_ID"], frequency[:, :, 0])
        self.ds["damping"] = (["operating_point_ID", "mode_ID"], damping[:, :, 0])

    def read_cmb_data(self, bladed_result: BladedResult):
        """ Read Campbell diagram data (participation factors).

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
            bladed_result: Bladed result reader object
        """
        # coupled modes and operating points have to be read before
        if self.ds["modes"] is None:
            self.read_coupled_modes(bladed_result)
        if self.ds["operating_points"] is None:
            self.read_op_data(bladed_result)

        campbell_data, coupled_mode_names = bladed_result['Campbell diagram']

        if len(coupled_mode_names) != len(self.ds["modes"]):
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
        participation_factors_amp = np.zeros((len(self.ds.operating_point_ID),
                                              len(uncoupled_mode_names),
                                              len(self.ds["modes"])))
        participation_factors_phase = np.zeros((len(self.ds.operating_point_ID),
                                                len(uncoupled_mode_names),
                                                len(self.ds["modes"])))

        for i_mode, mode_cmb in enumerate(campbell_data):
            # CHECK THAT COUPLED MODE (MODE TRACK) (FILE .$CM) MATCHES WITH THE COUPLED MODE OUTPUT (FILE .$02)
            used_operating_points = np.where(self.ds["frequency"][:, i_mode].values != -1)[0]
            if -1 in self.ds["frequency"][:, 0].values:
                print('The tracked coupled mode is not complete for all operating points')

            if not np.allclose(np.array(mode_cmb['freq']),
                               self.ds["frequency"][used_operating_points, i_mode].values * 2 * np.pi, rtol=1e-02):
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

        self.ds["participation_modes"] = (
            ["participation_mode_ID"], [AEMode(name=name) for name in uncoupled_mode_names])
        self.ds["participation_factors_amp"] = (
            ["operating_point_ID", "participation_mode_ID", "mode_ID"], participation_factors_amp)
        self.ds["participation_factors_phase"] = (
            ["operating_point_ID", "participation_mode_ID", "mode_ID"], participation_factors_phase)

    def read_op_data_4p7_4p8(self, bladed_result: BladedResult):
        """ Read operational data from Bladed results made by v4.7 and v4.8.

        For these versions the operational data can not be directly obtained with pyBladed, but (normally) the wind
        speed will be available in the .%02 file and the rotor speed can be extracted from the .$CM file.
        So this method is a workaround specifically for these Bladed versions.

        Args:
            bladed_result: Bladed result reader object
        """
        for result in bladed_result.results:
            if result[-3:] == '%02':
                if bladed_result.results[result]['AXISLAB']	== 'Wind Speed':  # this seems to be the standard case
                    windspeed = np.array(bladed_result.results[result]['AXIVAL'])

                    # get the rotor speed from the .$CM file
                    campbell_data, _ = bladed_result['Campbell diagram']
                    all_mode_track_rpms = [test['omegas'] for test in campbell_data]
                    mode_track_lengths = [len(mode_track_rpm) for mode_track_rpm in all_mode_track_rpms]
                    if not np.all(np.array(mode_track_lengths) == mode_track_lengths[0]):
                        print('Not all mode tracks have the same length. The longest mode track will be used to get '
                              'the rotor speed operational conditions.')
                    rpm = np.array(all_mode_track_rpms[np.argmax(mode_track_lengths)])

                    if windspeed.size != rpm.size:
                        print('Wind speed vector obtained from .%02 does not have the same length as rotational speed '
                              'vector obtained from .$CM file. Rotational speeds from .$CM will be disregarded')
                        rpm = np.ones(windspeed.shape)

                elif bladed_result.results[result]['AXISLAB'] == 'Rotor Speed':
                    rpm = np.array(bladed_result.results[result]['AXIVAL']) * (60 / (2 * np.pi))
                    windspeed = np.ones(rpm.shape)

                self.ds.coords["operating_parameter"] = ['wind speed [m/s]', 'rot. speed [rpm]']
                self.ds["operating_points"] = (["operating_point_ID", "operating_parameter"],
                                               np.array([windspeed.T, rpm.T]).T)

    def read_coupled_modes_pre4p7(self, bladed_result: BladedResult):
        """ Read coupled modes vor Bladed versions <4.7

        The output of a Bladed Campbell Diagram Linearization is very different for versions <4.6. Some notable
        differences:

        - .$02 is an ascii file, instead of the standard binary format described by the .%02 file
        - The rotor speed is given in the .%02 file as AXIVAL/AXISLAB, there does not seem to be the possibility to
          get the other operational conditions (wind speed, etc.)
        - The .$CM file has some different conventions compared to the newer versions:

            - The points in the top section of the file are not organised by mode track -> operating point,
              but organised by operating point -> mode track.
            - Besides that not all points seem to reappear in the mode tracks in the bottom of the file.
            - There are no phase angles in the participation factors

        - There is the small bug that the Frequency value for the keyword VARIAB in the .%02 file is missing
          parentheses. Therefore PyBladed will not recognise it as an actual keyword.
        - The rotor harmonics are included as modes in the data (NaN damping)

        Therefore we only read the frequency/damping from the .$02 file and the rotor speed + mode names from the .%02
        file

        Args:
            bladed_result: Bladed result reader object
        """
        print('WARNING: Reading the participation factors for Bladed Campbell <4.7 results has not been implemented '
              'yet. (Because the format of the .$CM file differs from newer versions)')
        for result in bladed_result.results:
            if result[-3:] == '%02':

                # operating data -> only rotor speed seems to be available
                print('WARNING: Bladed Campbell <4.7 does not provide wind speed as operational condition. The '
                      'Campbell diagram can only be visualized vs. rotor speed.')
                rpm = np.array(bladed_result.results[result]['AXIVAL']) * (60 / (2 * np.pi))

                self.ds.coords["operating_parameter"] = ['rot. speed [rpm]']
                self.ds["operating_points"] = (["operating_point_ID", "operating_parameter"],
                                               np.array([rpm.T]).T)

                # The first 9 rotor harmonics (1P, 2P, etc.) are included in the data. Cut them away.
                shape = [x for x in reversed(bladed_result.results[result]['DIMENS'])]
                frequency = np.loadtxt(result[:-3] + '$02').reshape(shape)[:, :-9, 0]
                damping = np.loadtxt(result[:-3] + '$02').reshape(shape)[:, :-9, 1]
                mode_names_orig = bladed_result.results[result]['AXITICK']

                damping = 100 * damping  # damping ratio in %
                # make sure mode names are unique -> add numbers if identical names appear
                modes = []
                for mode_name in mode_names_orig:
                    modes.append(AEMode(name=mode_name))

                self.ds["modes"] = (["mode_ID"], modes)
                self.ds["frequency"] = (["operating_point_ID", "mode_ID"], frequency)
                self.ds["damping"] = (["operating_point_ID", "mode_ID"], damping)


if __name__ == "__main__":
    result_dir = r'./example_simple_bladed_data'
    result_prefix = 'lin1'
    Bladed_example = BladedLinData(result_dir, result_prefix)
    Bladed_example.read_data()
