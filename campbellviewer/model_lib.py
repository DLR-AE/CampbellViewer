"""
This module contains data storing classes
"""
# global libs
import numpy as np
from PyQt5.QtCore import QAbstractItemModel, QAbstractTableModel, QAbstractListModel, Qt, QVariant, QModelIndex
from PyQt5.QtGui import QBrush, QColor

from globals import database, view_cfg
from utilities import assure_unique_name


class DatasetTableModel(QAbstractListModel):
    """
    Model for a list with all loaded datasets. This list model is outdated and has been replaced by the tree model
    """
    def __init__(self, parent=None, *args):
        super(DatasetTableModel, self).__init__()

    def rowCount(self, parent=QModelIndex()):
        return len(database)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return list(database.keys())[index.row()]
        elif role == Qt.CheckStateRole:
            if list(database.keys())[index.row()] in view_cfg.ActiveDataSets:
                return Qt.Checked
            else:
                return Qt.Unchecked
        else:
            return QVariant()

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            old_name = list(database.keys())[index.row()]
            view_cfg.ActiveDataSets = [value if old_name == ads else ads for ads in view_cfg.ActiveDataSets]
            view_cfg.ActiveModesDict[value] = view_cfg.ActiveModesDict.pop(old_name)
            # view_cfg.LineStyleDict[value] = view_cfg.LineStyleDict.pop(old_name)
            database[value] = database.pop(old_name)
            self.dataChanged.emit(index, index)
            return True
        elif role == Qt.CheckStateRole:
            ds_name = list(database.keys())[index.row()]
            if value == Qt.Checked and ds_name not in view_cfg.ActiveDataSets:
                view_cfg.ActiveDataSets.append(ds_name)
                self.dataChanged.emit(index, index)
                return True
            elif value == Qt.Unchecked and ds_name in view_cfg.ActiveDataSets:
                view_cfg.ActiveDataSets.remove(ds_name)
                self.dataChanged.emit(index, index)
                return True
        else:
            return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsUserCheckable


class ModeTableModel(QAbstractTableModel):
    """ Model for a table with all loaded modes. This list model is outdated and has been replaced by the tree model """
    def __init__(self, parent=None, *args):
        super(ModeTableModel, self).__init__()

    def rowCount(self, parent=QModelIndex()):
        # todo: it would be better to not have a loop/computation here. This function is called very often
        max_number_modes = 0
        for ads in view_cfg.ActiveDataSets:
            if len(database[ads]['mode_names']) > max_number_modes:
                max_number_modes = len(database[ads]['mode_names'])
        return max_number_modes

    def columnCount(self, parent=QModelIndex()):
        return len(view_cfg.ActiveDataSets)  # len(database)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            selected_dataset = list(database.keys())[index.column()]
            return str(np.array(database[selected_dataset]['mode_names'][index.row()]))
        elif role == Qt.CheckStateRole:
            # if mode name in ActiveModes
            ds_name = list(database.keys())[index.column()]
            if database[ds_name]['mode_names'][index.row()] in view_cfg.ActiveModesDict[ds_name]:
                return Qt.Checked
            else:
                return Qt.Unchecked
        else:
            return QVariant()

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            ds_name = list(database.keys())[index.column()]
            old_name = database[ds_name]['mode_names'][index.row()]

            new_name = assure_unique_name(value, database[ds_name]['mode_names'])

            # Is this really the best way to modify a value in an xarray?
            # Is it not possible to directly modify the value itself?
            new_mode_names = list(database[ds_name].mode_names.data)
            new_mode_names[index.row()] = new_name
            database[ds_name]['mode_names'] = new_mode_names
            # database[ds_name].mode_names[index.row()].values = database[ds_name]['mode_names'].__setitem__(old_name, xr.DataArray('test'))

            view_cfg.ActiveModesDict[ds_name] = [value if old_name == am else am for am in view_cfg.ActiveModesDict[ds_name]]
            self.dataChanged.emit(index, index)
            return True
        elif role == Qt.CheckStateRole:
            ds_name = list(database.keys())[index.column()]
            if value == Qt.Checked and self.data(index) not in view_cfg.ActiveModesDict[ds_name]:
                view_cfg.ActiveModesDict[ds_name].append(self.data(index))
                self.dataChanged.emit(index, index)
                return True
            elif value == Qt.Unchecked and self.data(index) in view_cfg.ActiveModesDict[ds_name]:
                view_cfg.ActiveModesDict[ds_name].remove(self.data(index))
                self.dataChanged.emit(index, index)
                return True
        else:
            return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsUserCheckable


class TreeItem(object):
    def __init__(self, name=None, checked_state=Qt.Checked, parent=None, branch_activity=True, data=None):
        self.parentItem = parent
        self.itemName = name  # the string which will be used for visualization in the treeview
        self.itemData = data  # additional data for this node (e.g. further description of a mode)
        self.itemActivity = checked_state  # stores the activity of the node (even if the level above has been unchecked)
        self.itemVisibleActivity = Qt.Checked  # the activity which is shown in the view
        if self.itemActivity == Qt.Checked and branch_activity is True:
            self.setVisibleActivity(Qt.Checked)
        else:
            self.setVisibleActivity(Qt.Unchecked)
        self.childItems = []

    def setVisibleActivity(self, visible_activity):
        self.itemVisibleActivity = visible_activity
        if visible_activity == Qt.Checked:
            self.color = QBrush(QColor(0, 0, 0))
        elif visible_activity == Qt.Unchecked:
            self.color = QBrush(QColor(224, 224, 224))

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemName)

    def data(self):
        try:
            return self.itemName
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

class TreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)

        # self.rootItem = TreeItem('Loaded datasets')
        # self.setupModelData(data.split('\n'), self.rootItem)
        self.rootItem = TreeItem('Loaded datasets')
        # self.setupModelData()

    def columnCount(self, parent):
        """ Our data will only have one column """
        return 1

    def data(self, index, role):
        """ Returns the data held in the index for a certain role """
        # I do not know why this check would be necessary. Can the view request data for an index which is not valid?
        if not index.isValid():
            return None

        item = index.internalPointer()

        # displayrole -> return the name belonging to the node of this index
        if role == Qt.DisplayRole:
            return item.data()
        # checkstaterole -> return the active/passive value of the node of this index
        elif role == Qt.CheckStateRole:
            return item.itemVisibleActivity
        # foregroundrole -> return color for the text (to indicate if active or not)
        elif role == Qt.ForegroundRole:
            return item.color
        # tooltiprole -> small pop-up with additional info when hovering over item
        elif role == Qt.ToolTipRole:
            if item.itemData is None:
                return None
            else:
                return item.itemData.summary()
        else:
            return None

    def setData(self, index, value, role=Qt.EditRole):
        """ sets data in the tree model based on user modification in the tree view and updates database accordingly """
        item = self.getItem(index)
        if role == Qt.EditRole:
            item.itemName = value
            if item.itemData is not None:
                item.itemData.name = value
        elif role == Qt.CheckStateRole:
            item.itemActivity = value
            self.updateActivityRepresentation(item)
        else:
            return False

        self.updateDatabase()  # The database has to be updated according to the modifications made to the tree model
        self.updateViewCfg()
        self.layoutChanged.emit()  # Update the canvas
        return True

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def headerData(self, section, orientation, role):
        """
        Returns header information. In our case we only have 1 column and only want the top header, so section is not
        used

        Args:
            section : int
                For horizontal headers, the section number corresponds to the column number.
                Similarly, for vertical headers, the section number corresponds to the row number.
            orientation : int
            role : int
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data()
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEditable

    def index(self, row, column, parent):
        """ Returns the index of a certain item, which is characterized by the 'coordinates' row, column and parent """
        # I don't know what this means. Does this mean that row, column, parent is not currently available in the model?
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        # Find the parent, this can be an actual node or the root node
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        # find the child and create the index
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        """ Returns the index of the parent node """
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        """
        Returns number of childs for a given parent
        -> e.g. number of datasets for a tool or number of modes for a dataset
        """
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def updateActivityRepresentation(self, item):
        """
        This method updates the visible activity of tree items taking into account the hierarchical structure of the
        tree -> all children and grandchildren of a node have to be inactive if a parent is inactive.
        """
        # An item can never be visibly active if its parent is not.
        if item.parent() is not None:  # the rootnode has no parent and always keeps the visibly active
            item.setVisibleActivity(item.parent().itemVisibleActivity and item.itemActivity)

        for child in item.childItems:
            child.setVisibleActivity((item.itemActivity and child.itemActivity))

            for grandchild in child.childItems:
                grandchild.setVisibleActivity((item.itemActivity and child.itemActivity and grandchild.itemActivity))

    def addModelData(self, old_database=dict()):
        """
        This function uses the database and view_cfg.active_data to update the treemodel data. All data in old_database
        has already been loaded in the treemodel. These items will not be changed in order to retain the settings
        (item activity, item expanded or not).

        It is difficult to update datasets which are already available in the old_database. Because there are two
        options: 1) Nothing should be changed, 2) the dataset has to be updated (e.g. which would be the case if a new
        dataset with an already existing name was loaded.
        I decided to only allow unique dataset names, so overwriting databases entries is not possible.
        """

        for tool in database:
            if tool in old_database:
                current_tool_node = self.rootItem.childItems[list(old_database.keys()).index(tool)]
            else:
                if tool in view_cfg.active_data:
                    self.rootItem.appendChild(TreeItem(tool, Qt.Checked, self.rootItem))
                else:
                    self.rootItem.appendChild(TreeItem(tool, Qt.Unchecked, self.rootItem))
                current_tool_node = self.rootItem.childItems[-1]
                old_database[tool] = {}

            for ds in database[tool]:
                if ds not in old_database[tool]:
                    if ds in view_cfg.active_data[tool]:
                        current_tool_node.appendChild(TreeItem(ds, Qt.Checked, current_tool_node))
                    else:
                        current_tool_node.appendChild(TreeItem(ds, Qt.Unchecked, current_tool_node))

                    for mode_ID, ae_mode in enumerate(database[tool][ds].modes.values):
                        if mode_ID in view_cfg.active_data[tool][ds]:
                            current_tool_node.childItems[-1].appendChild(TreeItem(ae_mode.name, Qt.Checked, current_tool_node.childItems[-1], data=ae_mode))
                        else:
                            current_tool_node.childItems[-1].appendChild(TreeItem(ae_mode.name, Qt.Unchecked, current_tool_node.childItems[-1], data=ae_mode))

        self.updateActivityRepresentation(self.rootItem)

    def updateDatabase(self):
        """
        Use data of the tree model to update the database.

        For now I assume that the modifications are ONLY modifications of existing entries in the model by editing
        the text in the tree item or checking/unchecking the tick box. Other useful things such as deleting/adding/copy
        are not implemented
        """

        # Because a direct link between the database and the tree model is not possible (it is not possible to link a
        # a node of the tree directly to a database entry), we have to loop over the full tree and update the full
        # database... -> this can not be optimal...
        for tool_node in self.rootItem.childItems:
            for ds_node in tool_node.childItems:
                for mode_ID, mode in enumerate(ds_node.childItems):
                    database[tool_node.itemName][ds_node.itemName]["modes"][mode_ID] = mode.itemData

    def updateViewCfg(self):
        """
        Use data of the tree model to update the view_cfg.

        For now I assume that the modifications are ONLY modifications of existing entries in the model by editing
        the text in the tree item or checking/unchecking the tick box. Other useful things such as deleting/adding/copy
        are not implemented
        """
        # active_data is completely replaced!
        view_cfg.active_data = {}
        for tool_node in self.rootItem.childItems:
            if tool_node.itemVisibleActivity == Qt.Checked:
                view_cfg.active_data[tool_node.itemName] = {}

                for ds_node in tool_node.childItems:
                    if ds_node.itemVisibleActivity == Qt.Checked:
                        view_cfg.active_data[tool_node.itemName][ds_node.itemName] = []

                    for mode_ID, mode in enumerate(ds_node.childItems):
                        if mode.itemVisibleActivity == Qt.Checked:
                            view_cfg.active_data[tool_node.itemName][ds_node.itemName].append(mode_ID)

    def update_highlight(self, selected, deselected):
        """
        Translate the data that is selected in the treeview to a list such that it can be used when
        plotting the data
        """
        if len(selected.indexes()) > 0:
            selected_index = selected.indexes()[0]
            selected_node = self.getItem(selected_index)
            # work way up the tree model
            view_cfg.selected_branch = self.get_branch_from_item(selected_node)

        else:
            view_cfg.selected_branch = []
        self.layoutChanged.emit()

    def get_branch_from_item(self, item):
        """
        Returns a list with the names of the parent items. This is used to link the item to the database dictionary.
        """
        current_node = item
        branch = []
        while current_node.parentItem is not None:
            branch.append(current_node.itemName)
            current_node = current_node.parentItem

        if len(branch) == 3:  # a mode has been selected -> replace mode name by Mode_ID
            branch[0] = item.row()
        return branch

    def removeRows(self, position, rows, parent=QModelIndex()):
        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + rows - 1)
        success = parentItem.removeChildren(position, rows)
        self.updateDatabase()
        self.updateViewCfg()
        self.endRemoveRows()

        return success

    def delete_data(self, selected):
        """
        Delete data from the tree model and the database

        Is it possible to only update the tree model and not modify the database? Do we want that? Probably having the
        tow options: 'Delete from database' and 'Delete from view' would be nice.
        """
        if len(selected) > 0:
            selected_index = selected[0]

            branch = self.get_branch_from_item(self.getItem(selected_index))
            self.removeRow(selected_index.row(), selected_index.parent())  # removeRow is a convenience function which uses removeRows
            self.updateViewCfg()

            database.remove_data(branch)

        self.layoutChanged.emit()

