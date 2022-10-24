"""
This module contains data storing classes
"""
# Global libs
import xarray as xr
from netCDF4 import Dataset
import os
import copy

# Local libs
from campbellviewer.interfaces.hawcstab2 import HAWCStab2Data
from campbellviewer.interfaces.bladed import BladedLinData
from campbellviewer.data_storage.data_template import AbstractLinearizationData
from campbellviewer.utilities import assure_unique_name, AEMode


class LinearizationDataWrapper(dict):
    """
    A wrapping class to store data of different linearization tools (f.ex. HAWCStab2, Bladed-lin,...) and different
    runs (f.ex. different turbine settings) in a uniform way
    """
    def add_data(self, name, tool, tool_specific_info={}):
        """
        Args:
            name (str): string identifier for this run
            tool (str): tool identifier
            tool_specific_info (dict): dictionary with specific info for the given tool (e.g. which files have to be
                used to load data)

        Returns:
            updates self.data attribute with available/requested data

        Note:
            '&' can not be in the tool name key or dataset key
        """

        if tool == 'bladed-lin':
            if 'Bladed (lin.)' not in self:
                self['Bladed (lin.)'] = {}
            self['Bladed (lin.)'][name] = BladedLinData(tool_specific_info['result_dir'], tool_specific_info['result_prefix'])
            self['Bladed (lin.)'][name].read_data()

        elif tool == 'hawcstab2':
            if 'HAWCStab2' not in self:
                self['HAWCStab2'] = {}
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

    def remove_data(self, branch):
        """
        Remove data from the database

        Args:
            branch (list): list with mode_idx, dataset, tool that have to be removed. This list will have length 1 if
                a tool has to be removed. It will have length 2 if a dataset has to be removed. And it will have length
                3 if modes have to be removed.
                Examples: branch = ['dataset_name', 'tool_name'] or branch = [[0, 1, 3], 'dataset_name', 'tool_name']
        """
        if len(branch) == 1:
            del self[branch[0]]
        elif len(branch) == 2:
            del self[branch[1]][branch[0]]
        elif len(branch) == 3:
            # I don't know how to do this without having to give back the modified
            # database (so just database[...][...].remove_modes())
            self[branch[2]][branch[1]].ds = self[branch[2]][branch[1]].remove_modes(branch[0])
        else:
            print('The list provided can only have 1, 2, or 3 values. Nothing removed from database')


    def save(self, fname='CampbellViewerDatabase.nc'):
        """
        Save the database to a file.

        Xarray has the functionality to save datasets in netcdf format. The total database dictionary is saved by
        saving each key-value pair as a separate group to the netcdf file.

        IMPORTANT: the standard scipy netcdf backend does not support saving to a group
                -> netCDF4 has to be installed. (by default xarray will use netCDF4 if it is installed)

        Args:
            fname (str, optional): file to which database will be saved
        """
        for toolname in self:
            for datasetname, dataset_obj in self[toolname].items():
                # The xarray datasets can be saved using the build-in to_netcdf methods of xarray.
                # With one exception: the AEMode class -> xarray cannot serialize arbitrary Python objects
                # Therefore each AEMode instance is converted to a list with its attributes.
                xr_dataset_to_save = copy.deepcopy(dataset_obj.ds)
                for ii, ae_mode in enumerate(xr_dataset_to_save.modes.values):
                    xr_dataset_to_save['modes'][ii] = ae_mode.to_plain_text()
                for ii, ae_mode in enumerate(xr_dataset_to_save.participation_modes.values):
                    xr_dataset_to_save['participation_modes'][ii] = ae_mode.to_plain_text()

                if os.path.exists(fname):
                    xr_dataset_to_save.to_netcdf(fname, mode='a', group=toolname + '&' + datasetname)
                else:
                    xr_dataset_to_save.to_netcdf(fname, mode='w', group=toolname + '&' + datasetname)


    def load(self, fname='CampbellViewerDatabase.nc'):
        """
        Load the database from a file.

        xr.open_dataset can not automatically find all groups in a netCDF4 file. So we first find the available
        group names in the file, then load the xarray datasets.

        Args:
            fname (str, optional): file from which the database will be loaded
        """
        if os.path.exists(fname):
            rootgrp = Dataset(fname, "r")
            group_names = list(rootgrp.groups)

            loaded_data = dict()
            # full_datasetname = toolname + '&' + datasetname
            for full_datasetname in group_names:
                toolname = full_datasetname.split('&')[0]
                datasetname = full_datasetname.split('&')[1]
                if toolname not in loaded_data:
                    loaded_data[toolname] = []
                if toolname not in self:
                    self[toolname] = dict()
                if datasetname in self[toolname]:
                    print('Datasetname {} was already in use in tool {}. The loaded dataset will be renamed'.format(datasetname, toolname))
                    datasetname = assure_unique_name(datasetname, self[toolname].keys())
                loaded_data[toolname].append(datasetname)

                if toolname == 'HAWCStab2':
                    self[toolname][datasetname] = HAWCStab2Data()
                elif toolname == 'Bladed (lin.)':
                    self[toolname][datasetname] = BladedLinData()
                else:
                    print('{} data is unknown, a standard AbstractLinearizationData object will be made'.format(toolname))
                    self[toolname][datasetname] = AbstractLinearizationData()
                self[toolname][datasetname].ds = xr.open_dataset(fname, group=full_datasetname)

                # store the database path name as a xarray dataset attribute
                self[toolname][datasetname].ds.attrs["database_file"] = fname

                # convert AEModes saved as plain text to AEMode objects
                for ii, ae_mode in enumerate(self[toolname][datasetname].ds['modes'].values):
                    self[toolname][datasetname].ds['modes'][ii] = AEMode.from_plain_text(ae_mode)
                for ii, ae_mode in enumerate(self[toolname][datasetname].ds['participation_modes'].values):
                    self[toolname][datasetname].ds['participation_modes'][ii] = AEMode.from_plain_text(ae_mode)
        else:
            print('REQUESTED DATABASE FILE {} was not found'.format(fname))
            loaded_data = dict()

        return loaded_data
