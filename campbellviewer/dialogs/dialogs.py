"""
Module for dialogs
"""
from __future__ import annotations
from typing import Tuple
import importlib.resources
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QDialog, QWidget, QTabWidget,
    QLineEdit, QPushButton, QSpinBox, QCheckBox, QComboBox, QLabel
    )
from PyQt5.QtGui  import QDoubleValidator, QIcon
from PyQt5.QtCore import Qt, QSettings

from campbellviewer.settings.globals import view_cfg, database

####
# Popup setting dialogs
####


class GeneralTab(QWidget):
    def __init__(self,*args):
        super(GeneralTab, self).__init__(*args)
        self._main_layout = QGridLayout(self)
        self._main_layout.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        self.setLayout(self._main_layout)


class SettingsMenuTabs(QTabWidget):
    """Class for a settings QDialog with tabs"""
    def __init__(self, qsettings: QSettings, *args):
        super(SettingsMenuTabs, self).__init__(*args)

        # Initialize tab screen
        self.__general = SettingsNumModes(qsettings)
        self.__hs2     = GeneralTab()
        self.__DNVB    = GeneralTab()

        #self.__plot._main_layout.addWidget(QLabel("Test 2"))

        # Add tabs
        self.addTab(self.__general,"General")
        self.addTab(self.__hs2    ,"HAWCStab2 I/O")
        self.addTab(self.__DNVB   ,"DNV Bladed I/O")

        # add ICON
        # icon_path = importlib.resources.files('campbellviewer') / 'assets' / 'Loads_noText.png'
        # self.setTabIcon(1,QtG.QIcon(QtG.QPixmap(str(icon_path)))

    def save_settings(self):
        self.__general.save_settings()

class GeneralSettingsDialog(QDialog):
    """Base class for a popup dialog for general settings """
    def __init__(self, qsettings: QSettings):
        super(GeneralSettingsDialog, self).__init__()

        self.setWindowTitle("Settings")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumSize(640, 480)
        icon_path = importlib.resources.files('campbellviewer') / 'assets' / 'windturbine_square.png'
        self.setWindowIcon(QIcon(str(icon_path)))

        main_layout = QGridLayout()
        self.setLayout(main_layout)

        # tabbed menu
        self.settings = SettingsMenuTabs(qsettings)
        main_layout.addWidget(self.settings, 0,0,1,2)

        # buttons
        ok_button = QPushButton('OK')
        main_layout.addWidget(ok_button, 1,0,1,1)
        cancel_button = QPushButton('Cancel')
        main_layout.addWidget(cancel_button, 1,1,1,1)
        ok_button.clicked.connect(self.ok_clicked)
        cancel_button.clicked.connect(self.cancel_clicked)

    def ok_clicked(self):
        self.settings.save_settings()
        self.close()

    def cancel_clicked(self):
        self.close()


class SettingsNumModes(QWidget):
    """Class to modify the default numbers shown

    Attributes:
        __qsettings  (QSettings): current settings object
        __minpara_sb (QSpinBox): QSpinBox to select the start plot mode
        __maxpara_sb (QSpinBox): QSpinBox to select the end plot mode
    """
    def __init__(self, qsettings: QSettings) -> None:
        """Initializes popup for HAWCStab2 input file header line definitions

        Args:
            qsettings: QSettings object

        """
        super(SettingsNumModes, self).__init__()

        self.__qsettings = qsettings
        popup_layout = QGridLayout(self)
        popup_layout.setAlignment(Qt.AlignLeft|Qt.AlignTop)

        # try to fetch the data from qsettings, otherwise take default
        if self.__qsettings.contains('mode_minpara_cmb'):
            mode_minpara = self.__qsettings.value('mode_minpara_cmb')
        else:
            # default to 1
            mode_minpara = 1
        if self.__qsettings.contains('mode_maxpara_cmb'):
            mode_maxpara = self.__qsettings.value('mode_maxpara_cmb')
        else:
            # default to 6
            mode_maxpara = 6

        popup_layout.addWidget(QLabel("<b>Campbell-Plot: Default Mode Number Range</b>"), 0,0,1,2)
        minpara_label = QLabel('First Mode Number:')
        maxpara_label = QLabel('Last  Mode Number:')
        popup_layout.addWidget(minpara_label, 1,0,1,1)
        popup_layout.addWidget(maxpara_label, 2,0,1,1)
        self.__minpara_sb = QSpinBox()
        self.__maxpara_sb = QSpinBox()
        self.__minpara_sb.setValue(mode_minpara)
        self.__maxpara_sb.setValue(mode_maxpara)
        popup_layout.addWidget(self.__minpara_sb, 1,1,1,1)
        popup_layout.addWidget(self.__maxpara_sb, 2,1,1,1)

    def save_settings(self):
        """save the settings"""
        self.__qsettings.setValue('mode_minpara_cmb',self.__minpara_sb.value())
        self.__qsettings.setValue('mode_maxpara_cmb',self.__maxpara_sb.value())

########################################################################################################################
class SettingsPopup(QDialog):
    """Base class for a QDialog popup window where the user can modify settings """
    def __init__(self):
        QDialog.__init__(self)

    def update_settings(self):
        """Update the settings based on the input given by the user """
        pass

    def get_settings(self):
        """Get the settings inserted by the user in this popup """
        pass

    def ok_click(self):
        """User clicked ok button -> update settings -> close popup """
        self.update_settings()
        self.close_popup()

    def close_popup(self):
        """Close popup """
        self.close()


class SettingsPopupDataSelection(SettingsPopup):
    """Class for popup-window to select data

    Attributes:
        selected_tool (str): A string indicating which tool the data will come from, HAWCStab2 or Bladed (lin.)
        dataset_name (str): Name of the dataset
        __ToolSelection (QComboBox): QCombobox to select tool
        __DataSetName (QLineEdit): QLineEdit to insert dataset name as string
    """
    def __init__(self):
        """ Initializes data selection popup """
        super(SettingsPopupDataSelection, self).__init__()

        # define initial tool and dataset
        self.selected_tool = 'HAWCStab2'
        self.dataset_name = 'default'

        self.setWindowTitle("Tool selection")
        popup_layoutV = QVBoxLayout(self)
        popup_layoutTool = QHBoxLayout()
        popup_layoutName = QHBoxLayout()
        popup_layoutBttn = QHBoxLayout()

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

    def get_settings(self) -> Tuple[str, str]:
        """Gives the current selected settings

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


class SettingsPopupNumModes(SettingsPopup):
    """Class for popup-window to modify the default numbers shown

    Attributes:
        mode_minpara (int): first mode for plotting
        mode_maxpara (int): last mode for plotting
        __minpara_sb (QSpinBox): QSpinBox to select the start plot mode
        __maxpara_sb (QSpinBox): QSpinBox to select the end plot mode
    """
    def __init__(self, mode_minpara: int, mode_maxpara: int) -> None:
        """Initializes popup for HAWCStab2 input file header line definitions

        Args:
            mode_minpara: integer for initial definition of the first mode for plotting
            mode_maxpara: integer for initial definition of the last mode for plotting
        """
        super(SettingsPopupNumModes, self).__init__()

        self.mode_minpara = mode_minpara
        self.mode_maxpara = mode_maxpara
        self.setWindowTitle("Settings for Default Mode Number for Plotting")
        popup_layout = QGridLayout(self)

        minpara_label = QLabel('First Mode Number:')
        maxpara_label = QLabel('Last  Mode Number:')
        popup_layout.addWidget(minpara_label, 0,0,1,1)
        popup_layout.addWidget(maxpara_label, 1,0,1,1)
        self.__minpara_sb = QSpinBox()
        self.__maxpara_sb = QSpinBox()
        self.__minpara_sb.setValue(self.mode_minpara)
        self.__maxpara_sb.setValue(self.mode_maxpara)
        popup_layout.addWidget(self.__minpara_sb, 0,1,1,1)
        popup_layout.addWidget(self.__maxpara_sb, 1,1,1,1)

        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.ok_click)
        popup_layout.addWidget(button_OK, 2,0,1,1)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.close_popup)
        popup_layout.addWidget(button_Cancel, 2,1,1,1)

        self.exec_()

    def get_settings(self) -> Tuple[int, int]:
        """Gives the current selected settings

        Returns:
            mode_minpara: integer of the first mode for plotting
            mode_maxpara: integer of the last mode for plotting
        """
        return self.mode_minpara, self.mode_maxpara

    def update_settings(self):
        """ Updates the settings based on the current content of the popup """
        self.mode_minpara = self.__minpara_sb.value()
        self.mode_maxpara = self.__maxpara_sb.value()


class SettingsPopupHS2Headers(SettingsPopup):
    """Class for popup-window to modify the header lines in Campbell, Amplitude and operational data file which serve as
    input for HAWCStab2

    Attributes:
        settingsCMB (int): Number of header lines in the .cmb file
        settingsAMP (int): Number of header lines in the .amp file
        settingsOP (int): Number of header lines in the .opt file
        __headerLinesCMBE (QSpinBox): QSpinBox to select the number of header lines in .cmb file
        __headerLinesAMPE (QSpinBox): QSpinBox to select the number of header lines in .amp file
        __headerLinesOPE (QSpinBox): QSpinBox to select the number of header lines in .opt file
    """
    def __init__(self, settingsCMB: int, settingsAMP: int, settingsOP: int):
        """Initializes popup for HAWCStab2 input file header line definitions

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
        popup_layoutHCMB = QHBoxLayout()
        popup_layoutHAMP = QHBoxLayout()
        popup_layoutHOP = QHBoxLayout()
        popup_layoutBttn = QHBoxLayout()

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

    def get_settings(self) -> Tuple[int, int, int]:
        """Gives the current selected settings

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
    """Class for popup-window to select for which mode the modal participations have to be shown

    Attributes:
        success (bool): Boolean indicating if user wants to continue -> if the user presses cancel -> success = false
        settingsAMPmode (int): integer indicating which mode has to be used for the modal participation plot
        selected_tool (str): string indicating from which tool the data has to be shown
        selected_dataset (str): string indicating from which dataset the data has to be shown
        __ToolSelection (QComboBox): QComboBox to select the tool for the modal participation plot
        __DataSetSelection (QComboBox): QComboBox to select the dataset for the modal participation plot
        __AMPmode (QComboBox): QComboBox to select the mode for the modal participation plot
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
        popup_layoutAMPmode = QHBoxLayout()
        popup_layoutBttn = QHBoxLayout()
        popup_layoutDS = QHBoxLayout()
        popup_layouttool = QHBoxLayout()

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
        """Update the options for the dataset selection based on the currently selected tool """
        self.__DataSetSelection.clear()
        self.__DataSetSelection.addItems(view_cfg.active_data[self.__ToolSelection.currentText()].keys())

    def update_mode_choice(self):
        """ Update the options for the mode selection based on the currently selected tool and dataset """
        self.__AMPmode.clear()
        if self.__DataSetSelection.currentText():
            self.__AMPmode.addItems(
                [str(database[self.__ToolSelection.currentText()][self.__DataSetSelection.currentText()].ds.modes.values[mode_id].name)
                 for mode_id in view_cfg.active_data[self.__ToolSelection.currentText()][self.__DataSetSelection.currentText()]])

    def get_settings(self) -> Tuple[bool, str, str, str]:
        """Gives the current selected settings

        Returns:
            success: boolean indicating if the user wants to continue with the selection
            selected_tool: string indicating which tool will be used
            selected_dataset: string indicating which dataset will be used
            settings_AMPmode: string indicating which mode index will be used
        """
        return self.success, self.selected_tool, self.selected_dataset, self.settingsAMPmode

    def update_settings(self):
        """Updates the settings based on the current content of the popup """
        self.success = True
        self.selected_tool = self.__ToolSelection.currentText()
        self.selected_dataset = self.__DataSetSelection.currentText()
        self.settingsAMPmode = view_cfg.active_data[self.selected_tool][self.selected_dataset][int(self.__AMPmode.currentIndex())]

    def cancel(self):
        """ Action if user presses cancel. Do not continue with the modal participation plotting. """
        self.success = False
        self.close()


class SettingsPopupAEMode(SettingsPopup):
    """Class for popup-window to modify the description of an aeroelastic mode

    Attributes:
        name (str): string with full name of the aeroelastic mode
        symmetry_type (str): string with indication of the symmetry type of the aeroelastic mode
        whirl_type (str): string with indication of the whirling type of the aeroelastic mode
        wt_component (str): string with indication of the main wind turbine component of the aeroelastic mode
        __NameSelection (QLineEdit): QLineEdit to insert the full name of the mode
        __SymTypeSelection (QComboBox): QComboBox to select the symmetry type of the mode
        __WhirlTypeSelection (QComboBox): QComboBox to select the whirling type of the mode
        __WTCompSelection (QComboBox): QComboBox to select the main wind turbine component of the mode
    """
    def __init__(self, name: str, symmetry_type: str, whirl_type: str, wt_component: str):
        """Initializes popup for modification of an aeroelastic mode description

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
        popup_layoutNAME = QHBoxLayout()
        popup_layoutSYM = QHBoxLayout()
        popup_layoutWHIRL = QHBoxLayout()
        popup_layoutWT = QHBoxLayout()
        popup_layoutBttn = QHBoxLayout()

        self.__NameSelection = QLineEdit(self.name)
        popup_layoutNAME.addWidget(QLabel('Mode name:'))
        popup_layoutNAME.addWidget(self.__NameSelection)

        self.__SymTypeSelection = QComboBox()
        self.__SymTypeSelection.addItems(['symmetric', 'asymmetric'])
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

    def get_settings(self) -> Tuple[str, str, str, str]:
        """Gives the current selected settings

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
    """Class for popup-window to filter aeroelastic modes

    Attributes:
        symmetry_type (str): string with indication of the symmetry type of the aeroelastic mode for the filter
        whirl_type (str): string with indication of the whirling type of the aeroelastic mode for the filter
        wt_component (str): string with indication of the main wind turbine component of the aeroelastic mode for the filter
        __SymTypeSelection (QComboBox): QComboBox to select the symmetry type of the mode for the filter
        __WhirlTypeSelection (QComboBox): QComboBox to select the whirling type of the mode for the filter
        __WTCompSelection (QComboBox): QComboBox to select the main wind turbine component of the mode for the filter
    """
    def __init__(self):
        """ Initializes popup to select a filter for the aeroelastic modes """
        super(SettingsPopupModeFilter, self).__init__()

        self.symmetry_type = 'all'
        self.whirl_type = 'all'
        self.wt_component = 'all'
        self.setWindowTitle("Filter modes")

        popup_layoutV = QVBoxLayout(self)
        popup_layoutSYM = QHBoxLayout()
        popup_layoutWHIRL = QHBoxLayout()
        popup_layoutWT = QHBoxLayout()
        popup_layoutBttn = QHBoxLayout()

        self.__SymTypeSelection = QComboBox()
        self.__SymTypeSelection.addItems(['all', 'symmetric', 'asymmetric'])
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

    def get_settings(self) -> Tuple[str, str, str]:
        """Gives the current selected settings

        Returns:
            symmetry_type: user-defined symmetry type of the aeroelastic mode for filtering
            whirl_type: user-defined whirl type of the aeroelastic mode for filtering
            wt_component: user-defined wind turbine component of the aeroelastic mode for filtering
        """
        return self.symmetry_type, self.whirl_type, self.wt_component

    def update_settings(self):
        """Updates the settings based on the current content of the popup """
        self.symmetry_type = self.__SymTypeSelection.currentText()
        self.whirl_type    = self.__WhirlTypeSelection.currentText()
        self.wt_component  = self.__WTCompSelection.currentText()


class SettingsPopupLinestyle(SettingsPopup):
    """Class for popup-window to set linestyle behaviour of matplotlib plot

    Attributes:
        main_window (QMainWindow): QMainWindow which can be updated based on the user settings
        __CMSelection (QComboBox): QComboBox to select the colormap for the matplotlib plot
        __OverwriteSelection (QCheckBox):
            QCheckBox to allow the user to overwrite the colormap with a user-defined list of colors
        __OverwriteListSelection (QLineEdit):
            QLineEdit where the user can define a list of colors to overwrite the standard colormap
        __LSSelection (QLineEdit): QLineEdit where the user can define a list of linestyles
        __LWSelection (QLineEdit): QLineEdit to set the default linewidth size
        __MarkerSelection (QLineEdit): QLineEdit where the user can define a list of marker types
        __MarkerSizeSelection (QLineEdit): QLineEdit to set the default marker size
        __SDOSelection (QComboBox): QComboBox to define in which order the lines are diversified
            e.g. [1. Color, 2. Marker, 3. Linestyle] will first make lines with different colors, until all colors are
            used, then use new markers, until all markers are used, then use new linestyle
    """
    def __init__(self, main_window: QMainWindow):
        """Initializes popup to set the default linestyle selection behaviour

        Args:
             main_window: QMainWindow which will be updated based on the settings
        """
        super(SettingsPopupLinestyle, self).__init__()

        self.main_window = main_window

        popup_layoutV = QVBoxLayout(self)
        popup_layoutCM = QHBoxLayout()
        popup_layoutLS = QHBoxLayout()
        popup_layoutMARKER = QHBoxLayout()
        popup_layoutLW = QHBoxLayout()
        popup_layoutMARKERSIZE = QHBoxLayout()
        popup_layoutCM2 = QHBoxLayout()
        popup_layoutSDO = QHBoxLayout()
        popup_layoutBttn = QHBoxLayout()

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
        popup_layoutCM2.addWidget(self.__OverwriteSelection, 0)
        popup_layoutCM2.addWidget(self.__OverwriteListSelection, 0)

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
        self.__SDOSelection.addItems(['Marker: 1. Color, 2. Linestyle',
                                      'Marker: 1. Linestyle, 2. Color',
                                      'Linestyle: 1. Color, 2. Marker',
                                      'Linestyle: 1. Marker, 2. Color',
                                      'Color: 1. Marker, 2. Linestyle',
                                      'Color: 1. Linestyle, 2. Marker'])
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
        """Based on the state of self.__OverwriteSelection, either overwrite the self.__CMSelection or not

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
                                                 ['linestyle', 'marker', 'color'],
                                                 ['color', 'linestyle', 'marker'],
                                                 ['marker', 'linestyle', 'color'],
                                                 ['marker', 'color', 'linestyle'],
                                                 ['linestyle', 'color', 'marker']][self.__SDOSelection.currentIndex()]

        view_cfg.lines = view_cfg.update_lines()
        self.main_window.UpdateMainPlot()