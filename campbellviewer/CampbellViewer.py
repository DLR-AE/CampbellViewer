########################################################################################
# This file is part of CampbellViewer.
# 
# CampbellViewer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# CampbellViewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with CampbellViewer.  If not, see <http://www.gnu.org/licenses/>
########################################################################################
#
# --------------------------------------------------------------------------------------
# Simple postprocessing GUI for wind turbine linearization results.
#
#
# Purpose: Create Interactive Campbell-Plots, participation plots, mode visualizations, etc.
#
# author: J.Rieke - Nordex Energy GmbH
#         H.Verdonck - DLR
#         O.Hach - DLR
#
# --------------------------------------------------------------------------------------
# There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# --------------------------------------------------------------------------------------

import sys
import numpy as np
import copy

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout, QSizePolicy, QMessageBox, QWidget, QDialog
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QSpinBox, QListWidget
from PyQt5.QtWidgets import QStyleFactory, QCheckBox, QComboBox, QTableView, QListView, QTreeView, QAbstractItemView
from PyQt5.QtGui  import QIcon, QDoubleValidator
from PyQt5.QtCore import QFileInfo, Qt

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors
from model_lib import DatasetTableModel, ModeTableModel, TreeModel
from globals import database, view_cfg
from utilities import assure_unique_name

matplotlib.rcParams['hatch.color']     = 'grey'
matplotlib.rcParams['hatch.linewidth'] = 0.2

# activate clipboard --> not working currently!
#~ matplotlib.rcParams['toolbar'] = 'toolmanager'

####
# Popup
class DataSelectionPopup(QDialog):
    '''Class for popup-window to specify data type'''
    def __init__(self, default='HAWCStab2'):
        QDialog.__init__(self)
        self.selected_tool = default
        self.dataset_name = 'default'

        self.setWindowTitle("Tool selection")
        popup_layoutV = QVBoxLayout(self)
        popup_layoutTool = QHBoxLayout(self)
        popup_layoutName = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)

        tool_selection = QLabel('Select which data type will be loaded (default=''HAWCStab2''):')
        self.__ToolSelection = QComboBox()
        self.__ToolSelection.addItems(['HAWCStab2', 'Bladed (lin.)'])
        popup_layoutTool.addWidget(tool_selection)
        popup_layoutTool.addWidget(self.__ToolSelection)

        datasetname = QLabel('Specify dataset name:')
        self.__DataSetName = QLineEdit('default')
        popup_layoutName.addWidget(datasetname)
        popup_layoutName.addWidget(self.__DataSetName)

        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.newDataSelected)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.ClosePopup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layoutTool)
        popup_layoutV.addLayout(popup_layoutName)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def selectTool(self):
        return self.selected_tool, self.dataset_name

    def newDataSelected(self):
        self.selected_tool = self.__ToolSelection.currentText()
        self.dataset_name = self.__DataSetName.text()
        self.close()

    def ClosePopup(self):
        self.close()


class SettingsPopup(QDialog):
    '''Class for popup-window to modify the header lines in Campbell, Amplitude and operational 
       data file as computed with HAWCStab2'''
    def __init__(self, settingsCMB, settingsAMP, settingsOP):
        QDialog.__init__(self)
        
        self.settingsCMB = settingsCMB
        self.settingsAMP = settingsAMP
        self.settingsOP  = settingsOP
        self.setWindowTitle("Settings for Header Lines")
        popup_layoutV    = QVBoxLayout(self)
        popup_layoutHCMB = QHBoxLayout(self)
        popup_layoutHAMP = QHBoxLayout(self)
        popup_layoutHOP  = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)
        
        headerLinesCMBL   = QLabel('Number of header lines in Campbell file:')
        headerLinesAMPL   = QLabel('Number of header lines in Amplitude file:')
        headerLinesOPL    = QLabel('Number of header lines in Operational data file:')
        self.__headerLinesCMBE   = QSpinBox()
        self.__headerLinesAMPE   = QSpinBox()
        self.__headerLinesOPE    = QSpinBox()
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
        button_OK.clicked.connect(self.newSettings)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.ClosePopup)
        popup_layoutBttn.addWidget(button_Cancel)
        
        
        popup_layoutV.addLayout(popup_layoutHCMB)
        popup_layoutV.addLayout(popup_layoutHAMP)
        popup_layoutV.addLayout(popup_layoutHOP)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()
        
    def getNewSettings(self):
        return(self.settingsCMB, self.settingsAMP, self.settingsOP)        

    def newSettings(self):  
        self.settingsCMB = self.__headerLinesCMBE.value()
        self.settingsAMP = self.__headerLinesAMPE.value()  
        self.settingsOP  = self.__headerLinesOPE.value()  
        self.on_apply = False
        self.close()        

    def ClosePopup(self):
        self.close()
        

class SettingsPopupAMP(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        
        self.settingsAMPmode = None
        self.selected_tool = list(view_cfg.active_data.keys())[0]
        self.selected_dataset = list(view_cfg.active_data[self.selected_tool].keys())[0]
        self.setWindowTitle("Set mode number for Amplitude plot")
        popup_layoutV        = QVBoxLayout(self)
        popup_layoutAMPmode  = QHBoxLayout(self)
        popup_layoutBttn     = QHBoxLayout(self)
        popup_layoutDS       = QHBoxLayout(self)
        popup_layouttool     = QHBoxLayout(self)

        tool_selection = QLabel('Select tool:')
        self.__ToolSelection = QComboBox()
        self.__ToolSelection.addItems(view_cfg.active_data.keys())
        self.__ToolSelection.currentTextChanged.connect(self.update_dataset_choice)
        popup_layouttool.addWidget(tool_selection)
        popup_layouttool.addWidget(self.__ToolSelection)

        dataset_selection = QLabel('Select dataset:')
        self.__DataSetSelection = QComboBox()
        self.__DataSetSelection.addItems(view_cfg.active_data[self.selected_tool].keys())
        self.__DataSetSelection.currentTextChanged.connect(self.update_mode_choice)
        popup_layoutDS.addWidget(dataset_selection)
        popup_layoutDS.addWidget(self.__DataSetSelection)

        AMPmode = QLabel('Amplitude mode to plot:')
        self.__AMPmode = QComboBox()
        self.__AMPmode.addItems([str(database[self.selected_tool][self.selected_dataset].modes.values[mode_id].name) for mode_id in view_cfg.active_data[self.selected_tool][self.selected_dataset]])
        popup_layoutAMPmode.addWidget(AMPmode)
        popup_layoutAMPmode.addWidget(self.__AMPmode)
        
        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.newSettings)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.ClosePopup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layouttool)
        popup_layoutV.addLayout(popup_layoutDS)
        popup_layoutV.addLayout(popup_layoutAMPmode)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def update_dataset_choice(self):
        self.__DataSetSelection.clear()
        self.__DataSetSelection.addItems(view_cfg.active_data[self.__ToolSelection.currentText()].keys())

    def update_mode_choice(self):
        self.__AMPmode.clear()
        self.__AMPmode.addItems(view_cfg.active_data[self.__ToolSelection.currentText()]
                                [self.__DataSetSelection.currentText()])

    def getNewSettings(self):
        return self.selected_tool, self.selected_dataset, self.settingsAMPmode

    def newSettings(self):
        self.selected_tool = self.__ToolSelection.currentText()
        self.selected_dataset = self.__DataSetSelection.currentText()
        self.settingsAMPmode = view_cfg.active_data[self.selected_tool][self.selected_dataset][int(self.__AMPmode.currentIndex())]

        self.on_apply = False
        self.close()        

    def ClosePopup(self):
        self.settingsAMPmode = -1
        self.close()


class SettingsPopupAEMode(QDialog):
    """ Class for popup-window to modify the description of an aeroelastic mode """
    def __init__(self, name, symmetry_type, whirl_type, wt_component):
        QDialog.__init__(self)

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

        name_selection = QLabel('Mode name:')
        self.__NameSelection = QLineEdit(self.name)
        popup_layoutNAME.addWidget(name_selection)
        popup_layoutNAME.addWidget(self.__NameSelection)

        symmetry_type_selection = QLabel('Symmetry type:')
        self.__SymTypeSelection = QComboBox()
        self.__SymTypeSelection.addItems(['Symmetric', 'Asymmetric'])
        self.__SymTypeSelection.setEditable(True)
        self.__SymTypeSelection.setCurrentText(self.symmetry_type)
        popup_layoutSYM.addWidget(symmetry_type_selection)
        popup_layoutSYM.addWidget(self.__SymTypeSelection)

        whirl_type_selection = QLabel('Whirl type:')
        self.__WhirlTypeSelection = QComboBox()
        self.__WhirlTypeSelection.addItems(['BW', 'FW', 'Sym'])
        self.__WhirlTypeSelection.setEditable(True)
        self.__WhirlTypeSelection.setCurrentText(self.whirl_type)
        popup_layoutWHIRL.addWidget(whirl_type_selection)
        popup_layoutWHIRL.addWidget(self.__WhirlTypeSelection)

        wt_component_selection = QLabel('Wind turbine component:')
        self.__WTCompSelection = QComboBox()
        self.__WTCompSelection.addItems(['tower', 'blade', 'drivetrain'])
        self.__WTCompSelection.setEditable(True)
        self.__WTCompSelection.setCurrentText(self.wt_component)
        popup_layoutWT.addWidget(wt_component_selection)
        popup_layoutWT.addWidget(self.__WTCompSelection)

        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.newSettings)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.ClosePopup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layoutNAME)
        popup_layoutV.addLayout(popup_layoutSYM)
        popup_layoutV.addLayout(popup_layoutWHIRL)
        popup_layoutV.addLayout(popup_layoutWT)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def getNewSettings(self):
        return (self.name, self.symmetry_type, self.whirl_type, self.wt_component)

    def newSettings(self):
        self.name = self.__NameSelection.text()
        self.symmetry_type = self.__SymTypeSelection.currentText()
        self.whirl_type = self.__WhirlTypeSelection.currentText()
        self.wt_component = self.__WTCompSelection.currentText()
        self.close()

    def ClosePopup(self):
        self.close()


class SettingsPopupModeFilter(QDialog):
    """ Class for popup-window to filter aeroleastic modes """
    def __init__(self):
        QDialog.__init__(self)

        self.symmetry_type = 'all'
        self.whirl_type = 'all'
        self.wt_component = 'all'
        self.setWindowTitle("Filter modes")

        popup_layoutV = QVBoxLayout(self)
        popup_layoutSYM = QHBoxLayout(self)
        popup_layoutWHIRL = QHBoxLayout(self)
        popup_layoutWT = QHBoxLayout(self)
        popup_layoutBttn = QHBoxLayout(self)

        symmetry_type_selection = QLabel('Only show this symmetry type:')
        self.__SymTypeSelection = QComboBox()
        self.__SymTypeSelection.addItems(['all', 'Symmetric', 'Asymmetric'])
        self.__SymTypeSelection.setEditable(True)
        popup_layoutSYM.addWidget(symmetry_type_selection)
        popup_layoutSYM.addWidget(self.__SymTypeSelection)

        whirl_type_selection = QLabel('Only show this whirl type:')
        self.__WhirlTypeSelection = QComboBox()
        self.__WhirlTypeSelection.addItems(['all', 'BW', 'FW', 'Sym'])
        self.__WhirlTypeSelection.setEditable(True)
        popup_layoutWHIRL.addWidget(whirl_type_selection)
        popup_layoutWHIRL.addWidget(self.__WhirlTypeSelection)

        wt_component_selection = QLabel('Only show this wind turbine component:')
        self.__WTCompSelection = QComboBox()
        self.__WTCompSelection.addItems(['all', 'tower', 'blade', 'drivetrain'])
        self.__WTCompSelection.setEditable(True)
        popup_layoutWT.addWidget(wt_component_selection)
        popup_layoutWT.addWidget(self.__WTCompSelection)

        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.newSettings)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.ClosePopup)
        popup_layoutBttn.addWidget(button_Cancel)

        popup_layoutV.addLayout(popup_layoutSYM)
        popup_layoutV.addLayout(popup_layoutWHIRL)
        popup_layoutV.addLayout(popup_layoutWT)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()

    def getNewSettings(self):
        return (self.symmetry_type, self.whirl_type, self.wt_component)

    def newSettings(self):
        self.symmetry_type = self.__SymTypeSelection.currentText()
        self.whirl_type = self.__WhirlTypeSelection.currentText()
        self.wt_component = self.__WTCompSelection.currentText()
        self.close()

    def ClosePopup(self):
        self.close()


class SettingsPopupLinestyle(QDialog):
    """ Class for popup-window to set linestyle behaviour """
    def __init__(self, main_window):
        QDialog.__init__(self)

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
        self.__CMSelection.addItems(['tab10', 'tab20', 'tab20b', 'tab20c', 'Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1', 'Set2', 'Set3'])
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
        # this line edit is very likely to give wrong input, this should be verified somewhere
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
        button_apply.clicked.connect(self.newSettings)
        popup_layoutBttn.addWidget(button_apply)
        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.ok)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.ClosePopup)
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

    def ok(self):
        self.newSettings()
        self.close()

    def newSettings(self):
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

    def ClosePopup(self):
        self.close()


class AmplitudeWindow(QMainWindow):
    sigClosed = QtCore.pyqtSignal()

    def __init__(self):
        super(AmplitudeWindow, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Amplitude Plot window")
        self.setMinimumWidth(1024)
        self.setMinimumHeight(800)

    def configure_plotAMP(self, requested_toolname, requested_datasetname, settingsAMPmode, dataset, AMPthreshold):
        self.settingsAMPmode = settingsAMPmode
        self.AMPmode_name = database[requested_toolname][requested_datasetname].modes.values[settingsAMPmode].name
        self.dataset = dataset
        self.AMPthreshold = AMPthreshold

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
            uxlim = self.axes1.get_xlim()
            uylim = self.axes1.get_ylim()
            uy2lim = self.axes2.get_ylim()
        else:            
            uxlim  = [ 3,20]
            #~ uxlim  = [self.data["campbell_data"][0,0],self.data["campbell_data"][-1,0]]
            uylim  = [0,1.1]
            uy2lim = [-180,180]
 
        self.main_plotAMP(title='Amplitude participations for tool {}, dataset {}, {}, visibility threshold = {}'.format(requested_toolname, requested_datasetname, self.AMPmode_name, self.AMPthreshold),
                          xlabel='Wind Speed in m/s', ylabel='normalized participation',
                          y2label='phase angle in degree', xlim=uxlim, ylim=uylim, y2lim=uy2lim)
        
    def main_plotAMP(self, title='Amplitudes', xlabel='', ylabel='', y2label='',
                     xlim=None, ylim=None, y2lim=None, xscale='linear', yscale='linear'):

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
        
        color_sequence      = ['r','g','b','y','c','m','k']
        line_style_sequence = [ '-','--','-.',':']
        lw                  = 1.0
        filled_markers      = ['o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'X']
        markersizedefault   = 3
        ampl_lines = []
        phase_lines = []

        for i, mode in enumerate(self.dataset.participation_modes.values):
            csq  = color_sequence     [(i) % len(color_sequence)]
            if i > len(color_sequence):
                lssq = line_style_sequence[(i) % len(line_style_sequence)]
                mssq = filled_markers     [(i) % len(filled_markers     )]
            else:
                lssq = '-'
                mssq = ''

            # only show modes with a part. of minimum self.AMPthreshold (for at least one of the operating points)
            if max(self.dataset.participation_factors_amp.loc[:, i, self.settingsAMPmode]) > self.AMPthreshold:
                ampl_line, = self.axes1.plot(self.dataset.operating_points.loc[:, 'wind speed [m/s]'],
                                self.dataset.participation_factors_amp.loc[:, i, self.settingsAMPmode],
                                label=mode.name, linewidth=lw, c=csq, linestyle=lssq,
                                marker=mssq, markersize=markersizedefault)
                phase_line, = self.axes2.plot(self.dataset.operating_points.loc[:, 'wind speed [m/s]'],
                                self.dataset.participation_factors_phase.loc[:, i, self.settingsAMPmode],
                                label=mode.name, linewidth=lw, c=csq, linestyle=lssq,
                                marker=mssq, markersize=markersizedefault)
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
    def __init__(self, tree_model):
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
                self.tree_model.modify_mode_description(idx.internalPointer(), self.popupAEMode.getNewSettings())
                del self.popupAEMode
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
            self.tree_model.filter_checked(idx.internalPointer(), self.popupFilterModes.getNewSettings())
            del self.popupFilterModes
        elif action == deleteThisItem:
            self.tree_model.delete_data([idx])
        elif action == deleteAllSelected:
            self.tree_model.delete_data(self.selectedIndexes())


class ApplicationWindow(QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Application main window")
        self.xaxis_item = 'WS'
        
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

        """
        ##############################################################
        # Table as Selection List
        self.mode_table_model = ModeTableModel()
        self.mode_table = QTableView()
        self.mode_table.setModel(self.mode_table_model)
        self.layout_list.addWidget(self.mode_table, 0)

        ##############################################################
        # Table as Selection List
        self.dataset_table_model = DatasetTableModel()
        self.dataset_table = QTableView()
        self.dataset_table.setModel(self.dataset_table_model)
        self.layout_list.addWidget(self.dataset_table, 0)
        """

        ##############################################################
        # Treemodel of datasets
        self.dataset_tree_model = TreeModel()
        self.dataset_tree = DatasetTree(self.dataset_tree_model)
        self.layout_list.addWidget(self.dataset_tree, 0)

        ##############################################################
        # Some defaults
        self.mode_minpara_cmb = 1
        self.mode_maxpara_cmb = 10
        self.mode_max_cmb     = self.mode_maxpara_cmb
        self.mode_min_cmb     = self.mode_minpara_cmb  
        self.pharmonics       = False
        self.skip_header_CMB  = 1              # number of header lines in Campbell file
        self.skip_header_AMP  = 5              # number of header lines in Amplitude file
        self.skip_header_OP   = 1              # number of header lines in operational data file
        self.settingsAMPmode  = None           # default mode for which amplitude plot is made
        self.settingsAMPdataset = None         # which dataset to use for amplitude plot
        self.AMPthreshold     = 0.05           # only modes with 5% amplitude participation are shown in amplitude plot
        # self.LineStyleDict = dict()

        ##############################################################
        # Figure settings
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.fig.subplots_adjust(0.06, 0.06, 0.88, 0.97)  # left,bottom,right,top
        self.canvas = FigureCanvas(self.fig)
        toolbar = NavigationToolbar(self.canvas, self)
        self.layout_mplib.addWidget(toolbar)
        self.layout_mplib.addWidget(self.canvas)

        # create figure with two axis
        self.axes1      = self.fig.add_subplot(211)
        self.axes2      = self.fig.add_subplot(212, sharex=self.axes1)
        self.initlimits = True                                         # True for init

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
        
        self.button_wsrpm = QPushButton('Switch plot over RPM/Windspeed', self)
        self.button_wsrpm.clicked.connect(self.plotWSRPM)
        self.button_layout.addWidget(self.button_wsrpm)

        self.button_savepdf = QPushButton('Quick Save to PDF', self)
        self.button_savepdf.clicked.connect(self.savepdf)
        self.button_layout.addWidget(self.button_savepdf)

        ##############################################################
        # Signals from the tree model.
        # -> layoutChanged signals are used to update the main plot
        # -> dataChanged signals are used to update the tree view
        self.dataset_tree_model.layoutChanged.connect(self.UpdateMainPlot)

    ##############################################################
    # Main plotting routine
    def main_plot(self, title='Campbell', xlabel='', ylabel='', y2label='', xlim=None, ylim=None, y2lim=None,
                  xscale='linear', yscale='linear', xaxis_item='WS'):
        """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
                        
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
        self.axes2.fill_between([-10, 100], y1=0, y2=-10, where=None, facecolor='grey', alpha=0.1, hatch='/')

        # Set item of x-axis = wind speed or RPM
        if not hasattr(self, 'xaxis_item'):
            self.xaxis_item = xaxis_item
            
        if self.xaxis_item == 'RPM' and xaxis_item == 'WS':
            self.xaxis_item = 'WS'
        elif self.xaxis_item == 'WS' and xaxis_item == 'RPM':
            self.xaxis_item = 'RPM'
            
        # linewidth and markersizedefault
        lw                  = 1.0
        markersizedefault   = 3
        freq_lines = []
        damp_lines = []

        for atool in view_cfg.active_data:  # active tool
            for ads in view_cfg.active_data[atool]:  # active dataset
                if database[atool][ads]['frequency'] is not None:
                    # set xaxis item
                    if self.xaxis_item == 'WS':
                        xaxis_values = database[atool][ads]['operating_points'].loc[:, 'wind speed [m/s]']
                    else:
                        xaxis_values = database[atool][ads]['operating_points'].loc[:, 'rot. speed [rpm]']

                    # add active modes
                    # this can probably also be done without a loop and just with the indices
                    for mode_ID in view_cfg.active_data[atool][ads]:
                        if view_cfg.lines[atool][ads][mode_ID] is None:
                            ls = view_cfg.ls.ls()
                            freq_line, = self.axes1.plot(xaxis_values,
                                                         database[atool][ads].frequency.loc[:, mode_ID],
                                                         color=ls['color'],
                                                         linestyle=ls['linestyle'],
                                                         marker=ls['marker'],
                                                         linewidth=view_cfg.ls.lw,
                                                         label=ads + ': ' + database[atool][ads].modes.values[mode_ID].name,
                                                         markersize=view_cfg.ls.markersizedefault, picker=2)
                            damp_line, = self.axes2.plot(xaxis_values,
                                                         database[atool][ads].damping.loc[:, mode_ID],
                                                         color=ls['color'],
                                                         linestyle=ls['linestyle'],
                                                         marker=ls['marker'],
                                                         linewidth=view_cfg.ls.lw,
                                                         label=ads + ': ' + database[atool][ads].modes.values[mode_ID].name,
                                                         markersize=view_cfg.ls.markersizedefault, picker=2)
                            view_cfg.lines[atool][ads][mode_ID] = [freq_line, damp_line]
                        else:
                            freq_line = self.axes1.add_line(view_cfg.lines[atool][ads][mode_ID][0])
                            damp_line = self.axes2.add_line(view_cfg.lines[atool][ads][mode_ID][1])

                        freq_lines.append(freq_line)
                        damp_lines.append(damp_line)

                        if [[mode_ID], ads, atool] in view_cfg.selected_data:
                            # this does not necessarily have to be done with mplcursors + not sure if this is the most
                            # efficient way to do it
                            cursor = mplcursors.cursor([freq_line, damp_line], multiple=True, highlight=True)
                            cursor.add_highlight(freq_line)
                            cursor.add_highlight(damp_line)

                # plot p-harmonics if present
                if database[atool][ads].operating_points is not None and self.pharmonics is True:
                    P_harmonics = [1, 3, 6, 9, 12]
                    for index in P_harmonics:
                        P_hamonics_data = database[atool][ads].operating_points.loc[:, 'rot. speed [rpm]']/60*index  # rpm in Hz
                        self.axes1.plot(xaxis_values, P_hamonics_data,
                                        c='grey', linestyle='--', linewidth=0.75, label=str(index)+'P')

        self.axes2.legend(bbox_to_anchor=(1, 0), loc=3)

        # setup mplcursors behavior: multiple text boxes if lines are clicked, highlighting line, pairing of
        # frequency and damping lines
        cursor = mplcursors.cursor(freq_lines + damp_lines, multiple=True, highlight=True)
        pairs = dict(zip(freq_lines, damp_lines))
        pairs.update(zip(damp_lines, freq_lines))
        @cursor.connect("add")
        def on_add(sel):
            sel.extras.append(cursor.add_highlight(pairs[sel.artist]))
            sel.annotation.get_bbox_patch().set(fc="grey")
            for line in sel.extras:
                line.set(color="C3")

        self.canvas.draw()

    def UpdateMainPlot(self, myarg='WS'):
        """ Update main plot """
        if myarg == 'RPM':
            myxlabel = 'RPM in $1/min$'
        else:
            myxlabel = 'Wind Speed in m/s'
            
        if hasattr(self,'axes1') and self.initlimits==False:
            uxlim=self.axes1.get_xlim()
            uylim=self.axes1.get_ylim()
            uy2lim=self.axes2.get_ylim()
        else:        
            uxlim  = [3, 20]
            uylim  = [0, 4]
            uy2lim = [-1, 4]            
            self.initlimits = False
            
        self.main_plot(title='Campbell Diagram', xlabel=myxlabel, ylabel='Frequency in Hz', 
                       y2label='Damping Ratio in %', xlim=uxlim, ylim=uylim, y2lim=uy2lim, xaxis_item=myarg)

    def load_database(self):
        """ Load data from database (and use default view settings) """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filter = "CampbellViewer Database file (*.nc);;All Files (*)"
        fileName, _ = QFileDialog.getOpenFileName(self, "Open CampbellViewer Database", "", filter, options=options)

        # save "old" database
        old_database = copy.deepcopy(database)

        loaded_datasets = database.load(fname=fileName)
        for toolname in loaded_datasets:
            if toolname not in view_cfg.active_data:
                view_cfg.active_data[toolname] = dict()

            for datasetname in loaded_datasets[toolname]:
                view_cfg.active_data[toolname][datasetname] = np.arange(self.mode_minpara_cmb-1,self.mode_maxpara_cmb,1).tolist()

        self.dataset_tree_model.addModelData(old_database=old_database)
        self.dataset_tree_model.layoutChanged.emit()

    def save_database(self):
        """ Save data to database """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filter = "CampbellViewer Database file (*.nc);;All Files (*)"
        fileName, _ = QFileDialog.getSaveFileName(self, "Open CampbellViewer Database", "", filter, options=options)

        database.save(fname=fileName)

    def dataSelection(self):
        """ Select to add HAWCStab2 or Bladed data """
        self.popup = DataSelectionPopup()
        tool, datasetname = self.popup.selectTool()

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
        view_cfg.lines[toolname][datasetname] = [None]*len(database[toolname][datasetname].modes)

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


        # self.update_linestyledict()

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

        # self.update_linestyledict()

    def update_linestyledict(self):
        """
        Formerly: Mirror the FullModesDict to a dictionary with linestyles. Currently not used.  This functionality has
        to be updated to the current code structure.
        """
        color_sequence = ['r', 'g', 'b', 'y', 'c', 'm', 'k']
        line_style_sequence = ['-', '--', '-.', ':']
        filled_markers = ['o', 'v', '^', '<', '>', '8', 'p', 'h', 's', '*', 'H', 'D', 'd', 'P', 'X']
        full_list = list()
        for l in line_style_sequence:
            for m in filled_markers:
                for c in color_sequence:
                    full_list.append(c + l + m)

        view_cfg.LineStyleDict = dict()
        counter = 0
        for ds_name, mode_list in view_cfg.FullModesDict.items():
            view_cfg.LineStyleDict[ds_name] = full_list[counter:counter+len(mode_list)]
            counter = counter+len(mode_list)

    def plotPharmonics(self):
        """ Plot P-Harmonics in Campbell diagram """
        if self.pharmonics == True:
            self.pharmonics = False
        else:
            self.pharmonics = True
        self.UpdateMainPlot()

    ##############################################################
    # Open File Dialog for HAWCStab2 Campbell diagramm files
    def plotWSRPM(self):
        """ Switch between plot over wind speed or RPM"""
        try:
            if self.xaxis_item == 'RPM':
                myarg = 'WS'
            elif self.xaxis_item == 'WS':
                myarg = 'RPM'
            self.UpdateMainPlot(myarg)
        except:
            myarg = 'RPM'
            self.UpdateMainPlot(myarg)
            return

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
        self.popup = SettingsPopup(self.skip_header_CMB, self.skip_header_AMP, self.skip_header_OP)
        (self.skip_header_CMB, self.skip_header_AMP, self.skip_header_OP) = self.popup.getNewSettings()
        del self.popup

    def setLinestyleDefaults(self):
        """ This routine sets the default linestyle behaviour """
        self.popup = SettingsPopupLinestyle(self)
        del self.popup

    ##########
    # Tools
    ##########
    def initAmplitudes(self):
        """
        This routine initializes the window/plot of the participation factors on the amplitudes for a
        certain mode/dataset
        """
        self.popupAMP = SettingsPopupAMP()
        self.settingsAMPtool, self.settingsAMPdataset, self.settingsAMPmode = self.popupAMP.getNewSettings()
        del self.popupAMP

        if database[self.settingsAMPtool][self.settingsAMPdataset].frequency is not None and \
                database[self.settingsAMPtool][self.settingsAMPdataset].participation_factors_amp is not None:
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
        if database[self.settingsAMPtool][self.settingsAMPdataset].frequency is not None and \
                database[self.settingsAMPtool][self.settingsAMPdataset].participation_factors_amp is not None:
            self.AmplitudeWindow.configure_plotAMP(self.settingsAMPtool, self.settingsAMPdataset, self.settingsAMPmode,
                                                   database[self.settingsAMPtool][self.settingsAMPdataset],
                                                   self.AMPthreshold)
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




###################################################################
# Main program
###################################################################
if __name__ == '__main__':
    # enable error tracing
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
