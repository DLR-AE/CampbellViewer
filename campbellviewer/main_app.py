"""
Disclaimer
-----------------------------------------------------------------

Simple postprocessing GUI for wind turbine linearization results.

Purposes:
- Create Interactive Campbell-Plots
- Participation plots
- Mode visualizations
- etc.

.. note::
    CampbellViewer is free software distributed under license conditions as stated in
    the file LICENSE, which is part of the repository.

    There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR
    PURPOSE.

authors:
- J. Rieke - Nordex Energy SE & Co. KG
- H. Verdonck - DLR
- O. Hach - DLR
- N. Joeres - Nordex Energy SE & Co. KG

"""

from __future__ import annotations
import sys
import os
import numpy as np
import copy
import argparse
import importlib.resources

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout, QMessageBox, QWidget,
    QFileDialog, QPushButton, QLabel, QCheckBox, QComboBox, QTreeView
    )
from PyQt5.QtGui  import QIcon
from PyQt5.QtCore import QFileInfo, Qt, QItemSelectionModel, QSettings

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
from campbellviewer.dialogs.dialogs import (
    SettingsPopupModeFilter,
    SettingsPopupLinestyle,
    SettingsPopupDataSelection,
    SettingsPopupAEMode,
    SettingsPopupAMP,
    GeneralSettingsDialog
    )

matplotlib.use("Qt5Agg")
matplotlib.rcParams['hatch.color']     = 'grey'
matplotlib.rcParams['hatch.linewidth'] = 0.2

# activate clipboard --> not working currently!
#~ matplotlib.rcParams['toolbar'] = 'toolmanager'


class AmplitudeWindow(QMainWindow):
    """Separate window for participation factor plot

    Attributes:
        requested_toolname (str): Name of the tool which is analysed
        settingsAMPmode (int): ID of the mode which is analysed
        AMPmode_name (str): Name of the mode which is analysed
        dataset (AbstractLinearizationData): Dataset to be analysed
        AMPthreshold (float): Threshold determining which participation modes are visualized, i.e. only modes with
            a significant participation are shown.
            e.g. threshold = 0.05 = only modes with more than 5% amplitude participation are shown in amplitude plot
        xaxis_param (str): string defining which operating parameter is on the x axis
        AMPfig: Matplotlib figure
        AMPcanvas: Matplotlib figure canvas
        main_widget (QWidget): Main widget
        layout_mplib (QVBoxLayout): Layout for the participation diagram widget
        axes1: matplotlib axes for the magnitude of the participation modes
        axes2: matplotlib axes for the phase of the participation modes
    """
    sigClosed = QtCore.pyqtSignal()

    def __init__(self):
        """ Initializes QMainWindow for the participation plots"""
        super(AmplitudeWindow, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Amplitude Plot window")
        self.setMinimumWidth(1024)
        self.setMinimumHeight(800)

    def configure_plotAMP(self, requested_toolname: str, requested_datasetname: str, requested_mode_id: int,
                          dataset, xaxis_param: str, threshold: float) -> None:
        """Configures matplotlib figure for participation plot

        Args:
            requested_toolname: name of the tool which will be analysed
            requested_datasetname: name of the dataset which will be analysed
            requested_mode_id: index of the mode which will be analysed
            dataset: AbstractLinearizationData dataset to be analysed
            xaxis_param: string defining which operating parameter is on the x axis
            threshold: Threshold determining which participation modes are visualized, i.e. only modes with
                a significant participation are shown.
        """
        self.requested_toolname = requested_toolname
        self.requested_datasetname = requested_datasetname
        self.settingsAMPmode = requested_mode_id
        self.AMPmode_name = database[requested_toolname][requested_datasetname].ds.modes.values[requested_mode_id].name
        self.dataset = dataset
        self.AMPthreshold = threshold  # only modes with (threshold*100)% amplitude participation are shown in amplitude plot
        self.xaxis_param = xaxis_param

        # Figure settings
        self.AMPfig = Figure(figsize=(6, 6), dpi=100, tight_layout=True)
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

        self.main_plotAMP(title=f'Amplitude participations for tool {requested_toolname}, '+
                                f'\ndataset {requested_datasetname}, {self.AMPmode_name}, '+
                                f'visibility threshold = {self.AMPthreshold:.2f}',
                          xlabel=view_cfg.xparam2xlabel(self.xaxis_param), ylabel='normalized participation',
                          y2label='phase angle in degree', xlim=view_cfg.axes_limits[0], ylim=uylim, y2lim=uy2lim)

    def main_plotAMP(self,
                     title: str='Amplitudes',
                     xlabel: str='',
                     ylabel: str='',
                     y2label: str='',
                     xlim: list=None,
                     ylim: list=None,
                     y2lim: list=None) -> None:
        """
        Fill the participation plot

        Args:
            title: title for the participation factors plot
            xlabel: label for the x-axis of the participation factors plot
            ylabel: label for the y-axis of the magnitude participation factors plot
            y2label: label for the y-axis of the phase participation factors plot
            xlim: limits for the x-axis of the participation factors plot
            ylim: limits for the y-axis of the magnitude participation factors plot
            y2lim: limits for the x-axis of the phase participation factors plot
        """

        # define figure with 2 subplots
        self.axes1 = self.AMPfig.add_subplot(211)
        self.axes2 = self.AMPfig.add_subplot(212, sharex=self.axes1)

        # We want the axes cleared every time plot() is called
        self.axes1.clear()
        self.axes2.clear()

        # Set label, grid, etc...
        self.AMPfig.suptitle(title)
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
                ls = mpl_ls.new_ls(self.requested_toolname, self.requested_datasetname)
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

        self.axes1.legend(loc='center right', bbox_to_anchor=(1.20,0.0))

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
    """
    QTreeView of the dataset tree (described by the TreeModel in model_lib)

    Attributes:
        aw (ApplicationWindow): ApplicationWindow in which tree is embedded
        tree_model (TreeModel): QAbstractItemModel which governs all the functionalities of the datatree
    """
    def __init__(self, tree_model: TreeModel, aw: ApplicationWindow):
        super(DatasetTree, self).__init__()
        self.aw = aw
        self.tree_model = tree_model
        self.setModel(tree_model)
        self.setSelectionMode(3)  # ExtendedSelection
        self.selectionModel().selectionChanged.connect(tree_model.updateSelectedData)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def keyPressEvent(self, event):
        """ If the delete key is pressed on the datatree, all selected data has to be deleted """
        if event.key() == QtCore.Qt.Key_Delete:
            self.tree_model.delete_data(self.selectedIndexes())

    def showContextMenu(self, position):
        """ A context menu is shown for the TreeView """
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
                popupAEMode = SettingsPopupAEMode(idx.internalPointer().itemData.name,
                                                  idx.internalPointer().itemData.symmetry_type,
                                                  idx.internalPointer().itemData.whirl_type,
                                                  idx.internalPointer().itemData.wt_component)
                self.tree_model.modify_mode_description(idx.internalPointer(), popupAEMode.get_settings())
                del popupAEMode
            elif action == showAmplitudes:
                modeID, dataset, tool = self.tree_model.get_branch_from_item(idx.internalPointer())
                self.aw.initAmplitudes(popup=False, chosen_mode=[tool, dataset, modeID[0]])
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
            self.tree_model.filter_checked(idx.internalPointer(), self.popupFilterModes.get_settings(),
                                           selection=self.selectedIndexes())
            del self.popupFilterModes
        elif action == deleteThisItem:
            self.tree_model.delete_data([idx])
        elif action == deleteAllSelected:
            self.tree_model.delete_data(self.selectedIndexes())


class ApplicationWindow(QMainWindow):
    """Main window of the GUI

    Attributes:
        file_menu (QMenu): Dropdown menu for file operations (loading/saving data)
        settings_menu (QMenu): Dropdown menu for managing GUI settings
        tools_menu (QMenu): Dropdown menu for additional tools to interact or visualize data
        help_menu (QMenu): Dropdown help menu
        main_layout (QVBoxLayout): Layout widget containing all widgets
        button_layout (QHBoxLayout): Layout widget containing interactive buttons
        layout_mplib (QVBoxLayout): Layout widget containing matplotlib plot
        layout_list (QVBoxLayout): Layout widget containing data tree
        layout_mpliblist (QHBoxLayout): Layout widget containing matplotlib and data tree
        dataset_tree_model (TreeModel): Model for the dataset tree
        dataset_tree (DatasetTree): View for the dataset tree
        fig (Figure): Matplotlib figure
        canvas (FigureCanvas): Canvas of the matplotlib figure
        legend (mpl.legend): Legend of the Matplotlib plot
        axes1 (mpl.ax): frequency plot axes of the matplotlib figure
        axes2 (mpl.ax): damping plot axes of the matplotlib figure
        right_mouse_press (bool): Flag for storing right mouse press on matplotlib figure
        cursor (mplcursors.cursor): Cursor object
        button_pharm (QPushButton): Button to toggle plotting P-harmonics
        button_xaxis (QComboBox): Button to select xaxis parameter
        xaxis_param (str): xaxis parameter
        xaxis_selection_box (QVBoxLayout): Layout for xaxis button + text
        button_savepdf (QPushButton): Button to save matplotlib figure to pdf
        button_rescale (QPushButton): Button to rescale Matplotlib figure
        pick_markers (bool): Flag whether markers in the matplotlib plot can be picked by mplcursors
        pick_markers_box (QCheckBox): Toggling picking markers or picking lines
        __CV_settings (dict): dictionary containing settings
    """

    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Application main window")

        ##############################################################
        # Menu items
        # FILE
        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Add New Dataset', self.dataSelection,
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
        self.settings_menu.addAction('&General Settings', self.open_general_settings)
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
        self.button_layout    = QHBoxLayout()
        self.layout_mplib     = QVBoxLayout()
        self.layout_list      = QVBoxLayout()
        self.layout_mpliblist = QHBoxLayout()

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
        # Signals from the tree model.
        # -> layoutChanged signals are used to update the main plot
        # -> dataChanged signals are used to update the tree view
        self.dataset_tree_model.layoutChanged.connect(self.UpdateMainPlot)

        ##############################################################
        # init QSettings for setting/getting user defaults settings
        self.__qsettings = QSettings('CampbellViewer')
        self.settings = GeneralSettingsDialog(self.__qsettings)
        self.settings.saved.connect(self.update_settings)

        ##############################################################
        # Get default settings
        self.update_settings()

        ##############################################################
        # Figure settings
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        toolbar = NavigationToolbar(self.canvas, self)
        self.layout_mplib.addWidget(toolbar)
        self.layout_mplib.addWidget(self.canvas)
        self.legend = None

        # create figure with two axis
        self.axes1      = self.fig.add_subplot(211)
        self.axes2      = self.fig.add_subplot(212, sharex=self.axes1)
        self.right_mouse_press = False
        self.cursor = None

        ##############################################################
        # Set Main Widget
        # This next line makes sure that key press events arrive in the matplotlib figure (e.g. to use 'x' and
        # 'y' for fixing an axis when zooming/panning)
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.statusBar().showMessage("GUI started", 2000)

        ##############################################################
        # Set buttons
        self.button_pharm = QPushButton('Plot P-Harmonics', self)
        self.button_pharm.setCheckable(True)
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
        self.button_savepdf.clicked.connect(self.save_pdf)
        self.button_layout.addWidget(self.button_savepdf)

        self.button_rescale = QPushButton('Rescale plot limits', self)
        self.button_rescale.clicked.connect(self.rescale_plot_limits)
        self.button_layout.addWidget(self.button_rescale)

        self.pick_markers = False
        self.pick_markers_box = QCheckBox('Pick markers', self)
        self.pick_markers_box.clicked.connect(self.add_or_remove_scatter)
        self.button_layout.addWidget(self.pick_markers_box)

    ##############################################################
    # Matplotlib and Matplotlib callback methods
    ##############################################################
    def UpdateMainPlot(self):
        """ Update main plot. This wrapping method currently does not make sense, but could be reimplemented later. """
        self.main_plot(title='Campbell Diagram', xlabel=view_cfg.xparam2xlabel(self.xaxis_param),
                       ylabel='Frequency in Hz', y2label='Damping Ratio in %')

    def main_plot(self, title: str='Campbell', xlabel: str='', ylabel: str='', y2label: str=''):
        """ Main plotting routine for the Campbell diagram

        Uses the information in the database and the view_cfg settings to make matplotlib plot. Matplotlib axes are
        completely cleared and re-filled.

        Args:
            title: Title for the plot
            xlabel: X-label for the Campbell diagram axes
            ylabel: Y-label for the frequency diagram
            y2label: Y-label for the damping diagram
        """

        # get the possibly user-modified axes limits, it would be good to have a signal when the axes limits are changed
        view_cfg.axes_limits = (self.axes1.get_xlim(), self.axes1.get_ylim(), self.axes2.get_ylim())

        # We want the axes cleared every time plot() is called
        self.axes1.clear()
        self.axes2.clear()
        if self.legend is not None:
            self.legend.remove()

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
        pharm_lines = []
        freq_scatters = []
        damp_scatters = []
        lines_to_be_selected = []

        for atool in view_cfg.active_data:  # active tool
            for ads in view_cfg.active_data[atool]:  # active dataset
                if database[atool][ads].ds['frequency'].values.ndim != 0:

                    # get xaxis values
                    if self.xaxis_param not in database[atool][ads].ds.operating_parameter:
                        self.statusBar().showMessage('WARNING: Operating condition {} is not available in the {}-{} '
                                                     'dataset. The data will not be '
                                                     'plotted.'.format(self.xaxis_param, atool, ads), 4000)
                        continue
                    else:
                        xaxis_values = database[atool][ads].ds['operating_points'].loc[:, self.xaxis_param]

                    # add active modes
                    # this can probably also be done without a loop and just with the indices
                    for mode_ID in view_cfg.active_data[atool][ads]:
                        if view_cfg.lines[atool][ads][mode_ID] is None:
                            ls = view_cfg.ls.new_ls(atool, ads)
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
                                                         # disabled to avoid double entries in legend
                                                         # label=ads + ': ' + database[atool][ads].ds.modes.values[mode_ID].name,
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
                            # disabled to avoid double entries in legend (if this is changed the mplcursors on_add
                            # method should be updated)
                            # damp_line.set_label(ads + ': ' + database[atool][ads].ds.modes.values[mode_ID].name)
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
                if database[atool][ads].ds.operating_points.values.ndim != 0 and self.__CV_settings['pharmonics']:
                    if self.__CV_settings['pharmonics']:
                        self.button_pharm.setChecked(True)
                    P_harmonics = [1, 3, 6, 9, 12]
                    for index in P_harmonics:
                        P_hamonics_data = database[atool][ads].ds.operating_points.loc[:, 'rot. speed [rpm]']/60.*index  # rpm in Hz
                        pharm_line, = self.axes1.plot(xaxis_values, P_hamonics_data,
                                        c='grey', linestyle='--', linewidth=0.75, label=str(index)+'P')
                        pharm_lines.append(pharm_line)

        # create a figure legend on the right edge and shrink the axes box accordingly
        # legend font size is decreased to make it fit - or disabled
        # Add a legend
        for fontsize in ['medium', 'small', 'x-small', 'xx-small', None]:
            if fontsize is None:
                bbox.x0 = 1
                break
            self.legend = self.fig.legend(loc='center right', fontsize=fontsize)
            bbox = self.legend.get_window_extent(self.fig.canvas.get_renderer()).transformed(self.fig.transFigure.inverted())
            if bbox.y1 < 1:
                break
            self.legend.remove()
            self.legend = None
        if self.legend is None:
            self.statusBar().showMessage('Legend disabled (too big for canvas)', 4000)
        self.fig.tight_layout(rect=(0, 0, bbox.x0, 1), h_pad=0.5, w_pad=0.5)

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

            self.cursor_p = mplcursors.cursor(pharm_lines, multiple=True)

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
                sel.annotation.get_bbox_patch().set(fc="cornflowerblue")

        else:
            # setup mplcursors behavior: multiple text boxes if lines are clicked, highlighting line, pairing of
            # frequency and damping lines
            if self.cursor is not None:
                self.cursor.remove()  # cleanup
            self.cursor = mplcursors.cursor(freq_lines + damp_lines, multiple=True, highlight=True,
                                       highlight_kwargs={'color': 'C3', 'linewidth': view_cfg.ls.lw+2,
                                                         'markerfacecolor': 'C3',
                                                         'markersize': view_cfg.ls.markersizedefault+2})
            self.cursor_p = mplcursors.cursor(pharm_lines, multiple=True)

            for line in lines_to_be_selected:
                self.cursor.add_highlight(line)

            pairs = dict(zip(freq_lines, damp_lines))
            pairs.update(zip(damp_lines, freq_lines))

            @self.cursor.connect("add")
            def on_add(sel):
                self.on_mpl_cursors_pick(sel.artist, 'select')
                sel.extras.append(self.cursor.add_highlight(pairs[sel.artist]))
                sel.annotation.get_bbox_patch().set(fc="grey")
                if sel.artist.axes == self.axes2:
                    # line in damping plot is selected -> these lines do not have a label -> so manually add label
                    # to cursor text box
                    sel.annotation.set_text(pairs[sel.artist].get_label() + '\n' + sel.annotation.get_text())

            @self.cursor.connect("remove")
            def on_remove(sel):
                self.on_mpl_cursors_pick(sel.artist, 'deselect')

            @self.cursor_p.connect("add")
            def on_add(sel):
                sel.annotation.get_bbox_patch().set(fc="cornflowerblue")

        self.canvas.draw()
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_mpl_cursors_pick(self, artist: matplotlib.artist.Artist, select: str):
        """ Callback function for picking matplotlib artists

        This function will update the selection in the dataset_tree based on the highlighting of lines in the
        matplotlib plots.

        Args:
            artist: Element of the matplotlib plot that has been picked
            select: String indicating if the artist is selected or deselected
        """

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
        """ Matplotlib Callback function for mouse motion.

        A vertical line is plotted at the mouse position if the right
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

    def on_release(self, event):
        """ Callback function for mouse release events. This does not necessarily have to be a matplotlib callback. """
        if event.button is MouseButton.RIGHT:
            self.right_mouse_press = False

    def find_data_of_highlights(self):
        """
        Gives a list with identification of all lines which are highlighted in the plot. Note that this is not
        necessarily the same as the selected_data in the ViewSettings.

        Returns:
            selected_lines (list) : List of lists with name of the tool, name of the dataset and mode ID for each
                highlighted line
        """
        selected_lines = []
        for atool in view_cfg.lines:
            for ads in view_cfg.lines[atool]:
                for mode_ID, mode_lines in enumerate(view_cfg.lines[atool][ads]):
                    if mode_lines is not None:

                        for sel in self.cursor.selections:
                            if sel.artist in mode_lines:
                                # print('Selections are:', atool, ads, mode_ID)
                                selected_lines.append([atool, ads, mode_ID])

        return selected_lines

    def add_or_remove_scatter(self, tick_flag):
        """ Add or remove scatter points to the matplotlib plot

        Normally the modes in the frequency and damping diagram are shown as Line2D objects. These lines can be
        highlighted by clicking on them (mplcursors). In order to be able to select individual points in the
        Campbell diagram (e.g. as input for mode visualization), an additional scatter plot can be overlayed on the
        Line2D objects.

        Args:
            tick_flag: Qt.Checked or Qt.Unchecked flag
        """
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

    ##############################################################
    # Database methods
    ##############################################################
    def load_database(self):
        """ Load data from database (and use default view settings) """
        db_filename = self.get_database_filename(mode='load')
        self.apply_database(db_filename)

    def save_database(self):
        """ Save data to database """
        db_filename = self.get_database_filename(mode='save')

        if db_filename[-3:] != ".nc":
            db_filename = db_filename + ".nc"

        database.save(fname=db_filename)

    def get_database_filename(self, mode: str) -> str:
        """ Use a QFileDialog to get the filename where the database can be loaded or saved.

        Args:
            mode : 'load' or 'save' -> identifier if a database filename has to be found to load or save a database

        Raises:
            ValueError : if mode is not 'load' or 'save'

        Returns:
            db_filename : string with database filename
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filter = "CampbellViewer Database file (*.nc);;All Files (*)"
        __path = self.__qsettings.value("IO/data_base", os.path.expanduser("~"))
        if mode == 'load':
            db_filename, _ = QFileDialog.getOpenFileName(self, "Load CampbellViewer Database", __path, filter, options=options)
            self.__qsettings.setValue("IO/data_base", db_filename)
        elif mode == 'save':
            db_filename, _ = QFileDialog.getSaveFileName(self, "Save to CampbellViewer Database", __path, filter, options=options)
            self.__qsettings.setValue("IO/data_base", db_filename)
        else:
            raise ValueError('mode to get a database filename can only be \'load\' or \'save\'')

        return db_filename

    def apply_database(self, db_filename: str):
        """ Load the database from the db_filename and apply it in the CampbellViewer

        Args:
            db_filename : string with the path to the database file which has to be applied
        """
        # save "old" database
        old_database = copy.deepcopy(database)

        loaded_datasets = database.load(fname=db_filename)
        for toolname in loaded_datasets:
            for datasetname in loaded_datasets[toolname]:
                self.init_active_data(toolname, datasetname)

        self.dataset_tree_model.addModelData(old_database=old_database)
        self.dataset_tree_model.layoutChanged.emit()

    ##############################################################
    # Adding new data methods
    ##############################################################
    def dataSelection(self):
        """ Select HAWCStab2 or Bladed data to add to GUI

        - Uses a SettingsPopupDataSelection popup to select from which tool data
          will be loaded and which (unique) name the dataset will get.

        - Loads the data through a fileDialog.
        - Adds the data the dataset tree model

        """
        self.popup = SettingsPopupDataSelection()
        tool, datasetname = self.popup.get_settings()

        if '&' in datasetname:
            self.statusBar().showMessage('& is not allowed in the datasetname', 4000)
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

    def init_active_data(self, toolname: str, datasetname: str):
        """ Initialize the active_data and lines global variables for this toolname/datasetname combination

        The active_data global variable is a dictionary storing the information which modes currently have to be
        plotted. The lines global variable will store the Line2D objects when the data has been plotted.
        """
        if toolname not in view_cfg.active_data:
            view_cfg.active_data[toolname] = dict()
            view_cfg.lines[toolname] = dict()
        view_cfg.active_data[toolname][datasetname] = np.arange(self.__CV_settings['mode_minpara_cmb']-1,
                                                                self.__CV_settings['mode_maxpara_cmb'], 1).tolist()
        view_cfg.lines[toolname][datasetname] = [None]*len(database[toolname][datasetname].ds.modes)

        # add the (unique) operating parameters of this dataset to the xaxis button.
        if len(self.button_xaxis) == 0:
            # this is first data added -> Use "wind speed [m/s]" as default operating parameter if it is in the
            # operating parameter list of the dataset.
            self.button_xaxis.addItems(database[toolname][datasetname].ds.operating_parameter.data)
            if 'wind speed [m/s]' in database[toolname][datasetname].ds.operating_parameter.data:
                self.button_xaxis.setCurrentText('wind speed [m/s]')
        else:
            # only add unique parameters
            self.button_xaxis.addItems(list(set(database[toolname][datasetname].ds.operating_parameter.data).difference(
                                           set([self.button_xaxis.itemText(i) for i in range(self.button_xaxis.count())]))))
        self.button_xaxis.model().sort(0)

    def openFileNameDialogHAWCStab2(self, datasetname: str='default'):
        """ Open File Dialog for HAWCStab2 Campbell diagram files

        Args:
            datasetname: Name that will be given to the selected dataset in the database
        """
        suffix_options = ['cmb', 'amp', 'opt']
        file_name_descriptions = ['Campbell Result Files',
                                  'Amplitude Result Files',
                                  'Operational Data Files']
        for suffix, descr in zip(suffix_options, file_name_descriptions):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            filter = "HAWCStab2 {} (*.{});;All Files (*)".format(descr, suffix)
            __path = self.__qsettings.value("IO/HS2_project", os.path.expanduser("~"))
            fileName, _ = QFileDialog.getOpenFileName(self, "Open {}".format(descr), __path, filter, options=options)

            if QFileInfo(fileName).exists():
                # get filename extension
                fileNameExtension = QFileInfo(fileName).suffix()
                # what kind of data are these
                if fileNameExtension == suffix:
                    database.add_data(datasetname, 'hawcstab2',
                                      tool_specific_info={'filename{}'.format(suffix): fileName,
                                                          'skip_header_CMB': self.__CV_settings['skip_header_CMB'],
                                                          'skip_header_AMP': self.__CV_settings['skip_header_AMP'],
                                                          'skip_header_OP': self.__CV_settings['skip_header_OP']})
                # save location to settings
                self.__qsettings.setValue("IO/HS2_project", QFileInfo(fileName).absolutePath())

    def openFileNameDialogBladedLin(self, datasetname: str='default'):
        """ Open File Dialog for Bladed linearization Campbell diagram files

        Args:
            datasetname: Name that will be given to the selected dataset in the database
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filter = "Bladed Linearization Result Files (*.$PJ);;All Files (*)"
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Bladed Linearization Result Files", "", filter, options=options)

        if QFileInfo(fileName).exists():
            result_dir = QFileInfo(fileName).absolutePath()
            result_prefix = QFileInfo(fileName).baseName()
            database.add_data(datasetname, 'bladed-lin',
                              tool_specific_info={'result_dir': result_dir, 'result_prefix': result_prefix})

    ##############################################################
    # Button action methods
    ##############################################################
    def plotPharmonics(self):
        """ Plot P-Harmonics in Campbell diagram """
        if self.__CV_settings['pharmonics']:
            self.button_pharm.setChecked(False)
            self.__CV_settings['pharmonics'] = False
        else:
            self.button_pharm.setChecked(True)
            self.__CV_settings['pharmonics'] = True
        self.UpdateMainPlot()

    def xaxis_change(self, text: str):
        """ Modify the data if the user requests a different variable on the x-axis

        - set the xaxis_param
        - modify all xaxis values of all lines
        - update the main plot

        Args:
            text: Identifier for the x-axis parameter

        """
        self.xaxis_param = text
        # modify the xaxis values of all lines
        for tool in view_cfg.lines:
            for ds in view_cfg.lines[tool]:
                if text not in database[tool][ds].ds.operating_parameter:
                    view_cfg.reset_these_lines(tool=tool, ds=ds)
                else:
                    for mode_lines in view_cfg.lines[tool][ds]:
                        if mode_lines is not None:
                            for artist in mode_lines:  # freq. and damp. lines
                                if isinstance(artist, matplotlib.lines.Line2D):
                                    artist.set_xdata(database[tool][ds].ds["operating_points"].sel(operating_parameter=text))
                                else:
                                    scatter_offsets = artist.get_offsets()
                                    scatter_offsets[:, 0] = database[tool][ds].ds["operating_points"].sel(operating_parameter=text)
                                    artist.set_offsets(scatter_offsets)

        view_cfg.auto_scaling_x = True
        self.UpdateMainPlot()

    def rescale_plot_limits(self):
        """ Rescale the limits of the Matplotlib plot to make all data fit """
        view_cfg.auto_scaling_x = True
        view_cfg.auto_scaling_y = True
        self.UpdateMainPlot()

    def save_pdf(self):
        """ Saves the current plot to pdf. """

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        ffilter = "Quick save of Campbell diagram PDF file (*.pdf)"
        __file = self.__qsettings.value("IO/pdf", os.path.expanduser("~"))
        pdf_filename, _ = QFileDialog.getSaveFileName(self,
                                                      "Save to CampbellViewer Database",
                                                      __file,
                                                      ffilter,
                                                      options=options)
        if pdf_filename:
            if not pdf_filename.endswith('.pdf'):
                pdf_filename += '.pdf'
            self.__qsettings.setValue("IO/pdf", pdf_filename)
            self.fig.savefig(pdf_filename)

    ##########
    # Settings
    ##########
    def open_general_settings(self) -> None:
        """opens the settings popup"""
        self.settings.exec_()


    def set_settings_to_default(self, save: bool = False) -> None:
        """retrieves the default values or settings

        Args:
            save: set True, if settings should be written to QSettings, default False

        mode_minpara_cmb (int): Default minimum mode index to be shown when loading new data
        mode_maxpara_cmb (int): Default maximum mode index to be shown when loading new data
        pharmonics (bool): Flag for showing P harmonics
        skip_header_CMB (int): Number of header lines in HAWCStab2 Campbell file
        skip_header_AMP (int): Number of header lines in HAWCStab2 Amplitude file
        skip_header_OP (int): Number of header lines in HAWCStab2 Operational file

        """
        # defaults
        self.__CV_settings = {'mode_minpara_cmb'  : 1,
                              'mode_maxpara_cmb'  : 6,
                              'pharmonics'        : False,
                              'skip_header_CMB'   : 1,
                              'skip_header_AMP'   : 5,
                              'skip_header_OP'    : 1,
                              'amp_part_threshold': 0.5}

        if save:
            for settings_key in self.__CV_settings:
                self.__qsettings.setValue(settings_key, self.__CV_settings[settings_key])


    def update_settings(self) -> None:
        """retrieves the default values or the user specific settings from QSettings"""
        # defaults
        self.set_settings_to_default(save=False)

        # try to get the user settings
        for settings_key in self.__CV_settings:
            if self.__qsettings.contains(settings_key):
                user_setting = self.__qsettings.value(settings_key)
                if isinstance(self.__CV_settings[settings_key],float):
                    self.__CV_settings[settings_key] = float(user_setting)
                elif isinstance(self.__CV_settings[settings_key],bool):
                    self.__CV_settings[settings_key] = bool(user_setting)
                else:
                    self.__CV_settings[settings_key] = user_setting

    def setLinestyleDefaults(self):
        """ This routine sets the default line style behaviour """
        popup = SettingsPopupLinestyle(self)
        del popup

    ##########
    # Tools
    ##########
    def amplitudes_of_highlights(self):
        """ Create a window for the participation factors of the highlighted mode in the diagram """
        selected_lines = self.find_data_of_highlights()
        if selected_lines == []:
            self.statusBar().showMessage('WARNING: There are no lines selected in the diagram, '
                                         'so no amplitude plot will be made', 4000)
        else:
            if len(selected_lines) > 1:
                self.statusBar().showMessage('WARNING: Multiple lines are selected in the diagram, '
                                             'but only one amplitude plot will be made', 4000)
            self.initAmplitudes(popup=False, chosen_mode=selected_lines[0])

    def initAmplitudes(self, popup: bool=True, chosen_mode: list=None) -> None:
        """ Initialize the participation diagram

        This routine initializes the window/plot of the participation factors on the amplitudes for a
        certain mode/dataset. Either a popup is used to select the mode which will be analyzed or the chosen_mode
        argument is used (which can be the result of amplitudes_of_highlights or the result when using the context menu
        for a mode in the tree view)

        Args:
            popup: Flag to indicate if a popup is used to select the mode which will be analyzed
            chosen_mode: List with toolname, dataset name and mode ID which will be analyzed (if popup = False)
        """
        if popup is True:
            self.popupAMP = SettingsPopupAMP()
            success, amp_tool, amp_dataset, amp_modeid = self.popupAMP.get_settings()
            del self.popupAMP
            if success is False:
                return
        else:
            if chosen_mode is None:
                return
            else:
                amp_tool = chosen_mode[0]
                amp_dataset = chosen_mode[1]
                amp_modeid = chosen_mode[2]

        if (database[amp_tool][amp_dataset].ds.frequency.values.ndim != 0 and
            database[amp_tool][amp_dataset].ds.participation_factors_amp.values.ndim != 0):
            self.AmplitudeWindow = AmplitudeWindow()
            self.AmplitudeWindow.sigClosed.connect(self.deleteAmplitudes)
        else:
            QMessageBox.about(self, "WARNING", "Campbell and Amplitude files have to be loaded first!")
            return

        self.updateAmplitudes(amp_tool, amp_dataset, amp_modeid)

    def updateAmplitudes(self, amp_tool: str, amp_dataset: str, amp_modeid: int):
        """ Update Amplitude plot for the chosen tool, dataset, mode_ID combination

        Args:
            amp_tool: Name of the tool
            amp_dataset: Name of the dataset
            amp_modeid: ID of the mode
        """
        if (database[amp_tool][amp_dataset].ds.frequency.values.ndim != 0 and
            database[amp_tool][amp_dataset].ds.participation_factors_amp.values.ndim != 0):

            # get the possibly user-modified axes limits, it would be good to have a signal when the axes limits are changed
            view_cfg.axes_limits = (self.axes1.get_xlim(), self.axes1.get_ylim(), self.axes2.get_ylim())

            self.AmplitudeWindow.configure_plotAMP(amp_tool,
                                                   amp_dataset,
                                                   amp_modeid,
                                                   database[amp_tool][amp_dataset].ds,
                                                   self.xaxis_param,
                                                   threshold=self.__CV_settings['amp_part_threshold'])
            self.AmplitudeWindow.show()
        else:
            QMessageBox.about(self, "WARNING", "Campbell and Amplitude files have to be loaded first!")
            return

    def deleteAmplitudes(self):
        """ Deletes AmplitudeWindow attribute if Amplitude Window is closed """
        del self.AmplitudeWindow

    ##########
    # file
    ##########
    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QMessageBox.about(self, "About",(
            "CampbellViewer is free software distributed under license conditions as "
            "stated in the file <a href=\"https://github.com/DLR-AE/CampbellViewer/blob/main/LICENSE\">LICENSE</a>, "
            "which is part of the repository. <br>CampbellViewer is distributed in the hope that it will be useful, "
            "but WITHOUT ANY WARRANTY; without even the implied warranty of "
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.<br><br>"
            "Wind turbine icon taken from "
            "<a href=\"https://thenounproject.com/icon/wind-turbine-2076/\">Noun Project</a>."
        ))


##########
# Exception handling
##########
def my_excepthook(type, value: str, tback):
    """ Ensures the error tracing in combination with pyQt.

    Args:
        type: type-object containing the exception type
        value: string containing the error message
        trb: traceback-object
    """

    # then call the default handler
    sys.__excepthook__(type, value, tback)


def process_cl_args():
    """
    Process the command line arguments

    PyQT has default arguments, additional arguments for the CampbellViewer can be defined here

    Returns:
          cv_specific_args: argparse Namespace with CampbellViewer specific command line arguments
          qt_default_args: optional list with the default pyqt command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', action='store')  # optional flag

    cv_specific_args, qt_default_args = parser.parse_known_args()

    # check that requested database exists
    if cv_specific_args.database is not None:
        if not os.path.exists(cv_specific_args.database):
            print('Requested database in command line does not exist.')
            cv_specific_args.database = None

    return cv_specific_args, qt_default_args


def main():
    """Main function to execute CampbellViewer.

    """

    sys.excepthook = my_excepthook

    # distinguish between CampbellViewer specific and PyQt command line arguments
    cv_specific_args, qt_default_args = process_cl_args()
    qt_args = sys.argv[:1] + qt_default_args

    # define main app
    app = QApplication(qt_args)
    app.setStyle('Fusion')

    aw = ApplicationWindow()
    aw.setWindowTitle("CampbellViewer")
    icon_path = importlib.resources.files('campbellviewer') / 'assets' / 'windturbine_square.png'
    aw.setWindowIcon(QIcon(str(icon_path)))

    # set initial size
    w = 1400
    h = 1000
    aw.setMinimumSize(w, h)
    aw.show()
    if cv_specific_args.database is not None:
        aw.apply_database(cv_specific_args.database)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
