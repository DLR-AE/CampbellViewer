from campbellviewer.interfaces.bladed import BladedLinData
import pytest

class TestInterfaceBladed(object):
    """Test for interface to Bladed results.
    """

    def test_scan_bladed_results(self, bladed_test_result_dir, bladed_test_result_prefix):
        """Simple test for scanning available Bladed result files (with pyBladed)
        """
        with pytest.raises(FileNotFoundError):
            _ = BladedLinData(bladed_test_result_dir, 'not_existing_prefix')

        bladed_data = BladedLinData(bladed_test_result_dir, bladed_test_result_prefix)
        bladed_result = bladed_data.scan_bladed_results()

        assert len(bladed_result.header_file_names) > 0

    def test_read_op_data(self, bladed_test_result_dir, bladed_test_result_prefix):
        """Simple test for reading operating data from a pyBladed BladedResult object
        """

        bladed_data = BladedLinData(bladed_test_result_dir, bladed_test_result_prefix)
        bladed_result = bladed_data.scan_bladed_results()

        bladed_data.read_op_data(bladed_result)

        assert bladed_data.ds['operating_points'].size > 1

    def test_read_coupled_modes(self, bladed_test_result_dir, bladed_test_result_prefix):
        """Simple test for reading coupled mode data from a pyBladed BladedResult object
        """

        bladed_data = BladedLinData(bladed_test_result_dir, bladed_test_result_prefix)
        bladed_result = bladed_data.scan_bladed_results()

        bladed_data.read_coupled_modes(bladed_result)

        assert bladed_data.ds['modes'].size > 1
        assert bladed_data.ds['frequency'].size > 1
        assert bladed_data.ds['damping'].size > 1

    def test_read_cmb_data(self, bladed_test_result_dir, bladed_test_result_prefix):
        """Simple test for reading detailed Campbell diagram data from a pyBladed BladedResult object
        """

        bladed_data = BladedLinData(bladed_test_result_dir, bladed_test_result_prefix)
        bladed_result = bladed_data.scan_bladed_results()

        bladed_data.read_op_data(bladed_result)
        bladed_data.read_coupled_modes(bladed_result)
        bladed_data.read_cmb_data(bladed_result)

        assert bladed_data.ds['participation_factors_amp'].size > 1
        assert bladed_data.ds['participation_factors_phase'].size > 1