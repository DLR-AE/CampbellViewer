# """
# #######################################################################################
# This file is part of CampbellViewer.

# CampbellViewer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# CampbellViewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with CampbellViewer. If not, see <http://www.gnu.org/licenses/>
# #######################################################################################

# --------------------------------------------------------------------------------------
# Simple postprocessing GUI for wind turbine linearization results.


# Purpose: Create Interactive Campbell-Plots, participation plots, mode visualizations, etc.

# author: J.Rieke - Nordex Energy GmbH
#         H.Verdonck - DLR
#         O.Hach - DLR

# --------------------------------------------------------------------------------------
# There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# --------------------------------------------------------------------------------------
# """

import sys
import numpy as np
import copy

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout, QMessageBox, QWidget, QDialog
from PyQt5.QtWidgets import QLineEdit, QFileDialog, QPushButton, QLabel, QSpinBox, QCheckBox, QComboBox, QTreeView
from PyQt5.QtGui  import QIcon, QDoubleValidator
from PyQt5.QtCore import QFileInfo, Qt, QItemSelectionModel

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure
import mplcursors

from campbellviewer.datatree_model import TreeModel
from campbellviewer.settings.globals import database, view_cfg
from campbellviewer.settings.view import MPLLinestyle
from campbellviewer.utilities import assure_unique_name

matplotlib.use("Qt5Agg")
matplotlib.rcParams['hatch.color']     = 'grey'
matplotlib.rcParams['hatch.linewidth'] = 0.2

# activate clipboard --> not working currently!
#~ matplotlib.rcParams['toolbar'] = 'toolmanager'

####
# Popup setting dialogs
####
class SettingsPopup(QDialog):
    """ Base class for a QDialog popup window where the user can modify settings """
    def __init__(self):
        QDialog.__init__(self)

    def update_settings(self):
        """ Update the settings based on the input given by the user """
        pass

    def get_settings(self):
        """ Get the settings inserted by the user in this popup """
        pass

    def ok_click(self):
        """ User clicked ok button -> update settings -> close popup """
        self.update_settings()
        self.close_popup()

    def close_popup(self):
        """ Close popup """
        self.close()

class SettingsPopupDataSelection(SettingsPopup):
    """
    Class for popup-window to select data

    Attributes:
        selected_tool: A string indicating which tool the data will come from, HAWCStab2 or Bladed (lin.)
        dataset_name: Name of the dataset
        __ToolSelection: QCombobox to select tool
        __DataSetName: QLineEdit to insert dataset name as string
    """
    def __init__(self):
        """ Initializes data selection popup """
        super(SettingsPopupDataSelection, self).__init__()

        # define initial tool and dataset
        self.selected_tool = 'HAWCStab2'
        self.dataset_name = 'default'

        self.setWindowTitle("Tool selection")
        popup_layoutV = QVBoxLayout(self)
        popup_layoutTool = QHBoxLayout(self)
        popup_layoutName = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)

        self.__ToolSelection = QComboBox()
        self.__ToolSelection.addItems(['HAWCStab2', 'Bladed (lin.)'])
        popup_layoutTool.addWidget(QLabel('Select which data type will be loaded (default=''HAWCStab2''):'))
        popup_layoutTool.addWidget(self.__ToolSelection)

        self.__DataSetName = QLineEdit('default')
        popup_layoutName.addWidget(QLabel('Specify dataset name:'))
        popup_layoutName.addWidget(self.__DataSetName)

        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.ok_click)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.close_popup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layoutTool)
        popup_layoutV.addLayout(popup_layoutName)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def get_settings(self):
        """
        Gives the current selected settings

        Returns:
          selected_tool: string indicating from which tool data will be selected
          dataset_name: string with user specified name for the dataset
        """
        return self.selected_tool, self.dataset_name

    def update_settings(self):
        """ Updates the settings based on the current content of the popup """
        self.selected_tool = self.__ToolSelection.currentText()
        self.dataset_name = self.__DataSetName.text()
        self.close()

    def ClosePopup(self):
        self.close()

class SettingsPopupHS2Headers(SettingsPopup):
    """
    Class for popup-window to modify the header lines in Campbell, Amplitude and operational data file which serve as
    input for HAWCStab2

    Attributes:
        settingsCMB: Number of header lines in the .cmb file
        settingsAMP: Number of header lines in the .amp file
        settingsOP: Number of header lines in the .opt file
        __headerLinesCMBE: QSpinBox to select the number of header lines in .cmb file
        __headerLinesAMPE: QSpinBox to select the number of header lines in .amp file
        __headerLinesOPE: QSpinBox to select the number of header lines in .opt file
    """
    def __init__(self, settingsCMB, settingsAMP, settingsOP):
        """
        Initializes popup for HAWCStab2 input file header line definitions

        Args:
          settingsCMB: integer for initial definition of the number of header lines in the .cmb file
          settingsAMP: integer for initial definition of the number of header lines in the .amp file
          settingsOP: integer for initial definition of the number of header lines in the .opt file
        """
        super(SettingsPopupHS2Headers, self).__init__()
        
        self.settingsCMB = settingsCMB
        self.settingsAMP = settingsAMP
        self.settingsOP = settingsOP
        self.setWindowTitle("Settings for Header Lines")
        popup_layoutV = QVBoxLayout(self)
        popup_layoutHCMB = QHBoxLayout(self)
        popup_layoutHAMP = QHBoxLayout(self)
        popup_layoutHOP = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)

        headerLinesCMBL = QLabel('Number of header lines in Campbell file:')
        headerLinesAMPL = QLabel('Number of header lines in Amplitude file:')
        headerLinesOPL = QLabel('Number of header lines in Operational data file:')
        self.__headerLinesCMBE = QSpinBox()
        self.__headerLinesAMPE = QSpinBox()
        self.__headerLinesOPE = QSpinBox()
        self.__headerLinesCMBE.setValue(self.settingsCMB)
        self.__headerLinesAMPE.setValue(self.settingsAMP)
        self.__headerLinesOPE.setValue(self.settingsOP)
        popup_layoutHCMB.addWidget(headerLinesCMBL)
        popup_layoutHCMB.addWidget(self.__headerLinesCMBE)
        popup_layoutHAMP.addWidget(headerLinesAMPL)
        popup_layoutHAMP.addWidget(self.__headerLinesAMPE)
        popup_layoutHOP.addWidget(headerLinesOPL)
        popup_layoutHOP.addWidget(self.__headerLinesOPE)

        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.ok_click)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.close_popup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layoutHCMB)
        popup_layoutV.addLayout(popup_layoutHAMP)
        popup_layoutV.addLayout(popup_layoutHOP)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()
        
    def get_settings(self):
        """
        Gives the current selected settings

        Returns:
          settingsCMB: user-defined number of header lines in the .cmb file
          settingsAMP: user-defined number of header lines in the .amp file
          settingsOP: user-defined number of header lines in the .opt file
        """
        return self.settingsCMB, self.settingsAMP, self.settingsOP

    def update_settings(self):
        """ Updates the settings based on the current content of the popup """
        self.settingsCMB = self.__headerLinesCMBE.value()
        self.settingsAMP = self.__headerLinesAMPE.value()  
        self.settingsOP = self.__headerLinesOPE.value()


class SettingsPopupAMP(SettingsPopup):
    """
    Class for popup-window to select for which mode the modal participations have to be shown

    Attributes:
        success: Boolean indicating if user wants to continue -> if the user presses cancel -> success = false
        settingsAMPmode: integer indicating which mode has to be used for the modal participation plot
        selected_tool: string indicating from which tool the data has to be shown
        selected_dataset: string indicating from which dataset the data has to be shown
        __ToolSelection: QComboBox to select the tool for the modal participation plot
        __DataSetSelection: QComboBox to select the dataset for the modal participation plot
        __AMPmode: QComboBox to select the mode for the modal participation plot
    """
    def __init__(self):
        """ Initializes popup for mode selection for modal participation plot """
        super(SettingsPopupAMP, self).__init__()

        self.success = False
        self.settingsAMPmode = None
        self.selected_tool = list(view_cfg.active_data.keys())[0]
        self.selected_dataset = list(view_cfg.active_data[self.selected_tool].keys())[0]
        self.setWindowTitle("Set mode number for Amplitude plot")
        popup_layoutV = QVBoxLayout(self)
        popup_layoutAMPmode = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)
        popup_layoutDS = QHBoxLayout(self)
        popup_layouttool = QHBoxLayout(self)

        self.__ToolSelection = QComboBox()
        self.__ToolSelection.addItems(view_cfg.active_data.keys())
        self.__ToolSelection.currentTextChanged.connect(self.update_dataset_choice)
        popup_layouttool.addWidget(QLabel('Select tool:'))
        popup_layouttool.addWidget(self.__ToolSelection)

        self.__DataSetSelection = QComboBox()
        self.__DataSetSelection.addItems(view_cfg.active_data[self.selected_tool].keys())
        self.__DataSetSelection.currentTextChanged.connect(self.update_mode_choice)
        popup_layoutDS.addWidget(QLabel('Select dataset:'))
        popup_layoutDS.addWidget(self.__DataSetSelection)

        self.__AMPmode = QComboBox()
        self.__AMPmode.addItems(
            [str(database[self.selected_tool][self.selected_dataset].ds.modes.values[mode_id].name) for mode_id in
             view_cfg.active_data[self.selected_tool][self.selected_dataset]])
        popup_layoutAMPmode.addWidget(QLabel('Amplitude mode to plot:'))
        popup_layoutAMPmode.addWidget(self.__AMPmode)
        
        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.ok_click)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.cancel)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layouttool)
        popup_layoutV.addLayout(popup_layoutDS)
        popup_layoutV.addLayout(popup_layoutAMPmode)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def update_dataset_choice(self):
        """ Update the options for the dataset selection based on the currently selected tool """
        self.__DataSetSelection.clear()
        self.__DataSetSelection.addItems(view_cfg.active_data[self.__ToolSelection.currentText()].keys())

    def update_mode_choice(self):
        """ Update the options for the mode selection based on the currently selected tool and dataset """
        self.__AMPmode.clear()
        if self.__DataSetSelection.currentText():
            self.__AMPmode.addItems(
                [str(database[self.__ToolSelection.currentText()][self.__DataSetSelection.currentText()].ds.modes.values[mode_id].name)
                 for mode_id in view_cfg.active_data[self.__ToolSelection.currentText()][self.__DataSetSelection.currentText()]])

    def get_settings(self):
        """
        Gives the current selected settings

        Returns:
          success: boolean indicating if the user wants to continue with the selection
          selected_tool: string indicating which tool will be used
          selected_dataset: string indicating which dataset will be used
          settings_AMPmode: string indicating which mode index will be used
        """
        return self.success, self.selected_tool, self.selected_dataset, self.settingsAMPmode

    def update_settings(self):
        """ Updates the settings based on the current content of the popup """
        self.success = True
        self.selected_tool = self.__ToolSelection.currentText()
        self.selected_dataset = self.__DataSetSelection.currentText()
        self.settingsAMPmode = view_cfg.active_data[self.selected_tool][self.selected_dataset][int(self.__AMPmode.currentIndex())]

    def cancel(self):
        """ Action if user presses cancel. Do not continue with the modal participation plotting. """
        self.success = False
        self.close()


class SettingsPopupAEMode(SettingsPopup):
    """
    Class for popup-window to modify the description of an aeroelastic mode

    Attributes:
        name: string with full name of the aeroelastic mode
        symmetry_type: string with indication of the symmetry type of the aeroelastic mode
        whirl_type: string with indication of the whirling type of the aeroelastic mode
        wt_component: string with indication of the main wind turbine component of the aeroelastic mode
        __NameSelection: QLineEdit to insert the full name of the mode
        __SymTypeSelection: QComboBox to select the symmetry type of the mode
        __WhirlTypeSelection: QComboBox to select the whirling type of the mode
        __WTCompSelection: QComboBox to select the main wind turbine component of the mode
    """
    def __init__(self, name, symmetry_type, whirl_type, wt_component):
        """
        Initializes popup for modification of an aeroelastic mode description

        Args:
          name: full name of the aeroelastic mode
          symmetry_type: symmetry type of the aeroelastic mode
          whirl_type: whirl type of the aeroelastic mode
          wt_component: wind turbine component of the aeroelastic mode
        """
        super(SettingsPopupAEMode, self).__init__()

        self.name = name
        self.symmetry_type = symmetry_type
        self.whirl_type = whirl_type
        self.wt_component = wt_component
        self.setWindowTitle("Modify mode description")

        popup_layoutV = QVBoxLayout(self)
        popup_layoutNAME = QHBoxLayout(self)
        popup_layoutSYM = QHBoxLayout(self)
        popup_layoutWHIRL = QHBoxLayout(self)
        popup_layoutWT = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)

        self.__NameSelection = QLineEdit(self.name)
        popup_layoutNAME.addWidget(QLabel('Mode name:'))
        popup_layoutNAME.addWidget(self.__NameSelection)

        self.__SymTypeSelection = QComboBox()
        self.__SymTypeSelection.addItems(['Symmetric', 'Asymmetric'])
        self.__SymTypeSelection.setEditable(True)
        self.__SymTypeSelection.setCurrentText(self.symmetry_type)
        popup_layoutSYM.addWidget(QLabel('Symmetry type:'))
        popup_layoutSYM.addWidget(self.__SymTypeSelection)

        self.__WhirlTypeSelection = QComboBox()
        self.__WhirlTypeSelection.addItems(['BW', 'FW', 'Sym'])
        self.__WhirlTypeSelection.setEditable(True)
        self.__WhirlTypeSelection.setCurrentText(self.whirl_type)
        popup_layoutWHIRL.addWidget(QLabel('Whirl type:'))
        popup_layoutWHIRL.addWidget(self.__WhirlTypeSelection)

        self.__WTCompSelection = QComboBox()
        self.__WTCompSelection.addItems(['tower', 'blade', 'drivetrain'])
        self.__WTCompSelection.setEditable(True)
        self.__WTCompSelection.setCurrentText(self.wt_component)
        popup_layoutWT.addWidget(QLabel('Wind turbine component:'))
        popup_layoutWT.addWidget(self.__WTCompSelection)

        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.ok_click)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.close_popup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layoutNAME)
        popup_layoutV.addLayout(popup_layoutSYM)
        popup_layoutV.addLayout(popup_layoutWHIRL)
        popup_layoutV.addLayout(popup_layoutWT)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def get_settings(self):
        """
        Gives the current selected settings

        Returns:
          name: user-defined full name of the aeroelastic mode
          symmetry_type: user-defined symmetry type of the aeroelastic mode
          whirl_type: user-defined whirl type of the aeroelastic mode
          wt_component: user-defined wind turbine component of the aeroelastic mode
        """
        return self.name, self.symmetry_type, self.whirl_type, self.wt_component

    def update_settings(self):
        """ Updates the settings based on the current content of the popup """
        self.name = self.__NameSelection.text()
        self.symmetry_type = self.__SymTypeSelection.currentText()
        self.whirl_type = self.__WhirlTypeSelection.currentText()
        self.wt_component = self.__WTCompSelection.currentText()


class SettingsPopupModeFilter(SettingsPopup):
    """
    Class for popup-window to filter aeroelastic modes

    Attributes:
        symmetry_type: string with indication of the symmetry type of the aeroelastic mode for the filter
        whirl_type: string with indication of the whirling type of the aeroelastic mode for the filter
        wt_component: string with indication of the main wind turbine component of the aeroelastic mode for the filter
        __SymTypeSelection: QComboBox to select the symmetry type of the mode for the filter
        __WhirlTypeSelection: QComboBox to select the whirling type of the mode for the filter
        __WTCompSelection: QComboBox to select the main wind turbine component of the mode for the filter
    """
    def __init__(self):
        """ Initializes popup to select a filter for the aeroelastic modes """
        super(SettingsPopupModeFilter, self).__init__()

        self.symmetry_type = 'all'
        self.whirl_type = 'all'
        self.wt_component = 'all'
        self.setWindowTitle("Filter modes")

        popup_layoutV = QVBoxLayout(self)
        popup_layoutSYM = QHBoxLayout(self)
        popup_layoutWHIRL = QHBoxLayout(self)
        popup_layoutWT = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)

        self.__SymTypeSelection = QComboBox()
        self.__SymTypeSelection.addItems(['all', 'Symmetric', 'Asymmetric'])
        self.__SymTypeSelection.setEditable(True)
        popup_layoutSYM.addWidget(QLabel('Only show this symmetry type:'))
        popup_layoutSYM.addWidget(self.__SymTypeSelection)

        self.__WhirlTypeSelection = QComboBox()
        self.__WhirlTypeSelection.addItems(['all', 'BW', 'FW', 'Sym'])
        self.__WhirlTypeSelection.setEditable(True)
        popup_layoutWHIRL.addWidget(QLabel('Only show this whirl type:'))
        popup_layoutWHIRL.addWidget(self.__WhirlTypeSelection)

        self.__WTCompSelection = QComboBox()
        self.__WTCompSelection.addItems(['all', 'tower', 'blade', 'drivetrain'])
        self.__WTCompSelection.setEditable(True)
        popup_layoutWT.addWidget(QLabel('Only show this wind turbine component:'))
        popup_layoutWT.addWidget(self.__WTCompSelection)

        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.ok_click)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.close_popup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layoutSYM)
        popup_layoutV.addLayout(popup_layoutWHIRL)
        popup_layoutV.addLayout(popup_layoutWT)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def get_settings(self):
        """
        Gives the current selected settings

        Returns:
          symmetry_type: user-defined symmetry type of the aeroelastic mode for filtering
          whirl_type: user-defined whirl type of the aeroelastic mode for filtering
          wt_component: user-defined wind turbine component of the aeroelastic mode for filtering
        """
        return self.symmetry_type, self.whirl_type, self.wt_component

    def update_settings(self):
        """ Updates the settings based on the current content of the popup """
        self.symmetry_type = self.__SymTypeSelection.currentText()
        self.whirl_type = self.__WhirlTypeSelection.currentText()
        self.wt_component = self.__WTCompSelection.currentText()


class SettingsPopupLinestyle(SettingsPopup):
    """
    Class for popup-window to set linestyle behaviour of matplotlib plot

    Attributes:
        main_window: QMainWindow which can be updated based on the user settings
        __CMSelection: QComboBox to select the colormap for the matplotlib plot
        __OverwriteSelection: QCheckBox to allow the user to overwrite the colormap with a user-defined list of colors
        __OverwriteListSelection: QLineEdit where the user can define a list of colors to overwrite the standard colormap
        __LSSelection: QLineEdit where the user can define a list of linestyles
        __LWSelection: QLineEdit to set the default linewidth size
        __MarkerSelection: QLineEdit where the user can define a list of marker types
        __MarkerSizeSelection: QLineEdit to set the default marker size
        __SDOSelection: QComboBox to define in which order the lines are diversified
            e.g. [1. Color, 2. Marker, 3. Linestyle] will first make lines with different colors, until all colors are
            used, then use new markers, until all markers are used, then use new linestyle
    """
    def __init__(self, main_window):
        """
        Initializes popup to set the default linestyle selection behaviour

        Args:
             main_window: QMainWindow which will be updated based on the settings
        """
        super(SettingsPopupLinestyle, self).__init__()

        self.main_window = main_window

        popup_layoutV = QVBoxLayout(self)
        popup_layoutCM = QHBoxLayout(self)
        popup_layoutLS = QHBoxLayout(self)
        popup_layoutMARKER = QHBoxLayout(self)
        popup_layoutLW = QHBoxLayout(self)
        popup_layoutMARKERSIZE = QHBoxLayout(self)
        popup_layoutCM2 = QHBoxLayout(self)
        popup_layoutSDO = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)

        self.__CMSelection = QComboBox()
        self.__CMSelection.addItems(['tab10', 'tab20', 'tab20b', 'tab20c', 'Pastel1', 'Pastel2', 'Paired',
                                     'Accent', 'Dark2', 'Set1', 'Set2', 'Set3'])
        self.__CMSelection.setCurrentText(view_cfg.ls.colormap)
        popup_layoutCM.addWidget(QLabel('Colormap:'), 1)
        popup_layoutCM.addWidget(self.__CMSelection, 1)

        self.__OverwriteSelection = QCheckBox()
        self.__OverwriteSelection.stateChanged.connect(self.override_colormap)
        self.__OverwriteListSelection = QLineEdit('r, g, b, y, c, m, k')
        self.override_colormap(Qt.Unchecked)
        popup_layoutCM2.addWidget(QLabel('Overwrite the standard colormap:'), 1)
        popup_layoutCM2.addWidget(self.__OverwriteSelection, 0.1)
        popup_layoutCM2.addWidget(self.__OverwriteListSelection, 0.9)

        # It would be better to have an editable QListWidget, but that would generate more code, so just a line edit for now
        # this line edit is very likely to give wrong input, this should be validated somewhere...
        self.__LSSelection = QLineEdit(','.join(view_cfg.ls.style_sequences['linestyle']))
        popup_layoutLS.addWidget(QLabel('Linestyle list:'), 1)
        popup_layoutLS.addWidget(self.__LSSelection, 1)

        self.__LWSelection = QLineEdit(str(view_cfg.ls.lw))
        self.onlyDouble = QDoubleValidator()
        self.__LWSelection.setValidator(self.onlyDouble)
        popup_layoutLW.addWidget(QLabel('Linewidth:'), 1)
        popup_layoutLW.addWidget(self.__LWSelection, 1)

        self.__MarkerSelection = QLineEdit(','.join(view_cfg.ls.style_sequences['marker']))
        popup_layoutMARKER.addWidget(QLabel('Marker list:'), 1)
        popup_layoutMARKER.addWidget(self.__MarkerSelection, 1)

        self.__MarkerSizeSelection = QLineEdit(str(view_cfg.ls.markersizedefault))
        self.__MarkerSizeSelection.setValidator(self.onlyDouble)
        popup_layoutMARKERSIZE.addWidget(QLabel('Marker size default:'), 1)
        popup_layoutMARKERSIZE.addWidget(self.__MarkerSizeSelection, 1)

        self.__SDOSelection = QComboBox()
        self.__SDOSelection.addItems(['1. Color, 2. Marker, 3. Linestyle',
                                      '1. Color, 2. Linestyle, 3. Marker',
                                      '1. Marker, 2. Color, 3. Linestyle',
                                      '1. Marker, 2. Linestyle, 3. Color',
                                      '1. Linestyle, 2. Color, 3. Marker',
                                      '1. Linestyle, 2. Marker, 3. Color'])
        popup_layoutSDO.addWidget(QLabel('Order in which linestyles are determined:'), 1)
        popup_layoutSDO.addWidget(self.__SDOSelection, 1)

        button_apply = QPushButton('Apply', self)
        button_apply.clicked.connect(self.update_settings)
        popup_layoutBttn.addWidget(button_apply)
        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.ok_click)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.close_popup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layoutCM)
        popup_layoutV.addLayout(popup_layoutCM2)
        popup_layoutV.addLayout(popup_layoutLS)
        popup_layoutV.addLayout(popup_layoutLW)
        popup_layoutV.addLayout(popup_layoutMARKER)
        popup_layoutV.addLayout(popup_layoutMARKERSIZE)
        popup_layoutV.addLayout(popup_layoutSDO)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def override_colormap(self, state):
        """
        Based on the state of self.__OverwriteSelection, either overwrite the self.__CMSelection or not

        Args:
            state: Qt.Checked or Qt.Unchecked to indicate if colormap will be overwritten by user-specified colormap
                list or not
        """
        if state == Qt.Checked:
            self.__CMSelection.clear()
            self.__OverwriteListSelection.setStyleSheet("QLineEdit{background : white;}")
            self.__OverwriteListSelection.setReadOnly(False)
        else:
            self.__CMSelection.addItems(
                ['tab10', 'tab20', 'tab20b', 'tab20c', 'Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1',
                 'Set2', 'Set3'])
            self.__CMSelection.setCurrentText(view_cfg.ls.colormap)
            self.__OverwriteListSelection.setStyleSheet("QLineEdit{background : grey;}")
            self.__OverwriteListSelection.setReadOnly(True)

    def update_settings(self):
        """ Updates the settings based on the current content of the popup """
        view_cfg.ls.colormap = self.__CMSelection.currentText()
        if self.__OverwriteSelection.checkState() == Qt.Checked:
            view_cfg.ls.overwrite_cm_color_sequence = self.__OverwriteListSelection.text().split(',')
        else:
            view_cfg.ls.overwrite_cm_color_sequence = None
        view_cfg.ls.style_sequences['linestyle'] = self.__LSSelection.text().split(',')
        view_cfg.ls.lw = float(self.__LWSelection.text())
        view_cfg.ls.style_sequences['marker'] = self.__MarkerSelection.text().split(',')
        view_cfg.ls.markersizedefault = float(self.__MarkerSizeSelection.text())
        view_cfg.ls.style_determination_order = [['color', 'marker', 'linestyle'],
                                                 ['color', 'linestyle', 'marker'],
                                                 ['marker', 'color', 'linestyle'],
                                                 ['marker', 'linestyle', 'color'],
                                                 ['linestyle', 'color', 'marker'],
                                                 ['linestyle', 'marker', 'color']][self.__SDOSelection.currentIndex()]

        view_cfg.lines = view_cfg.update_lines()
        self.main_window.UpdateMainPlot()


class AmplitudeWindow(QMainWindow):
    """ Separate window for participation factor plot """
    sigClosed = QtCore.pyqtSignal()

    def __init__(self):
        super(AmplitudeWindow, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Amplitude Plot window")
        self.setMinimumWidth(1024)
        self.setMinimumHeight(800)

    def configure_plotAMP(self, requested_toolname, requested_datasetname, settingsAMPmode,
                          dataset, AMPthreshold, xaxis_param):
        self.settingsAMPmode = settingsAMPmode
        self.AMPmode_name = database[requested_toolname][requested_datasetname].ds.modes.values[settingsAMPmode].name
        self.dataset = dataset
        self.AMPthreshold = AMPthreshold
        self.xaxis_param = xaxis_param

        # Figure settings
        self.AMPfig = Figure(figsize=(6, 6), dpi=100, tight_layout=True)
        self.AMPfig.subplots_adjust(0.06, 0.06, 0.88, 0.97) # left,bottom,right,top
        self.AMPcanvas = FigureCanvas(self.AMPfig)
        toolbar = NavigationToolbar(self.AMPcanvas, self)

        self.main_widget = QWidget(self)
        self.layout_mplib = QVBoxLayout(self.main_widget)
        self.layout_mplib.addWidget(toolbar)
        self.layout_mplib.addWidget(self.AMPcanvas)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        if hasattr(self, 'axes1'):
            uylim = self.axes1.get_ylim()
            uy2lim = self.axes2.get_ylim()
        else:
            uylim = [0, 1.1]
            uy2lim = [-180, 180]

        self.main_plotAMP(title='Amplitude participations for tool {}, dataset {}, {}, visibility threshold = {}'.format(requested_toolname, requested_datasetname, self.AMPmode_name, self.AMPthreshold),
                          xlabel=view_cfg.xparam2xlabel(self.xaxis_param), ylabel='normalized participation',
                          y2label='phase angle in degree', xlim=view_cfg.axes_limits[0], ylim=uylim, y2lim=uy2lim)

    def main_plotAMP(self, title='Amplitudes', xlabel='', ylabel='', y2label='',
                     xlim=None, ylim=None, y2lim=None):

        # define figure with 2 subplots
        self.axes1 = self.AMPfig.add_subplot(211)
        self.axes2 = self.AMPfig.add_subplot(212, sharex=self.axes1)

        # We want the axes cleared every time plot() is called
        self.axes1.clear()
        self.axes2.clear()

        # Set label, grid, etc...
        self.axes1.set_title(title)
        self.axes1.set_xlabel(xlabel)
        self.axes1.set_ylabel(ylabel)
        self.axes1.set_xlim(xlim)
        self.axes1.set_ylim(ylim)
        self.axes1.grid()
        self.axes2.set_xlabel(xlabel)
        self.axes2.set_ylabel(y2label)
        self.axes2.set_xlim(xlim)
        self.axes2.set_ylim(y2lim)
        self.axes2.grid()

        mpl_ls = MPLLinestyle()
        ampl_lines = []
        phase_lines = []

        for i, mode in enumerate(self.dataset.participation_modes.values):
            # only show modes with a part. of minimum self.AMPthreshold (for at least one of the operating points)
            if max(self.dataset.participation_factors_amp.loc[:, i, self.settingsAMPmode]) > self.AMPthreshold:
                ls = mpl_ls.new_ls()
                ampl_line, = self.axes1.plot(self.dataset.operating_points.loc[:, self.xaxis_param],
                                self.dataset.participation_factors_amp.loc[:, i, self.settingsAMPmode],
                                label=mode.name, linewidth=mpl_ls.lw, c=ls['color'], linestyle=ls['linestyle'],
                                marker=ls['marker'], markersize=mpl_ls.markersizedefault)
                phase_line, = self.axes2.plot(self.dataset.operating_points.loc[:, self.xaxis_param],
                                self.dataset.participation_factors_phase.loc[:, i, self.settingsAMPmode],
                                label=mode.name, linewidth=mpl_ls.lw, c=ls['color'], linestyle=ls['linestyle'],
                                marker=ls['marker'], markersize=mpl_ls.markersizedefault)
                ampl_lines.append(ampl_line)
                phase_lines.append(phase_line)

        self.axes2.legend(bbox_to_anchor=(1, 0), loc=3)

        cursor = mplcursors.cursor(ampl_lines + phase_lines, multiple=True, highlight=True)
        pairs = dict(zip(ampl_lines, phase_lines))
        pairs.update(zip(phase_lines, ampl_lines))
        @cursor.connect("add")
        def on_add(sel):
            sel.extras.append(cursor.add_highlight(pairs[sel.artist]))
            sel.annotation.get_bbox_patch().set(fc="grey")
            for line in sel.extras:
                line.set(color="C3")

        self.AMPcanvas.draw()

    def closeEvent(self, event):
        self.sigClosed.emit()


class DatasetTree(QTreeView):
    """ QTreeView of the dataset tree (described by the TreeModel in model_lib) """
    def __init__(self, tree_model, aw):
        super(DatasetTree, self).__init__()
        self.tree_model = tree_model
        self.setModel(tree_model)
        self.setSelectionMode(3)  # ExtendedSelection
        self.selectionModel().selectionChanged.connect(tree_model.updateSelectedData)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.tree_model.delete_data(self.selectedIndexes())

    def showContextMenu(self, position):
        idx = self.currentIndex()
        if not idx.isValid():
            return

        menu = QMenu()

        # todo: I don't know if it is possible to define the action and the linked method in one line (as in the
        # file_menu definition below. This does not seem to work here. So for now first define actions then consequences
        # First define all the actions
        if idx.internalPointer().itemType == 'mode':
            modifyModeDescr = menu.addAction('Modify mode description')
            showAmplitudes = menu.addAction('Show participation factors')
            menu.addSeparator()
        elif idx.internalPointer().itemType == 'dataset' or idx.internalPointer().itemType == 'tool':
            checkAll = menu.addAction('Check all children')
            uncheckAll = menu.addAction('Uncheck all children')

        checkAllSelected = menu.addAction('Check all selected')
        uncheckAllSelected = menu.addAction('Uncheck all selected')

        filterModes = menu.addAction('Filter modes')

        menu.addSeparator()

        deleteThisItem = menu.addAction('Delete this item')
        deleteAllSelected = menu.addAction('Delete all selected items')

        action = menu.exec_(self.viewport().mapToGlobal(position))

        # Then define what happens if an action is clicked
        if idx.internalPointer().itemType == 'mode':
            if action == modifyModeDescr:
                self.popupAEMode = SettingsPopupAEMode(idx.internalPointer().itemData.name,
                                                       idx.internalPointer().itemData.symmetry_type,
                                                       idx.internalPointer().itemData.whirl_type,
                                                       idx.internalPointer().itemData.wt_component)
                self.tree_model.modify_mode_description(idx.internalPointer(), self.popupAEMode.get_settings())
                del self.popupAEMode
            elif action == showAmplitudes:
                modeID, dataset, tool = self.tree_model.get_branch_from_item(idx.internalPointer())
                aw.settingsAMPtool = tool
                aw.settingsAMPdataset = dataset
                aw.settingsAMPmode = modeID[0]
                aw.initAmplitudes(popup=False)
        elif idx.internalPointer().itemType == 'dataset' or idx.internalPointer().itemType == 'tool':
            if action == checkAll:
                self.tree_model.set_checked(idx, Qt.Checked)
            elif action == uncheckAll:
                self.tree_model.set_checked(idx, Qt.Unchecked)

        if action == checkAllSelected:
            self.tree_model.set_checked(idx, Qt.Checked, only_selected=True, selection=self.selectedIndexes())
        elif action == uncheckAllSelected:
            self.tree_model.set_checked(idx, Qt.Unchecked, only_selected=True, selection=self.selectedIndexes())
        elif action == filterModes:
            self.popupFilterModes = SettingsPopupModeFilter()
            self.tree_model.filter_checked(idx.internalPointer(), self.popupFilterModes.get_settings())
            del self.popupFilterModes
        elif action == deleteThisItem:
            self.tree_model.delete_data([idx])
        elif action == deleteAllSelected:
            self.tree_model.delete_data(self.selectedIndexes())


class ApplicationWindow(QMainWindow):
    """ Main window of the GUI """
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Application main window")

        ##############################################################
        # Menu items
        # FILE
        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Add Dataset', self.dataSelection,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction('&Load Database', self.load_database)
        self.file_menu.addAction('&Save to Database', self.save_database)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        # SETTINGS
        self.settings_menu = QMenu('&Settings', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.settings_menu)
        self.settings_menu.addAction('&Header Lines', self.setHeaderLines)
        self.settings_menu.addAction('&Linestyle defaults', self.setLinestyleDefaults)

        # Tools
        self.tools_menu = QMenu('&Tools', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.tools_menu)
        self.tools_menu.addAction('&Plot amplitudes of modes', self.initAmplitudes)
        self.tools_menu.addAction('&Plot amplitudes of highlighted modes', self.amplitudes_of_highlights)

        # HELP
        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)

        ##############################################################
        # DEFINITION OF MAIN WIDGET
        self.main_widget = QWidget(self)

        ##############################################################
        # Layout definition
        self.main_layout      = QVBoxLayout(self.main_widget)
        self.button_layout    = QHBoxLayout(self.main_widget)
        self.layout_mplib     = QVBoxLayout(self.main_widget)
        self.layout_list      = QVBoxLayout(self.main_widget)
        self.layout_mpliblist = QHBoxLayout(self.main_widget)

        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.layout_mpliblist)
        self.layout_mpliblist.addLayout(self.layout_mplib, 4)
        self.layout_mpliblist.addLayout(self.layout_list, 1)

        ##############################################################
        # Treemodel of datasets
        self.dataset_tree_model = TreeModel()
        self.dataset_tree = DatasetTree(self.dataset_tree_model, self)
        self.layout_list.addWidget(self.dataset_tree, 0)

        ##############################################################
        # Some defaults
        self.mode_minpara_cmb = 1
        self.mode_maxpara_cmb = 6
        self.mode_max_cmb     = self.mode_maxpara_cmb
        self.mode_min_cmb     = self.mode_minpara_cmb
        self.pharmonics       = False
        self.skip_header_CMB  = 1              # number of header lines in Campbell file
        self.skip_header_AMP  = 5              # number of header lines in Amplitude file
        self.skip_header_OP   = 1              # number of header lines in operational data file
        self.settingsAMPmode  = None           # default mode for which amplitude plot is made
        self.settingsAMPdataset = None         # which dataset to use for amplitude plot
        self.AMPthreshold     = 0.05           # only modes with 5% amplitude participation are shown in amplitude plot

        ##############################################################
        # Figure settings
        self.fig = Figure(figsize=(6, 6), dpi=100, tight_layout=True)
        self.fig.subplots_adjust(0.06, 0.06, 0.88, 0.97)  # left,bottom,right,top
        self.canvas = FigureCanvas(self.fig)
        toolbar = NavigationToolbar(self.canvas, self)
        self.layout_mplib.addWidget(toolbar)
        self.layout_mplib.addWidget(self.canvas)

        # create figure with two axis
        self.axes1      = self.fig.add_subplot(211)
        self.axes2      = self.fig.add_subplot(212, sharex=self.axes1)
        self.initlimits = True                                         # True for init
        self.right_mouse_press = False
        self.cursor = None

        ##############################################################
        # Set Main Widget
        # This next line makes sure that key press events arrive in the matplotlib figure (e.g. to use 'x' and
        # 'y' for fixing an axis when zooming/panning)
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.statusBar().showMessage("Let the fun begin!", 2000)

        ##############################################################
        # Set buttons
        self.button_pharm = QPushButton('Plot P-Harmonics', self)
        self.button_pharm.clicked.connect(self.plotPharmonics)
        self.button_layout.addWidget(self.button_pharm)

        self.button_xaxis = QComboBox(self)
        self.button_xaxis.currentTextChanged.connect(self.xaxis_change)
        self.xaxis_param = self.button_xaxis.currentText()
        self.xaxis_selection_box = QVBoxLayout()
        self.xaxis_selection_box.addWidget(QLabel('x-axis operating parameter:'))
        self.xaxis_selection_box.addWidget(self.button_xaxis)
        self.button_layout.addLayout(self.xaxis_selection_box)

        self.button_savepdf = QPushButton('Quick Save to PDF', self)
        self.button_savepdf.clicked.connect(self.savepdf)
        self.button_layout.addWidget(self.button_savepdf)

        self.button_rescale = QPushButton('Rescale plot limits', self)
        self.button_rescale.clicked.connect(self.rescale_plot_limits)
        self.button_layout.addWidget(self.button_rescale)

        self.pick_markers = False
        self.pick_markers_box = QCheckBox('Pick markers', self)
        self.pick_markers_box.clicked.connect(self.add_or_remove_scatter)
        self.button_layout.addWidget(self.pick_markers_box)

        ##############################################################
        # Signals from the tree model.
        # -> layoutChanged signals are used to update the main plot
        # -> dataChanged signals are used to update the tree view
        self.dataset_tree_model.layoutChanged.connect(self.UpdateMainPlot)

    ##############################################################
    def add_or_remove_scatter(self, tick_flag):
        self.pick_markers = tick_flag
        if tick_flag is True:
            # add scatter plot on top of normal plot
            for atool in view_cfg.lines:
                for ads in view_cfg.lines[atool]:
                    for mode_ID, mode_lines in enumerate(view_cfg.lines[atool][ads]):
                        if mode_lines is not None:
                            marker_type = mode_lines[0].get_marker()
                            if marker_type == '':
                                marker_type = 'o'
                            marker_size = max(view_cfg.ls.markersizedefault, (mode_lines[0].get_markersize()+1)**2)
                            test = self.axes1.scatter(mode_lines[0].get_xdata(), mode_lines[0].get_ydata(),
                                                      color='white', edgecolors=mode_lines[0].get_c(),
                                                      marker=marker_type, s=marker_size, zorder=1E9)
                            test2 = self.axes2.scatter(mode_lines[1].get_xdata(), mode_lines[1].get_ydata(),
                                                       color='white', edgecolors=mode_lines[0].get_c(),
                                                       marker=marker_type, s=marker_size, zorder=1E9)
                            view_cfg.lines[atool][ads][mode_ID].append(test)
                            view_cfg.lines[atool][ads][mode_ID].append(test2)
            self.UpdateMainPlot()

        elif tick_flag is False:
            for atool in view_cfg.lines:
                for ads in view_cfg.lines[atool]:
                    for mode_ID, mode_lines in enumerate(view_cfg.lines[atool][ads]):
                        if mode_lines is not None:
                            view_cfg.lines[atool][ads][mode_ID] = mode_lines[:2]
            self.UpdateMainPlot()

    # Main plotting routine
    def main_plot(self, title='Campbell', xlabel='', ylabel='', y2label='', xscale='linear', yscale='linear'):
        """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

        # get the possibly user-modified axes limits, it would be good to have a signal when the axes limits are changed
        view_cfg.axes_limits = (self.axes1.get_xlim(), self.axes1.get_ylim(), self.axes2.get_ylim())

        # We want the axes cleared every time plot() is called
        self.axes1.clear()
        self.axes2.clear()

        # Set label, grid, etc...
        self.axes1.set_title(title)
        self.axes1.set_xlabel(xlabel)
        self.axes1.set_ylabel(ylabel)
        self.axes1.grid()
        self.axes2.set_xlabel(xlabel)
        self.axes2.set_ylabel(y2label)
        self.axes2.grid()
        self.vline1 = None
        self.vline2 = None

        freq_lines = []
        damp_lines = []
        freq_scatters = []
        damp_scatters = []
        lines_to_be_selected = []

        for atool in view_cfg.active_data:  # active tool
            for ads in view_cfg.active_data[atool]:  # active dataset
                if database[atool][ads].ds['frequency'].values.ndim != 0:

                    # get xaxis values
                    if self.xaxis_param not in database[atool][ads].ds.operating_parameter:
                        print('WARNING: Operating condition {} is not available in the {}-{} dataset. The data will '
                              'not be plotted.'.format(self.xaxis_param, atool, ads))
                        continue
                    else:
                        xaxis_values = database[atool][ads].ds['operating_points'].loc[:, self.xaxis_param]

                    # add active modes
                    # this can probably also be done without a loop and just with the indices
                    for mode_ID in view_cfg.active_data[atool][ads]:
                        if view_cfg.lines[atool][ads][mode_ID] is None:
                            ls = view_cfg.ls.new_ls()
                            freq_line, = self.axes1.plot(xaxis_values,
                                                         database[atool][ads].ds.frequency.loc[:, mode_ID],
                                                         color=ls['color'],
                                                         linestyle=ls['linestyle'],
                                                         marker=ls['marker'],
                                                         linewidth=view_cfg.ls.lw,
                                                         label=ads + ': ' + database[atool][ads].ds.modes.values[mode_ID].name,
                                                         markersize=view_cfg.ls.markersizedefault, picker=2)
                            damp_line, = self.axes2.plot(xaxis_values,
                                                         database[atool][ads].ds.damping.loc[:, mode_ID],
                                                         color=ls['color'],
                                                         linestyle=ls['linestyle'],
                                                         marker=ls['marker'],
                                                         linewidth=view_cfg.ls.lw,
                                                         label=ads + ': ' + database[atool][ads].ds.modes.values[mode_ID].name,
                                                         markersize=view_cfg.ls.markersizedefault, picker=2)
                            view_cfg.lines[atool][ads][mode_ID] = [freq_line, damp_line]
                            if self.pick_markers is True:
                                marker_type = ls['marker']
                                if marker_type == '':
                                    marker_type = 'o'
                                scat_collection_freq = self.axes1.scatter(xaxis_values,
                                                             database[atool][ads].ds.frequency.loc[:, mode_ID],
                                                             color='white', edgecolors=ls['color'], zorder=1E9,
                                                             marker=marker_type, s=view_cfg.ls.markersizedefault**2)
                                scat_collection_damp = self.axes2.scatter(xaxis_values,
                                                             database[atool][ads].ds.damping.loc[:, mode_ID],
                                                             color='white', edgecolors=ls['color'], zorder=1E9,
                                                             marker=marker_type, s=view_cfg.ls.markersizedefault**2)
                                view_cfg.lines[atool][ads][mode_ID].extend([scat_collection_freq, scat_collection_damp])
                        else:
                            freq_line = self.axes1.add_line(view_cfg.lines[atool][ads][mode_ID][0])
                            self.axes1.update_datalim(freq_line.get_xydata())  # add_line is not automatically used for autoscaling
                            self.axes1.autoscale_view()
                            freq_line.set_label(ads + ': ' + database[atool][ads].ds.modes.values[mode_ID].name)
                            damp_line = self.axes2.add_line(view_cfg.lines[atool][ads][mode_ID][1])
                            self.axes2.update_datalim(damp_line.get_xydata())
                            self.axes2.autoscale_view()
                            damp_line.set_label(ads + ': ' + database[atool][ads].ds.modes.values[mode_ID].name)
                            if self.pick_markers is True:
                                scat_collection_freq = self.axes1.add_collection(view_cfg.lines[atool][ads][mode_ID][2])
                                scat_collection_damp = self.axes2.add_collection(view_cfg.lines[atool][ads][mode_ID][3])

                        freq_lines.append(freq_line)
                        damp_lines.append(damp_line)
                        if self.pick_markers is True:
                            freq_scatters.append(scat_collection_freq)
                            damp_scatters.append(scat_collection_damp)

                        if [[mode_ID], ads, atool] in view_cfg.selected_data:
                            lines_to_be_selected.append(freq_line)
                            lines_to_be_selected.append(damp_line)

                # plot p-harmonics if present
                if database[atool][ads].ds.operating_points.values.ndim != 0 and self.pharmonics:
                    P_harmonics = [1, 3, 6, 9, 12]
                    for index in P_harmonics:
                        P_hamonics_data = database[atool][ads].ds.operating_points.loc[:, 'rot. speed [rpm]']/60*index  # rpm in Hz
                        self.axes1.plot(xaxis_values, P_hamonics_data,
                                        c='grey', linestyle='--', linewidth=0.75, label=str(index)+'P')

        self.axes2.legend(bbox_to_anchor=(1, 0), loc=3)
        # self.axes2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=5)

        xlim, ylim, y2lim = view_cfg.get_axes_limits(self.axes1.get_xlim(), self.axes1.get_ylim(), self.axes2.get_ylim())
        self.axes1.set_xlim(xlim)
        self.axes2.set_xlim(xlim)
        self.axes1.set_ylim(ylim)
        self.axes2.set_ylim(y2lim)

        # do fill_between after the limits
        self.axes2.fill_between([-10, 100], y1=0, y2=-10, where=None, facecolor='grey', alpha=0.1, hatch='/')

        if self.pick_markers is True:
            if self.cursor is not None:
                self.cursor.remove()  # cleanup
            self.cursor = mplcursors.cursor(freq_scatters + damp_scatters, multiple=True, highlight=True,
                                       highlight_kwargs={'color': 'C3'})

            pairs = dict(zip(freq_scatters, damp_scatters))
            pairs.update(zip(damp_scatters, freq_scatters))

            @self.cursor.connect("add")
            def on_add(sel):
                """
                Additional actions when a marker is selected

                When a marker is selected (either in the frequency or damping diagram), the corresponding marker in the
                other diagram has to be added to the mplcursors selection. The PathCollection objects (in this case
                the scatters for each mode) of the frequency and damping diagram are linked through the pairs dict.
                The linked artist is added here manually.
                """
                sel.extras.append(self.cursor.add_highlight(pairs[sel.artist],
                                                            pairs[sel.artist]._offsets[sel.index],
                                                            sel.index))
                sel.annotation.get_bbox_patch().set(fc="grey")

        else:
            # setup mplcursors behavior: multiple text boxes if lines are clicked, highlighting line, pairing of
            # frequency and damping lines
            if self.cursor is not None:
                self.cursor.remove()  # cleanup
            self.cursor = mplcursors.cursor(freq_lines + damp_lines, multiple=True, highlight=True,
                                       highlight_kwargs={'color': 'C3', 'linewidth': view_cfg.ls.lw+2,
                                                         'markerfacecolor': 'C3',
                                                         'markersize': view_cfg.ls.markersizedefault+2})
            for line in lines_to_be_selected:
                self.cursor.add_highlight(line)

            pairs = dict(zip(freq_lines, damp_lines))
            pairs.update(zip(damp_lines, freq_lines))

            @self.cursor.connect("add")
            def on_add(sel):
                self.on_mpl_cursors_pick(sel.artist, 'select')
                sel.extras.append(self.cursor.add_highlight(pairs[sel.artist]))
                sel.annotation.get_bbox_patch().set(fc="grey")

            @self.cursor.connect("remove")
            def on_remove(sel):
                self.on_mpl_cursors_pick(sel.artist, 'deselect')

        self.canvas.draw()
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_mpl_cursors_pick(self, artist, select):
        if not isinstance(artist, matplotlib.lines.Line2D): return
        for atool in view_cfg.lines:
            for ads in view_cfg.lines[atool]:
                for mode_ID, mode_lines in enumerate(view_cfg.lines[atool][ads]):
                    if mode_lines is not None:
                        if artist in mode_lines:
                            # print('Dataset found: tool={}, dataset={}, mode={}'.format(atool, ads, database[atool][ads].ds.modes[mode_ID]))

                            item = self.dataset_tree_model.getItem_from_branch([[mode_ID], ads, atool])

                            # when the user selects a mode in the tree the full plot is reset and updated, this has to
                            # be prevented when selecting a line with mplcursors. Therefore only update view_cfg.selected_data
                            self.dataset_tree.selectionModel().selectionChanged.disconnect(self.dataset_tree.tree_model.updateSelectedData)
                            self.dataset_tree.selectionModel().selectionChanged.connect(self.dataset_tree.tree_model.updateViewCfgSelectedData)

                            if select == 'select':
                                self.dataset_tree.selectionModel().select(self.dataset_tree_model.createIndex(item.row(), 0, item),
                                                                          QItemSelectionModel.Select)  # Toggle
                            elif select == 'deselect':
                                self.dataset_tree.selectionModel().select(self.dataset_tree_model.createIndex(item.row(), 0, item),
                                                                          QItemSelectionModel.Deselect)  # Toggle

                            self.dataset_tree.selectionModel().selectionChanged.disconnect(self.dataset_tree.tree_model.updateViewCfgSelectedData)
                            self.dataset_tree.selectionModel().selectionChanged.connect(self.dataset_tree.tree_model.updateSelectedData)

    def on_motion(self, event):
        """
        Matplotlib Callback function for mouse motion. A vertical line is plotted at the mouse position if the right
        mouse button is pressed.
        """
        if self.right_mouse_press is False: return
        if event.inaxes != self.axes1 and event.inaxes != self.axes2: return
        if self.vline1 is not None:
            self.vline1.remove()
            self.vline2.remove()
        self.vline1 = self.axes1.vlines(x=event.xdata, ymin=self.axes1.get_ylim()[0], ymax=self.axes1.get_ylim()[1])
        self.vline2 = self.axes2.vlines(x=event.xdata, ymin=self.axes2.get_ylim()[0], ymax=self.axes2.get_ylim()[1])
        self.canvas.draw()

    def on_press(self, event):
        """ Callback function for mouse press events. This does not necessarily have to be a matplotlib callback. """
        if event.button is MouseButton.RIGHT:
            self.right_mouse_press = True

            self.find_data_of_highlights()

    def find_data_of_highlights(self):
        for atool in view_cfg.lines:
            for ads in view_cfg.lines[atool]:
                for mode_ID, mode_lines in enumerate(view_cfg.lines[atool][ads]):
                    if mode_lines is not None:

                        for sel in self.cursor.selections:
                            if sel.artist in mode_lines:
                                print('Selections are:', atool, ads, mode_ID)
                                self.settingsAMPtool = atool
                                self.settingsAMPdataset = ads
                                self.settingsAMPmode = mode_ID

    def on_release(self, event):
        """ Callback function for mouse release events. This does not necessarily have to be a matplotlib callback. """
        if event.button is MouseButton.RIGHT:
            self.right_mouse_press = False

    def UpdateMainPlot(self):
        """ Update main plot. This wrapping method currently does not make sense, but could be reimplemented later. """
        self.main_plot(title='Campbell Diagram', xlabel=view_cfg.xparam2xlabel(self.xaxis_param),
                       ylabel='Frequency in Hz', y2label='Damping Ratio in %')

    def load_database(self):
        """ Load data from database (and use default view settings) """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filter = "CampbellViewer Database file (*.nc);;All Files (*)"
        fileName, _ = QFileDialog.getOpenFileName(self, "Load CampbellViewer Database", "", filter, options=options)

        # save "old" database
        old_database = copy.deepcopy(database)

        loaded_datasets = database.load(fname=fileName)
        for toolname in loaded_datasets:
            for datasetname in loaded_datasets[toolname]:
                self.init_active_data(toolname, datasetname)

        self.dataset_tree_model.addModelData(old_database=old_database)
        self.dataset_tree_model.layoutChanged.emit()

    def save_database(self):
        """ Save data to database """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filter = "CampbellViewer Database file (*.nc);;All Files (*)"
        fileName, _ = QFileDialog.getSaveFileName(self, "Save to CampbellViewer Database", "", filter, options=options)

        if fileName[-3:] != ".nc":
            fileName = fileName + ".nc"

        database.save(fname=fileName)

    def dataSelection(self):
        """ Select to add HAWCStab2 or Bladed data """
        self.popup = SettingsPopupDataSelection()
        tool, datasetname = self.popup.get_settings()

        if '&' in datasetname:
            print('& is not allowed in the datasetname')
            datasetname = datasetname.replace('&', '_')

        # A unique datasetname is enforced
        if tool in database:
            datasetname = assure_unique_name(datasetname, database[tool].keys())

        # save "old" database (only the delta updated_database - old_database is added to tree model, this is done to
        # retain the tree node properties of elements that were already loaded)
        old_database = copy.deepcopy(database)

        # load data in database
        if tool == 'HAWCStab2':
            self.openFileNameDialogHAWCStab2(datasetname)
        elif tool == 'Bladed (lin.)':
            self.openFileNameDialogBladedLin(datasetname)
        else:
            raise ValueError('Only HAWCStab2 and Bladed-Linearization data are allowed as input.')
        del self.popup

        # if the data is loaded successfully -> initialize the active modes
        # update the tree model data
        if tool in database:
            if datasetname in database[tool]:
                self.init_active_data(tool, datasetname)
                self.dataset_tree_model.addModelData(old_database=old_database)
                self.dataset_tree_model.layoutChanged.emit()

    def init_active_data(self, toolname, datasetname):
        """ Initialize the active_data global variable for this toolname/datasetname combination """
        if toolname not in view_cfg.active_data:
            view_cfg.active_data[toolname] = dict()
            view_cfg.lines[toolname] = dict()
        view_cfg.active_data[toolname][datasetname] = np.arange(self.mode_minpara_cmb-1,
                                                                self.mode_maxpara_cmb, 1).tolist()
        view_cfg.lines[toolname][datasetname] = [None]*len(database[toolname][datasetname].ds.modes)

        # add the (unique) operating parameters of this dataset to the xaxis button.
        self.button_xaxis.addItems(list(set(database[toolname][datasetname].ds.operating_parameter.data).difference(
                                       set([self.button_xaxis.itemText(i) for i in range(self.button_xaxis.count())]))))
        self.button_xaxis.model().sort(0)

    ##############################################################
    # Open File Dialog for HAWCStab2 result files
    def openFileNameDialogHAWCStab2(self, datasetname='default'):
        '''Open File Dialog for HAWCStab2 Campbell diagramm files'''
        suffix_options = ['cmb', 'amp', 'opt']
        file_name_descriptions = ['Campbell Result Files',
                                  'Amplitude Result Files',
                                  'Operational Data Files']
        for suffix, descr in zip(suffix_options, file_name_descriptions):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            filter = "HAWCStab2 {} (*.{});;All Files (*)".format(descr, suffix)
            fileName, _ = QFileDialog.getOpenFileName(self, "Open {}".format(descr), "", filter, options=options)

            if QFileInfo(fileName).exists():
                # get filename extension
                fileNameExtension = QFileInfo(fileName).suffix()
                # what kind of data are these
                if fileNameExtension == suffix:
                    database.add_data(datasetname, 'hawcstab2',
                                      tool_specific_info={'filename{}'.format(suffix): fileName,
                                                          'skip_header_CMB': self.skip_header_CMB,
                                                          'skip_header_AMP': self.skip_header_AMP,
                                                          'skip_header_OP': self.skip_header_OP})

    def openFileNameDialogBladedLin(self, datasetname='default'):
        '''Open File Dialog for Bladed Linearization result files'''
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filter = "Bladed Linearization Result Files (*.$PJ);;All Files (*)"
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Bladed Linearization Result Files", "", filter, options=options)

        if QFileInfo(fileName).exists():
            result_dir = QFileInfo(fileName).absolutePath()
            result_prefix = QFileInfo(fileName).baseName()
            database.add_data(datasetname, 'bladed-lin',
                              tool_specific_info={'result_dir': result_dir, 'result_prefix': result_prefix})

    def plotPharmonics(self):
        """ Plot P-Harmonics in Campbell diagram """
        if self.pharmonics == True:
            self.pharmonics = False
        else:
            self.pharmonics = True
        self.UpdateMainPlot()

    def xaxis_change(self, text):
        """
        - set the xaxis_param
        - modify all xaxis values of the active lines
        - update the main plot
        """
        self.xaxis_param = text
        # modify the xaxis values of all visible lines
        for atool in view_cfg.active_data:  # active tool
            for ads in view_cfg.active_data[atool]:  # active dataset
                if text not in database[atool][ads].ds.operating_parameter:
                    view_cfg.reset_these_lines(tool=atool, ds=ads)
                else:
                    for mode_ID in view_cfg.active_data[atool][ads]:  # active mode tracks
                        if view_cfg.lines[atool][ads][mode_ID] is not None:
                            for artist in view_cfg.lines[atool][ads][mode_ID]:  # freq. and damp. lines
                                if isinstance(artist, matplotlib.lines.Line2D):
                                    artist.set_xdata(database[atool][ads].ds["operating_points"].sel(operating_parameter=text))
                                else:
                                    scatter_offsets = artist.get_offsets()
                                    scatter_offsets[:, 0] = database[atool][ads].ds["operating_points"].sel(operating_parameter=text)
                                    artist.set_offsets(scatter_offsets)

        view_cfg.auto_scaling_x = True
        self.UpdateMainPlot()

    def rescale_plot_limits(self):
        view_cfg.auto_scaling_x = True
        view_cfg.auto_scaling_y = True
        self.UpdateMainPlot()

    ###################
    # save plot
    def savepdf(self):
        """Saves the current plot to pdf. todo: FileDialog to set file name has to be added"""

        pdf_filename = 'CampbellViewerPlot.pdf'
        if QFileInfo(pdf_filename).exists():
            msg = QMessageBox()
            msg.setWindowTitle("WARNING")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("File already exist! Overwrite?")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            if msg.exec_() == QMessageBox.Ok:
                self.fig.savefig(pdf_filename)
        else:
            self.fig.savefig(pdf_filename)

    ##########
    # Settings
    ##########
    def setHeaderLines(self):
        """ This routine overrides the default header line numbers for Campbell and Amplitude files """
        self.popup = SettingsPopupHS2Headers(self.skip_header_CMB, self.skip_header_AMP, self.skip_header_OP)
        (self.skip_header_CMB, self.skip_header_AMP, self.skip_header_OP) = self.popup.get_settings()
        del self.popup

    def setLinestyleDefaults(self):
        """ This routine sets the default linestyle behaviour """
        self.popup = SettingsPopupLinestyle(self)
        del self.popup

    ##########
    # Tools
    ##########
    def amplitudes_of_highlights(self):
        self.find_data_of_highlights()
        self.initAmplitudes(popup=False)

    def initAmplitudes(self, popup=True):
        """
        This routine initializes the window/plot of the participation factors on the amplitudes for a
        certain mode/dataset
        """
        if popup is True:
            self.popupAMP = SettingsPopupAMP()
            success, self.settingsAMPtool, self.settingsAMPdataset, self.settingsAMPmode = self.popupAMP.get_settings()
            del self.popupAMP
            if success is False:
                return

        if (database[self.settingsAMPtool][self.settingsAMPdataset].ds.frequency.values.ndim != 0 and
            database[self.settingsAMPtool][self.settingsAMPdataset].ds.participation_factors_amp.values.ndim != 0):
            self.AmplitudeWindow = AmplitudeWindow()
            self.AmplitudeWindow.sigClosed.connect(self.deleteAmplitudes)
        else:
            QMessageBox.about(self, "WARNING", "Campbell and Amplitude files have to be loaded first!")
            return

        self.updateAmplitudes()

    def deleteAmplitudes(self):
        """ Deletes AmplitudeWindow attribute if Amplitude Window is closed """
        del self.AmplitudeWindow

    def updateAmplitudes(self):
        """ Update Amplitude plot according to settingsAMPdataset and settingsAMPmode """
        if (database[self.settingsAMPtool][self.settingsAMPdataset].ds.frequency.values.ndim != 0 and
            database[self.settingsAMPtool][self.settingsAMPdataset].ds.participation_factors_amp.values.ndim != 0):

            # get the possibly user-modified axes limits, it would be good to have a signal when the axes limits are changed
            view_cfg.axes_limits = (self.axes1.get_xlim(), self.axes1.get_ylim(), self.axes2.get_ylim())

            self.AmplitudeWindow.configure_plotAMP(self.settingsAMPtool,
                                                   self.settingsAMPdataset,
                                                   self.settingsAMPmode,
                                                   database[self.settingsAMPtool][self.settingsAMPdataset].ds,
                                                   self.AMPthreshold,
                                                   self.xaxis_param)
            self.AmplitudeWindow.show()
        else:
            QMessageBox.about(self, "WARNING", "Campbell and Amplitude files have to be loaded first!")
            return

    ##########
    # file
    ##########
    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QMessageBox.about(self, "About",
        """Copyright 2021 \nThis program is a simple code for postprocessing the results from a HAWCStab2 calculation """+
        """for creating Campbell diagrams.\n\n"""+
        """CampbellViewer is free software: you can redistribute it and/or modify\n"""+
        """it under the terms of the GNU General Public License as published by\n"""+
        """the Free Software Foundation, either version 3 of the License, or\n"""+
        """(at your option) any later version.\n\n"""+
        """CampbellViewer is distributed in the hope that it will be useful,\n"""+
        """but WITHOUT ANY WARRANTY; without even the implied warranty of\n"""+
        """MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"""+
        """GNU General Public License for more details.\n\n"""+
        """You should have received a copy of the GNU General Public License\n"""+
        """along with CampbellViewer.  If not, see <http://www.gnu.org/licenses/>""")




##########
# Exception handling
##########
def my_excepthook(type, value, tback):
    '''
    FUNCTION my_excepthook

    Ensures the error tracing in combination with pyQt.

    :param type: type-object containing the exception type
    :param value: string containing the error message
    :param trb: traceback-object
    :return: Nothing
    '''

    # then call the default handler
    sys.__excepthook__(type, value, tback)


def main():
    """Main function to execute CampbellViewer.

    """

    sys.excepthook = my_excepthook

    # define main app
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    aw = ApplicationWindow()
    aw.setWindowTitle("UniversalCampbellPlotter")
    aw.setWindowIcon(QIcon('../images/Campbell.PNG'))

    # set initial size
    w = 1400
    h = 1000
    aw.setMinimumSize(w, h)
    aw.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
