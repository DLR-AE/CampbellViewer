"""
This module contains data storing classes
"""
# global libs
import xarray as xr
import h5py
import os

# local libs
from HAWCStab2_lib import HAWCStab2Data
from BladedLin_lib import BladedLinData
from utilities import assure_unique_name

class LinearizationDataWrapper(dict):
    """
    A wrapping class to store data of different linearization tools (f.ex. HAWCStab2, Bladed-lin,...) and different
    runs (f.ex. different turbine settings) in a uniform way
    """
    def add_data(self, name, tool, tool_specific_info=dict()):
        """
        Args:
            name (str): string identifier for this run
            tool (str): tool identifier
            tool_specific_info (dict): dictionary with specific info for the given tool

        Returns:
            updates self.data attribute with available/requested data

        Note:
            '&' can not be in the tool name key or dataset key
        """

        if tool == 'bladed-lin':
            if 'Bladed (lin.)' not in self:
                self['Bladed (lin.)'] = dict()
            self['Bladed (lin.)'][name] = BladedLinData(tool_specific_info['result_dir'], tool_specific_info['result_prefix'])
            self['Bladed (lin.)'][name].read_data()
        elif tool == 'hawcstab2':
            if 'HAWCStab2' not in self:
                self['HAWCStab2'] = dict()
            if name not in self['HAWCStab2']:
                self['HAWCStab2'][name] = HAWCStab2Data()
            for key, value in tool_specific_info.items():
                if key == 'filenamecmb':
                    self['HAWCStab2'][name].read_cmb_data(value, tool_specific_info['skip_header_CMB'])
                elif key == 'filenameamp':
                    self['HAWCStab2'][name].read_amp_data(value, tool_specific_info['skip_header_AMP'])
                elif key == 'filenameopt':
                    self['HAWCStab2'][name].read_opt_data(value, tool_specific_info['skip_header_OP'])
        else:
            raise NotImplementedError('Only reading of bladed and hawcstab2 data implemented.')

    def remove_data(self, tool, name):
        """
        Remove specified dataset
        Args:
            name (str): string identifier of the dataset that should be removed
        """
        try:
            del self[tool][name]
        except KeyError:
            print('Failed attempt to remove dataset which was not loaded')

    def save(self, fname='CampbellViewerDatabase.nc'):
        # IMPORTANT: the standard scipy netcdf backend does not support saving to a group and the h5netcdf engine
        # crashes for me...
        # netCDF4 has to be installed... (by default xarray will use netCDF4 if it is installed)

        for toolname in self:
            for datasetname, xr_dataset in self[toolname].items():
                if os.path.exists(fname):
                    xr_dataset.to_netcdf(fname, mode='a', group=toolname + '&' + datasetname)
                else:
                    xr_dataset.to_netcdf(fname, mode='w', group=toolname + '&' + datasetname)

    def load(self, fname='CampbellViewerDatabase.nc'):
        # xr.open_dataset can not automatically find all groups in a netCDF4 file. So first find the available
        # group names in the file, then load the xarray datasets

        if os.path.exists(fname):
            with h5py.File(fname, 'r') as f:
                group_names = list(f.keys())

            loaded_data = dict()
            # full_datasetname = toolname + '&' + datasetname
            for full_datasetname in group_names:
                toolname = full_datasetname.split('&')[0]
                datasetname = full_datasetname.split('&')[1]
                if toolname not in loaded_data:
                    loaded_data[toolname] = []
                loaded_data[toolname].append(datasetname)
                if toolname not in self:
                    self[toolname] = dict()
                if datasetname in self[toolname]:
                    # print('Careful! {} dataset will be overwritten'.format(toolname + ' ' + datasetname))
                    print('Datasetname {} was already in use in tool {}. The loaded dataset will be renamed'.format(datasetname, toolname))
                    datasetname = assure_unique_name(datasetname, self[toolname].keys())
                self[toolname][datasetname] = xr.open_dataset(fname, group=full_datasetname)
        else:
            print('REQUESTED DATABASE FILE {} was not found'.format(fname))
            loaded_data = dict()

        return loaded_data

