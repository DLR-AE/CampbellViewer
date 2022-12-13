
import pytest

@pytest.fixture(autouse=True, scope='session')
def hs2_amp_file():
    return 'examples/data/hawcstab2/IEA15MW/aeroelastic_entire_turbine.amp'

@pytest.fixture(autouse=True, scope='session')
def hs2_cmb_file():
    return 'examples/data/hawcstab2/IEA15MW/aeroelastic_entire_turbine.cmb'

@pytest.fixture(autouse=True, scope='session')
def hs2_opt_file():
    return 'examples/data/hawcstab2/IEA15MW/operation_1_25_windspeed.opt'