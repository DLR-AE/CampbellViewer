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
# This is a first try to build a simple postprocessing GUI for HAWCStab2.
#
#
# Purpose: Create Campbell-Plots from HAWCStab2 result files (*.cmp, *.amp, *.op).
#
# author: J.Rieke - Nordex Energy GmbH
#
#
# --------------------------------------------------------------------------------------
# There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# --------------------------------------------------------------------------------------

import sys
import numpy as np

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout, QSizePolicy, QMessageBox, QWidget, QDialog
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QSpinBox
from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtGui  import QIcon
from PyQt5.QtCore import QFileInfo

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors

matplotlib.rcParams['hatch.color']     = 'grey'
matplotlib.rcParams['hatch.linewidth'] = 0.2

# activate clipboard --> not working currently!
#~ matplotlib.rcParams['toolbar'] = 'toolmanager'


####
# Some data classes
class AmpDataSensor(object):
    '''A small class for storing the amplitude data in a sorted way.'''
    def __init__(self, number_of_windspeeds, numberDOFs, number_of_modes):
        self.name      = []
        self.amplitude = np.empty([number_of_windspeeds, numberDOFs, number_of_modes])
        self.phase     = np.empty([number_of_windspeeds, numberDOFs, number_of_modes])

####
# Popup
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
        
        headerLinesCMBL   = QLabel('Number of header lines in Cambell file:')
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
    def __init__(self, settingsAMPmode):
        QDialog.__init__(self)
        
        self.settingsAMPmode = settingsAMPmode
        self.setWindowTitle("Set mode number for Amplitude plot")
        popup_layoutV        = QVBoxLayout(self)
        popup_layoutAMPmode  = QHBoxLayout(self)
        popup_layoutBttn     = QHBoxLayout(self)
        
        AMPmode          = QLabel('Number of amplitude mode to plot:')
        self.__AMPmode   = QSpinBox()
        self.__AMPmode.setValue(self.settingsAMPmode)
        popup_layoutAMPmode.addWidget(AMPmode)
        popup_layoutAMPmode.addWidget(self.__AMPmode)
        
        button_OK = QPushButton('OK', self)
        button_OK.clicked.connect(self.newSettings)
        popup_layoutBttn.addWidget(button_OK)
        button_Cancel = QPushButton('Cancel', self)
        button_Cancel.clicked.connect(self.ClosePopup)
        popup_layoutBttn.addWidget(button_Cancel)
        
        
        popup_layoutV.addLayout(popup_layoutAMPmode)
        popup_layoutV.addLayout(popup_layoutBttn)
        self.exec_()
        
    def getNewSettings(self):
        return(self.settingsAMPmode)        

    def newSettings(self):  
        self.settingsAMPmode = self.__AMPmode.value()
        self.on_apply = False
        self.close()        

    def ClosePopup(self):
        self.settingsAMPmode = -1
        self.close()        


####
# Main classes  self.AmpDataList.name
class TableModeListClass(QTableWidget):
    ''' Small custom table class'''
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def addList(self, ListOfItems):
        """Add items in list to table."""
        row    = len(ListOfItems)
        column = 1 # don't change this!
        self.setRowCount(row)
        self.setColumnCount(column)
        self.setHorizontalHeaderLabels(['Mode'])
        i=0
        for item in ListOfItems:
            self.setItem(i,0, QTableWidgetItem(item))
            i+=1
            
    def renewListNames(self,AmpDataList):
        """Update items in list to table."""
        i=0
        for item in AmpDataList:
            self.setItem(i,0, QTableWidgetItem(item))
            i+=1


class AmplitudeWindow(QMainWindow):
    def __init__(self,settingsAMPmode, data, numberDOFs, sensorList):
        super(AmplitudeWindow, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Amplitude Plot window")
        self.setMinimumWidth(1024)
        self.setMinimumHeight(800)
        
        self.settingsAMPmode = settingsAMPmode
        self.data            = data
        self.numberDOFs      = numberDOFs
        self.sensorList      = sensorList
        
        
        # Figure settings
        self.AMPfig    = Figure(figsize=(6, 6), dpi=100, tight_layout=True)
        self.AMPfig.subplots_adjust(0.06, 0.06, 0.88, 0.97) # left,bottom,right,top
        self.AMPcanvas = FigureCanvas(self.AMPfig)
        toolbar        = NavigationToolbar(self.AMPcanvas, self)
        
        self.main_widget  = QWidget(self)
        self.layout_mplib = QVBoxLayout(self.main_widget)
        self.layout_mplib.addWidget(toolbar)
        self.layout_mplib.addWidget(self.AMPcanvas)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        if hasattr(self,'axes1'):
            uxlim=self.axes1.get_xlim()
            uylim=self.axes1.get_ylim()
            uy2lim=self.axes2.get_ylim()
        else:            
            #~ uxlim  = [ 3,20]
            uxlim  = [self.data["campbell_data"][0,0],self.data["campbell_data"][-1,0]]
            uylim  = [0,1.1]
            uy2lim = [-180,180]
        
        self.main_plotAMP(title='Amplitude participations for mode '+str(self.settingsAMPmode), xlabel='Wind Speed in m/s', ylabel='normalized participation', 
                       y2label='phase angle in degree', xlim=uxlim, ylim=uylim,y2lim=uy2lim) 
        
    def main_plotAMP(self, title='Amplitudes', xlabel='', ylabel='', y2label='', xlim=None, ylim=None, y2lim=None, xscale='linear', yscale='linear'):
                
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
        
        
        mode_index=(self.settingsAMPmode-1)*self.numberDOFs*2+1
        
        for i in range(1,self.numberDOFs):
            csq  = color_sequence     [(i-1) % len(color_sequence)]
            if i > len(color_sequence):
                lssq = line_style_sequence[(i-1) % len(line_style_sequence)]
                mssq = filled_markers     [(i-1) % len(filled_markers     )]
            else:
                lssq = '-'
                mssq = ''
            self.axes1.plot(self.data["amplitude_data"][:,0], self.data["amplitude_data"][:,mode_index+  (i-1)*2],label=self.sensorList[i-1], 
                            linewidth=lw, c=csq, linestyle=lssq, marker=mssq, markersize=markersizedefault, picker=True, pickradius=2)
            self.axes2.plot(self.data["amplitude_data"][:,0], self.data["amplitude_data"][:,mode_index+1+(i-1)*2],label=self.sensorList[i-1], 
                            linewidth=lw, c=csq, linestyle=lssq, marker=mssq, markersize=markersizedefault, picker=True, pickradius=2)
  
  
        self.axes2.legend(bbox_to_anchor=(1, 0),loc=3)
        cursor_upper = mplcursors.cursor(self.axes1,multiple=True) # , highlight=True
        cursor_lower = mplcursors.cursor(self.axes2,multiple=True) # , highlight=True
        @cursor_upper.connect("add")
        def _(sel):
            sel.annotation.get_bbox_patch().set(fc="grey")
        @cursor_lower.connect("add")
        def _(sel):
            sel.annotation.get_bbox_patch().set(fc="grey")
        self.AMPcanvas.draw()
        
        
        

class ApplicationWindow(QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Application main window")
        
        self.data         = {}
        self.cmb_filename = None
        self.xaxis_item   = 'WS'
        
                
        ##############################################################
        # Menu items
        # FILE
        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Open HAWCStab2 Campbell result file', self.openFileNameDialogCMB, 
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction('&Open HAWCStab2 Amplitude result file', self.openFileNameDialogAMP, 
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_L)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
                
        # SETTINGS
        self.settings_menu = QMenu('&Settings', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.settings_menu)
        self.settings_menu.addAction('&Header Lines', self.setHeaderLines)
                
        # Tools
        self.tools_menu = QMenu('&Tools', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.tools_menu)
        self.tools_menu.addAction('&Plot amplitudes of modes', self.plotAmplitudes)
        
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
        self.layout_mpliblist.addLayout(self.layout_mplib,10)
        self.layout_mpliblist.addLayout(self.layout_list,1)
               
        
        
        ##############################################################
        # Table as Selection List
        self.myTable = TableModeListClass() 
        self.myTable.addList(["Tower SS", "Tower FA"])
        self.layout_list.addWidget(self.myTable,0)
        self.myTable.clicked.connect(self.RedrawCMBfromSelection)
        self.myTable.cellChanged.connect(self.RedrawCMBafterListChange)
        
        
        
        ##############################################################
        # Some defaults  
        self.mode_minpara_cmb = 1
        self.mode_maxpara_cmb = 10
        self.mode_max_cmb     = self.mode_maxpara_cmb  
        self.mode_min_cmb     = self.mode_minpara_cmb  
        self.pharmonics       = False
        self.skip_header_CMB  = 1                     # number of header lines in Campbell file
        self.skip_header_AMP  = 5                     # number of header lines in Amplitude file
        self.skip_header_OP   = 1                     # number of header lines in operational data file
        self.numberDOFs       = 15                    # number of degree of freedoms in amplitude file
        self.sensorList       = ['TWR x   ','TWR y   ','TWR yaw ','SFT x   ','SFT y   ','SFT tor ','Sym edge',
                                 'BW edge ','FW edge ','Sym flap','BW flap ','FW flap ','Sym tors','BW tors ','FW tors ']
        self.settingsAMPmode  = 1
        
        
        ##############################################################
        # Buttons
        self.button_cmb = QPushButton('Open HAWCStab2 Campbell diagramm result file', self)
        self.button_cmb.clicked.connect(self.openFileNameDialogCMB)
        self.button_layout.addWidget(self.button_cmb)
        self.button_amp = QPushButton('Open HAWCStab2 Amplitude result file', self)
        self.button_amp.clicked.connect(self.openFileNameDialogAMP)
        self.button_layout.addWidget(self.button_amp)
        self.button_op = QPushButton('Open HAWCStab2 Operational data file', self)
        self.button_op.clicked.connect(self.openFileNameDialogOP)
        self.button_layout.addWidget(self.button_op)
        self.button_extract = QPushButton('Extract mode names \n from amplitude result file', self)
        self.button_extract.clicked.connect(self.ExtractModeNames)
        self.button_layout.addWidget(self.button_extract)
        
        self.button_add = QPushButton('Add mode', self)
        self.button_add.clicked.connect(self.AddModeCMB)
        self.button_layout.addWidget(self.button_add)
        
        self.button_remove = QPushButton('Remove mode', self)
        self.button_remove.clicked.connect(self.RemoveModeCMB)
        self.button_layout.addWidget(self.button_remove)
        
        self.button_pharm = QPushButton('Plot P-Harmonics', self)
        self.button_pharm.clicked.connect(self.plotPharmonics)
        self.button_layout.addWidget(self.button_pharm)
        
        self.button_wsrpm = QPushButton('Switch Plot over\nRPM/Windspeed', self)
        self.button_wsrpm.clicked.connect(self.plotWSRPM)
        self.button_layout.addWidget(self.button_wsrpm)
        
        self.button_savepdf = QPushButton('Quick Save\nto PDF', self)
        self.button_savepdf.clicked.connect(self.savepdf)
        self.button_layout.addWidget(self.button_savepdf)
        
        
        ##############################################################
        # Figure settings
        #~ self.fig    = Figure(figsize=(6, 6), dpi=100, tight_layout=True)
        self.fig    = Figure(figsize=(6, 6), dpi=100)
        self.fig.subplots_adjust(0.06, 0.06, 0.88, 0.97) # left,bottom,right,top 
        self.canvas = FigureCanvas(self.fig)
        toolbar     = NavigationToolbar(self.canvas, self)
        
        # create figure with two axis
        self.axes1      = self.fig.add_subplot(211)
        self.axes2      = self.fig.add_subplot(212, sharex=self.axes1)
        self.initlimits = True                                         # True for init
        
        self.layout_mplib.addWidget(toolbar)         
        
        
        ##############################################################
        # Set Main Widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        self.statusBar().showMessage("All hail matplotlib!", 2000)
    
            #~ def onpick(self,event):
                #~ print('click', event)
                #~ thisline = event.artist
                #~ xdata = thisline.get_xdata()
                #~ ydata = thisline.get_ydata()
                #~ ind = event.ind
                #~ points = tuple(zip(xdata[ind], ydata[ind]))
                #~ print('onpick points:', points)
                #~ TODO get mode number/name from self.ActiveModeList
                #~ QMessageBox.information(self, "Info for mode","x-data:"+str(xdata[ind])+"\n"+"y-data:"+str(ydata[ind]))
            
        

    ##############################################################
    # Main plotting routine
    def main_plot(self, title='Campbell', xlabel='', ylabel='', y2label='', xlim=None, ylim=None, y2lim=None, xscale='linear', yscale='linear', xaxis_item='WS'):
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
        
        # Set item of x-axis = wind speed or RPM
        if not hasattr(self,'xaxis_item'):
            self.xaxis_item = xaxis_item
            
        if self.xaxis_item == 'RPM' and xaxis_item == 'WS':
            self.xaxis_item = 'WS'
        elif self.xaxis_item == 'WS' and xaxis_item == 'RPM':
            self.xaxis_item = 'RPM'
            
        # set markes and colors for plot
        color_sequence      = ['r','g','b','y','c','m','k']
        line_style_sequence = [ '-','--','-.',':']
        lw                  = 1.0
        filled_markers      = ['o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'X']
        markersizedefault   = 3
        
        (number_of_windspeeds, number_of_modes) = np.shape(self.data["campbell_data"])
        # num_datablocks_cmb = 2 for HS2 <= 2.13 from 2.14 on num_datablocks_cmb = 3
        num_datablocks_cmb = self.num_datablocks_cmb
        number_of_modes=int((number_of_modes-1)/num_datablocks_cmb)
                    
        if "campbell_data" in self.data:
            #~ self.axes2.fill_between(self.data["campbell_data"][:,0], y1=0, y2=-10, where=None, facecolor='grey', alpha=0.1, hatch='/')
            self.axes2.fill_between([0,30], y1=0, y2=-10, where=None, facecolor='grey', alpha=0.1, hatch='/')
            #~ self.axes2.axhline(y = 0, linewidth=2, color='r')
            
            # set xaxis item
            if self.xaxis_item == 'WS':
                xaxis_values = self.data["campbell_data"][:,0]
            else:
                if 'Operational_data' in self.data:
                    xaxis_values = self.data["Operational_data"][:,2]
                else:
                    QMessageBox.about(self, "WARNING from main plot","Operational data have to be loaded first!")
                    xaxis_values = self.data["campbell_data"][:,0]
            min_rpm = np.floor(np.amin(xaxis_values))
            max_rpm = np.ceil (np.amax(xaxis_values))
            self.axes1.set_xlim([min_rpm,max_rpm])
            
            #
            i = 0
            for counter, value in enumerate(self.ActiveModeList):
                csq  = color_sequence     [(counter) % len(color_sequence)]
                if counter > len(color_sequence)-1:
                    lssq = line_style_sequence[(counter) % len(line_style_sequence)]
                    mssq = filled_markers     [(counter) % len(filled_markers     )]
                else:
                    lssq = '-'
                    mssq = ''
                if hasattr(self, 'AmpDataList'):
                    self.axes1.plot(xaxis_values,self.data["campbell_data"][:,value+1 ], 
                                                           c=csq, linestyle=lssq, linewidth=lw, label=str(value+1)+' '+self.AmpDataList.name[value],
                                                           marker=mssq, markersize=markersizedefault, picker=True, pickradius=2)
                    self.axes2.plot(xaxis_values,self.data["campbell_data"][:,value+number_of_modes+1], 
                                                           c=csq, linestyle=lssq, linewidth=lw, label=str(value+1)+' '+self.AmpDataList.name[value],
                                                           marker=mssq, markersize=markersizedefault, picker=True, pickradius=2)
                else:
                    self.axes1.plot(xaxis_values,self.data["campbell_data"][:,value+1 ], 
                                                           c=csq, linestyle=lssq, linewidth=lw, label='mode '+str(value+1), 
                                                           marker=mssq, markersize=markersizedefault, picker=True, pickradius=2)
                    self.axes2.plot(xaxis_values,self.data["campbell_data"][:,value+number_of_modes+1], 
                                                           c=csq, linestyle=lssq, linewidth=lw, label='mode '+str(value+1), 
                                                           marker=mssq, markersize=markersizedefault, picker=True, pickradius=2)
            # plot p-harmonics if present
            if 'Operational_data' in self.data and self.pharmonics==True:
                P_harmonics = [1,3,6,9,12]
                #~ P_harmonics = [1,2,3,4,5,6,7,8,9,10,11,12]
                for index in P_harmonics:
                    P_hamonics_data = self.data["Operational_data"][:,2]/60*index # rpm in Hz
                    self.axes1.plot(xaxis_values,P_hamonics_data, 
                                    c='grey', linestyle='--', linewidth=0.75, label=str(index)+'P')                
                                    
            
            self.axes2.legend(bbox_to_anchor=(1, 0),loc=3)
            cursor_upper = mplcursors.cursor(self.axes1,multiple=True) # , highlight=True
            cursor_lower = mplcursors.cursor(self.axes2,multiple=True) # , highlight=True
            @cursor_upper.connect("add")
            def _(sel):
                sel.annotation.get_bbox_patch().set(fc="grey")
            @cursor_lower.connect("add")
            def _(sel):
                sel.annotation.get_bbox_patch().set(fc="grey")
            self.canvas.draw()  
            
        else:
            self.canvas.draw()
            
            
            
    def UpdateMainPlot(self,myarg='WS'):
        '''Update main plot ''' 
        if myarg == 'RPM':
            myxlabel = 'RPM in $1/min$'
        else:
            myxlabel = 'Wind Speed in m/s'
            
        if hasattr(self,'axes1') and self.initlimits==False:
            uxlim=self.axes1.get_xlim()
            uylim=self.axes1.get_ylim()
            uy2lim=self.axes2.get_ylim()
        else:        
            uxlim  = [self.data["campbell_data"][0,0],self.data["campbell_data"][-1,0]]
            uylim  = [ 0, 2]
            uy2lim = [-1, 2]            
            self.initlimits = False
            
        self.main_plot(title='Campbell Diagram', xlabel=myxlabel, ylabel='Frequency in Hz', 
                       y2label='Damping Ratio in %', xlim=uxlim, ylim=uylim, y2lim=uy2lim, xaxis_item=myarg) 
                       
    
    def AddModeCMB(self):
        ''' Add a mode to Campbell diagram'''       
        self.ActiveModeList.append(max(self.ActiveModeList)+1)
        self.UpdateMainPlot(self.xaxis_item) 
    
    def RemoveModeCMB(self):
        ''' Remove a mode to Campbell diagram''' 
        self.mode_max_cmb = self.mode_max_cmb - 1       
        del self.ActiveModeList[-1]
        self.UpdateMainPlot(self.xaxis_item)
    
    def RedrawCMBfromSelection(self):
        ''' Redraw the Campbell diagram with selected mode list'''    
        self.ActiveModeList = sorted(set(index.row() for index in self.myTable.selectedIndexes()))
        self.UpdateMainPlot(self.xaxis_item)
    
    def RedrawCMBafterListChange(self):
        ''' Redraw the Campbell diagram after renaming one element in mode list''' 
        rows = sorted(set(index.row() for index in self.myTable.selectedIndexes()))
        for row in rows:
            self.AmpDataList.name[row]=self.myTable.item(row,0).text()
        self.UpdateMainPlot(self.xaxis_item)
        
     
    ##############################################################
    # Open File Dialog for HAWCStab2 Campbell diagramm files
    def openFileNameDialogCMB(self):   
        '''Open File Dialog for HAWCStab2 Campbell diagramm files'''
        options  = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog 
        filter   = "HAWCStab2 campbell result files (*.cmb);;All Files (*)"
        fileName, _ = QFileDialog.getOpenFileName(self,"Open Campbell Files", "", filter, options=options)
        if QFileInfo(fileName).exists():
            # save info
            self.cmb_filename = fileName
            # get filename extension
            fileNameExtension = QFileInfo(fileName).suffix()
            # what kind of data are these
            if fileNameExtension=='cmb':
                # Get number of modes/damping values           
                with open(fileName, 'r') as f:
                    first_line = f.readlines()[0]
                    split_line = first_line.split()
                    self.num_modes_cmb      = int(split_line[len(split_line)-1])
                    self.num_datablocks_cmb = split_line.count(split_line[len(split_line)-1])
                with open(fileName, 'r') as f:
                    self.data["campbell_data"] = np.genfromtxt(f,skip_header=self.skip_header_CMB)
                    
                self.button_cmb.setStyleSheet("background-color:rgb(0,255,0)")
                last_backslash = fileName.rfind('/')
                self.button_cmb.setText('Open HAWCStab2 Campbell diagramm result file \n'+fileName[last_backslash:])
            else:
                return  

        
        # Create a list of all mode numbers in File
        # The Campbell files contain (mode number)*num_datablocks_cmb+1 columns
        # num_datablocks_cmb = 2 for HS2 <= 2.13 from 2.14 on num_datablocks_cmb = 3
        num_datablocks_cmb = self.num_datablocks_cmb
        self.modeList=[]
        data_shape=self.data["campbell_data"].shape
        for counter in range(0,int((data_shape[1]-1)/num_datablocks_cmb)):
            self.modeList.append("mode "+str(counter+1))       
        self.myTable.blockSignals(True)
        self.myTable.addList(self.modeList)       
        self.myTable.blockSignals(False)
                
        # plot the data immediately 
        self.ActiveModeList=np.arange(self.mode_minpara_cmb-1,self.mode_maxpara_cmb,1).tolist()
        self.UpdateMainPlot(self.xaxis_item)
        self.layout_mplib.addWidget(self.canvas)
        
        # get amp data with same name but different suffix
        try:
            suffix = QFileInfo(self.cmb_filename).suffix()
            amp_filename = self.cmb_filename.rstrip(suffix)+'amp'
            self.__get_amp_from_file(amp_filename)
        except:            
            QMessageBox.about(self, "WARNING","Filename root for amplitude file has different root name! Open separately!")
            
        # get op data with same name but different suffix
        try:
            suffix = QFileInfo(self.cmb_filename).suffix()
            op_filename = self.cmb_filename.rstrip(suffix)+'opt'
            self.__get_op_from_file(op_filename)
        except:            
            QMessageBox.about(self, "WARNING","Filename root for operational file has different root name! Open separately!")
     
     
    ##############################################################
    # Open File Dialog for HAWCStab2 Amplitude files
    def openFileNameDialogAMP(self):   
        ''' Open File Dialog for HAWCStab2 Amplitude files  
            - The first 5 rows contains header text.
            - Column 1 contains wind speeds.
            - Every mode has got 30 columns of sensor data for 15 sensors, each sensor has a normalized deflection/rotation and a phase.
              TWR x   [m]     phase [deg]     
              TWR y   [m]     phase [deg] 
              TWR yaw [rad]   phase [deg]     
              SFT x   [m]     phase [deg]     
              SFT y   [m]     phase [deg] 
              SFT tor [rad]   phase [deg]  
              Sym edge[m]     phase [deg]   
              BW edge [m]     phase [deg]   
              FW edge [m]     phase [deg]  
              Sym flap[m]     phase [deg]   
              BW flap [m]     phase [deg]   
              FW flap [m]     phase [deg]
              Sym tors[rad]   phase [deg] 
              BW tors [rad]   phase [deg] 
              FW tors [rad]   phase [deg]
        '''
        if "campbell_data" in self.data:
            options  = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            filter   = "HAWCStab2 amplitude result files (*.amp);;All Files (*)"
            fileName, _ = QFileDialog.getOpenFileName(self,"Open Aplitude Files", "", filter, options=options)
            if QFileInfo(fileName).exists():
                # get filename extension
                fileNameExtension = QFileInfo(fileName).suffix()
                # what kind of data are these
                if fileNameExtension=='amp':
                    self.__get_amp_from_file(fileName)
                else:
                    return    
        else:
            QMessageBox.about(self, "WARNING","Campbell data file has to be loaded first!")
            return 
            
    def __get_amp_from_file(self,fileName):
        with open(fileName, 'r') as f:
            self.data["amplitude_data"] = np.genfromtxt(f,skip_header=self.skip_header_AMP)
        self.button_amp.setStyleSheet("background-color:rgb(0,255,0)")
        last_backslash = fileName.rfind('/')
        self.button_amp.setText('Open HAWCStab2 Amplitude result file \n'+fileName[last_backslash:])
        
                
    ##############################################################
    # Open File Dialog for HAWCStab2 operational data files
    def openFileNameDialogOP(self):   
        '''Open File Dialog for HAWCStab2 operational data files'''
        if "campbell_data" in self.data and "amplitude_data" in self.data:
            options  = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog 
            filter   = "HAWCStab2 operational data files (*.op *opt);;All Files (*)"
            fileName, _ = QFileDialog.getOpenFileName(self,"Open Operational Data Files", "", filter, options=options)
            if QFileInfo(fileName).exists():
                # get filename extension
                fileNameExtension = QFileInfo(fileName).suffix()
                # what kind of data are these
                if fileNameExtension=='op' or fileNameExtension=='opt':
                    self.__get_op_from_file(fileName)
                else:
                    return  
        else:
            QMessageBox.about(self, "WARNING","Campbell and Amplitude files have to be loaded first!")
            return

    def __get_op_from_file(self,fileName):
        with open(fileName, 'r') as f:
            self.data["Operational_data"] = np.genfromtxt(f,skip_header=self.skip_header_OP)
        self.button_op.setStyleSheet("background-color:rgb(0,255,0)")
        last_backslash = fileName.rfind('/')
        self.button_op.setText('Open HAWCStab2 operational data file \n'+fileName[last_backslash:])
        self.plotPharmonics()
        self.ExtractModeNames()
        
                    
    ##################################################################
    #
    def plotPharmonics(self):
        ''' Plot P-Harmonics in Campbell diagram''' 
        if self.pharmonics==True:
            self.pharmonics=False
        else:
            self.pharmonics=True
        self.UpdateMainPlot(self.xaxis_item)

    def ExtractModeNames(self):
        '''This routine should interprete the amplitude result file, so that for 
           every mode a dedicated name can be derived.'''
        if "campbell_data" in self.data and "amplitude_data" in self.data:
            # split array in chunks
            (number_of_windspeeds, number_of_modes) = np.shape(self.data["amplitude_data"])
            number_of_modes  = int((number_of_modes-1)/(self.numberDOFs*2))
            if hasattr(self, 'AmpDataList'):
                del self.AmpDataList
            self.AmpDataList = AmpDataSensor(number_of_windspeeds, self.numberDOFs, number_of_modes)
            for i in range(0,number_of_modes):
                for j in range(0,self.numberDOFs):
                    amp_index   = i*self.numberDOFs*2+1+2*j
                    phase_index = i*self.numberDOFs*2+2+2*j
                    self.AmpDataList.amplitude[:,j,i] = self.data["amplitude_data"][:,amp_index  ]
                    self.AmpDataList.phase    [:,j,i] = self.data["amplitude_data"][:,phase_index]
            
            # determine dominant DOF per mode
            for i in range(0,number_of_modes):
                mean_DOF = np.mean(self.AmpDataList.amplitude[:,:,i],axis=0)
                self.AmpDataList.name.append(self.sensorList[np.argmax(mean_DOF)])
            
            # Override data for first two modes, because in HAWCStab2 tower amplitudes are not 1.0 although it is a tower mode.
            # Unfortunately, higher tower modes cannot be filtered easyly.
            self.AmpDataList.name[0]='Tower SS'
            self.AmpDataList.name[1]='Tower FA'
            self.myTable.blockSignals(True)
            self.myTable.renewListNames(self.AmpDataList.name)    
            self.myTable.blockSignals(False)
            self.UpdateMainPlot('WS')
        else:
            QMessageBox.about(self, "WARNING","Campbell and Amplitude files have to be loaded first!")
            return 
     
    ##############################################################
    # Open File Dialog for HAWCStab2 Campbell diagramm files
    def plotWSRPM(self):
        """ Switch between plot over wind speed or RPM"""
        if "Operational_data" not in self.data:
            QMessageBox.about(self, "WARNING","Operational data have to be loaded first!")
            return
        try:
          if self.xaxis_item == 'RPM':
              myarg = 'WS'
          elif self.xaxis_item == 'WS':            
              myarg = 'RPM' 
          self.xaxis_item = myarg
          self.UpdateMainPlot(myarg)  
        except:
          myarg = 'RPM' 
          self.xaxis_item = myarg  
          self.UpdateMainPlot(myarg)  
          return

    ###################
    # save plot
    def savepdf(self):
        """Saves the current plot to pdf with *.cmb filename"""
        if self.cmb_filename != None:
            # get filename extension
            fileNameExtension = QFileInfo(self.cmb_filename).suffix()
            pdf_filename = self.cmb_filename.strip(fileNameExtension)+'pdf'
            
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
        '''This routine overrides the default header line numbers for Campbell and Amplitude files'''
        self.popup=SettingsPopup(self.skip_header_CMB,self.skip_header_AMP,self.skip_header_OP)
        (self.skip_header_CMB,self.skip_header_AMP,self.skip_header_OP)=self.popup.getNewSettings()
        del self.popup

    ##########
    # Tools
    ##########
    def plotAmplitudes(self):
        '''This routine plot participation factors on the amplitudes for a certain mode'''
        if "campbell_data" in self.data and "amplitude_data" in self.data:
            self.popupAMP=SettingsPopupAMP(self.settingsAMPmode)
            (self.settingsAMPmode)=self.popupAMP.getNewSettings()
            del self.popupAMP
            
            if self.settingsAMPmode > 0:
                self.AmplitudeWindow = AmplitudeWindow(self.settingsAMPmode, self.data, self.numberDOFs, self.sensorList) 
                self.AmplitudeWindow.show()
            elif self.settingsAMPmode == 0:
                QMessageBox.about(self, "WARNING","Mode numer has to be greater than 0!")
                return
            elif self.settingsAMPmode < 0:
                return
        else:
            QMessageBox.about(self, "WARNING","Campbell and Amplitude files have to be loaded first!")
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
