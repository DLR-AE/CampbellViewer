from campbellviewer.interfaces.hawcstab2 import HAWCStab2Data


class TestInterfaceHawcStab2(object):
    """Test for interfaces with HAWCStab2 files.
    """

    def test_read_amp(self, hs2_amp_file):
        """Simple test for reading .amp files
        """

        hs2_data = HAWCStab2Data()

        hs2_data.read_amp_data(filenameamp=hs2_amp_file)

        assert hs2_data.ds['participation_factors_amp'].size > 1


    def test_read_cmb(self, hs2_cmb_file):
        """Simple test for reading .cmb files
        """

        hs2_data = HAWCStab2Data()

        hs2_data.read_cmb_data(filenamecmb=hs2_cmb_file)

        assert hs2_data.ds['frequency'].size > 1
        assert hs2_data.ds['damping'].size > 1


    def test_read_opt(self, hs2_opt_file):
        """Simple test for reading .opt files
        """

        hs2_data = HAWCStab2Data()

        hs2_data.read_opt_data(filenameopt=hs2_opt_file)

        assert hs2_data.ds['operating_points'].size > 1
