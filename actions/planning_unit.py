"""
This file is part of TreeManage 1.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: latin-1 -*-
from PyQt4.QtGui import QIcon

try:
    from qgis.core import Qgis
except:
    from qgis.core import QGis as Qgis

if Qgis.QGIS_VERSION_INT >= 20000 and Qgis.QGIS_VERSION_INT < 29900:
    from PyQt4 import QtCore
    from PyQt4.QtCore import Qt, QDate, QPoint
    from PyQt4.QtGui import QIntValidator, QDoubleValidator, QMenu
    from PyQt4.QtGui import QWidget, QAction, QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QDateEdit
    from PyQt4.QtGui import QGridLayout, QSpacerItem, QSizePolicy, QStringListModel, QCompleter, QAbstractItemView
    from PyQt4.QtGui import QTableView, QListWidgetItem, QStandardItemModel, QStandardItem, QTabWidget, QListWidget
    from PyQt4.QtSql import QSqlTableModel
    import urlparse
    import win32gui

else:
    from qgis.PyQt import QtCore
    from qgis.PyQt.QtCore import Qt, QDate, QStringListModel,QPoint
    from qgis.PyQt.QtGui import QIntValidator, QDoubleValidator, QStandardItem, QStandardItemModel
    from qgis.PyQt.QtWidgets import QWidget, QAction, QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, \
        QGridLayout, QSpacerItem, QSizePolicy, QCompleter, QTableView, QListWidget, QListWidgetItem, \
        QTabWidget, QAbstractItemView, QMenu
    from qgis.PyQt.QtSql import QSqlTableModel
    import urllib.parse as urlparse
from qgis.core import QgsExpression, QgsFeatureRequest




from functools import partial

from _utils import widget_manager as wm
from tree_manage.actions.multiple_selection import MultipleSelection
from tree_manage.actions.parent import ParentAction
from tree_manage.actions.parent_manage import ParentManage
from tree_manage.ui_manager import PlaningUnit


class PlanningUnit(ParentAction):
    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class constructor """
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)
        #ParentManage.__init__(self, iface, settings, controller, plugin_dir)

        self.iface = iface
        self.settings = settings
        self.controller = controller
        self.plugin_dir = plugin_dir
        self.canvas = self.iface.mapCanvas()

    def reset_lists(self):
        """ Reset list of selected records """
        self.ids = []
        self.list_ids = {}
        self.list_ids['node'] = []


    def reset_layers(self):
        """ Reset list of layers """
        self.layers = {}
        self.layers['node'] = []


    def open_form(self):
        self.previous_map_tool = self.canvas.mapTool()
        # Get layers of every geom_type
        self.reset_lists()
        self.reset_layers()
        self.geom_type = 'node'
        self.layers['node'] = [self.controller.get_layer_by_tablename('v_edit_node')]

        #self.layers['node'] = self.controller.get_group_layers('node')
        self.visible_layers = self.get_visible_layers()
        self.remove_selection()


        self.dlg_unit = PlaningUnit()
        self.load_settings(self.dlg_unit)
        self.set_icon(self.dlg_unit.btn_insert, "111")
        self.set_icon(self.dlg_unit.btn_delete, "112")
        self.set_icon(self.dlg_unit.btn_snapping, "137")

        validator = QIntValidator(1, 9999999)
        self.dlg_unit.txt_times.setValidator(validator)

        wm.set_qtv_config(self.dlg_unit.tbl_unit, edit_triggers=QTableView.DoubleClicked)

        sql = ("SELECT id, name FROM " + self.schema_name + ".cat_campaign")
        rows = self.controller.get_rows(sql, log_sql=True)
        wm.set_item_data(self.dlg_unit.cmb_campaign, rows, 1)
        sql = ("SELECT id, name FROM " + self.schema_name + ".cat_work")
        rows = [('', '')]
        rows.extend(self.controller.get_rows(sql))
        wm.set_item_data(self.dlg_unit.cmb_work, rows, 1)
        self.load_default_values()
        table_name = "v_ui_planning_unit"
        self.update_table(self.dlg_unit, self.dlg_unit.tbl_unit, table_name, self.dlg_unit.cmb_campaign, self.dlg_unit.cmb_work)

        # Signals
        self.dlg_unit.cmb_campaign.currentIndexChanged.connect(
            partial(self.update_table, self.dlg_unit, self.dlg_unit.tbl_unit, table_name, self.dlg_unit.cmb_campaign, self.dlg_unit.cmb_work))

        self.dlg_unit.cmb_work.currentIndexChanged.connect(
            partial(self.update_table, self.dlg_unit, self.dlg_unit.tbl_unit, table_name, self.dlg_unit.cmb_campaign, self.dlg_unit.cmb_work))

        completer = QCompleter()
        self.dlg_unit.txt_id.textChanged.connect(
            partial(self.populate_comboline, self.dlg_unit,self.dlg_unit.txt_id, completer))

        self.dlg_unit.btn_close.clicked.connect(partial(self.save_default_values))
        self.dlg_unit.btn_close.clicked.connect(partial(self.close_dialog, self.dlg_unit))
        self.dlg_unit.btn_close.clicked.connect(partial(self.remove_selection))

        self.dlg_unit.rejected.connect(partial(self.save_default_values))
        self.dlg_unit.rejected.connect(partial(self.close_dialog, self.dlg_unit))
        self.dlg_unit.rejected.connect(partial(self.remove_selection))


        self.dlg_unit.btn_snapping.clicked.connect(partial(self.selection_init,  self.dlg_unit.tbl_unit))
        #self.dlg_unit.btn_insert.clicked.connect(partial(self.selection_init, self.dlg_unit.tbl_unit))
        self.dlg_unit.btn_delete.clicked.connect(partial(self.delete_row, self.dlg_unit.tbl_unit))

        self.open_dialog(self.dlg_unit)


    def populate_comboline(self, dialog, widget, completer):
        filter = wm.getWidgetText(dialog, widget)
        sql = ("SELECT node_id FROM " + self.schema_name + ".v_edit_node "
               " WHERE node_id ILIKE '%" + str(filter)+"%'")
        rows = self.controller.get_rows(sql, log_sql=True)
        list_items = [row[0] for row in rows]
        model = QStringListModel()

        self.set_completer_object(completer, model, widget, list_items)



    def set_completer_object(self, completer, model, widget, list_items, max_visible=10):
        """ Set autocomplete of widget @table_object + "_id"
            getting id's from selected @table_object.
            WARNING: Each QlineEdit needs their own QCompleter and their own QStringListModel!!!
        """

        # Set completer and model: add autocomplete in the widget
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(int(max_visible))
        widget.setCompleter(completer)
        completer.setCompletionMode(1)
        model.setStringList(list_items)
        completer.setModel(model)


    def delete_row(self, qtable):
        # Get selected rows
        selected_list = qtable.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_info_box(message)
            return
        layer = self.controller.get_layer_by_tablename('v_edit_node')
        for index in selected_list:
            row = index.row()
            column_index = wm.get_col_index_by_col_name(qtable, 'node_id')
            feature_id = index.sibling(row, column_index).data()
            self.controller.log_info(str(feature_id))
            if feature_id in self.ids:
                self.ids.remove(feature_id)
                feature = self.get_feature_by_id(layer, feature_id, 'node_id')
                layer.deselect(feature.id())
            qtable.model().removeRow(index.row())



    def selection_init(self,  qtable):
        """ Set canvas map tool to an instance of class 'MultipleSelection' """
        multiple_selection = MultipleSelection(self.iface, self.controller, self.layers['node'], parent_manage=self, table_object=qtable)
        
        self.canvas.setMapTool(multiple_selection)
        self.disconnect_signal_selection_changed()
        self.connect_signal_selection_changed(qtable)
        cursor = self.get_cursor_multiple_selection()
        self.canvas.setCursor(cursor)


    def disconnect_signal_selection_changed(self):
        """ Disconnect signal selectionChanged """

        try:
            self.canvas.selectionChanged.disconnect()
        except Exception:
            pass


    def connect_signal_selection_changed(self, qtable):
        """ Connect signal selectionChanged """
        try:
            self.canvas.selectionChanged.connect(partial(self.selection_changed, qtable, self.geom_type))
        except Exception:

            pass


    def selection_changed(self, qtable, geom_type):
        """ Slot function for signal 'canvas.selectionChanged' """

        self.disconnect_signal_selection_changed()

        field_id = geom_type + "_id"

        # Iterate over all layers of the group
        for layer in self.layers[self.geom_type]:
            if layer.selectedFeatureCount() > 0 and self.iface.legendInterface().isLayerVisible(layer):
                # Get selected features of the layer
                features = layer.selectedFeatures()
                for feature in features:
                    # Append 'feature_id' into the list
                    selected_id = feature.attribute(field_id)
                    if selected_id not in self.ids:
                        self.ids.append(selected_id)
                        self.insert_row(qtable, selected_id)

        self.remove_selection()
        self.connect_signal_selection_changed(qtable)


    def select_features_by_ids(self, geom_type, expr):
        """ Select features of layers of group @geom_type applying @expr """

        # Build a list of feature id's and select them
        for layer in self.layers[geom_type]:
            if expr is None:
                layer.removeSelection()
            else:
                it = layer.getFeatures(QgsFeatureRequest(expr))
                id_list = [i.id() for i in it]
                if len(id_list) > 0:
                    layer.selectByIds(id_list)
                else:
                    layer.removeSelection()


    def insert_row(self, qtable, selected_id):
        """ Reload @widget with contents of @tablename applying selected @expr_filter """
        model = qtable.model()
        record = model.record()
        campaign_id = wm.get_item_data(self.dlg_unit, self.dlg_unit.cmb_campaign, 0)
        work_id = wm.get_item_data(self.dlg_unit, self.dlg_unit.cmb_work, 0)
        times = wm.getWidgetText(self.dlg_unit, self.dlg_unit.txt_times, return_string_null=False)
        if times is None or times < 1 or times == "":
            times = "1"

        record.setValue("node_id", selected_id)
        record.setValue("campaign_id", campaign_id)
        record.setValue("work_id", work_id)
        record.setValue("frequency", str(times))
        model.insertRecord(-1, record)


    def update_table(self, dialog, qtable, table_name, combo1, combo2):

        campaign_id = wm.get_item_data(dialog, combo1, 0)
        work_id = wm.get_item_data(dialog, combo2, 0)

        expr_filter = "campaign_id =" + str(campaign_id)
        if work_id is None or work_id == "":
            self.dlg_unit.btn_insert.setEnabled(False)
            self.dlg_unit.btn_snapping.setEnabled(False)
        else:
            self.dlg_unit.btn_insert.setEnabled(True)
            self.dlg_unit.btn_snapping.setEnabled(True)
            expr_filter += " AND work_id =" + str(work_id)

        self.fill_table_unit(qtable, table_name, expr_filter=expr_filter)
        self.get_id_list()


    # def select_features(self):
    #     layer = self.controller.get_layer_by_tablename("v_edit_node")
    #     self.controller.log_info(str(self.ids))
    #     for feature_id in self.ids:
    #         self.controller.log_info(str(feature_id))
    #         feature = self.get_feature_by_id(layer, feature_id, 'node_id')
    #         self.controller.log_info(str(feature.id()))
    #         self.controller.log_info(str(type(feature)))
    #         layer.select(feature.id())

    def fill_table_unit(self, qtable, table_name,  expr_filter=None):
        """ Fill table @widget filtering query by @workcat_id
         Set a model with selected filter.
         Attach that model to selected table
         @setEditStrategy:
             0: OnFieldChange
             1: OnRowChange
             2: OnManualSubmit
         """
        expr = None
        if expr_filter:
            # Check expression
            (is_valid, expr) = self.check_expression(expr_filter)  # @UnusedVariable
            if not is_valid:
                return expr

        # Set a model with selected filter expression
        if self.schema_name not in table_name:
            table_name = self.schema_name + "." + table_name

        # Set model
        model = QSqlTableModel()
        model.setTable(table_name)
        model.setEditStrategy(QSqlTableModel.OnFieldChange)
        model.setSort(0, 0)
        model.select()

        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())
        # Attach model to table view
        if expr:
            qtable.setModel(model)
            qtable.model().setFilter(expr_filter)
        else:
            qtable.setModel(model)

        return expr

    def get_id_list(self):
        self.ids = []
        column_index = wm.get_col_index_by_col_name(self.dlg_unit.tbl_unit, 'node_id')
        for x in range(0, self.dlg_unit.tbl_unit.model().rowCount()):
            _id = self.dlg_unit.tbl_unit.model().data(self.dlg_unit.tbl_unit.model().index(x, column_index))
            self.ids.append(_id)


    def remove_selection(self):
        """ Remove all previous selections """
        self.controller.log_info(str("TEST"))
        for layer in self.layers['node']:
            if layer in self.visible_layers:
                self.iface.legendInterface().setLayerVisible(layer, False)
                self.controller.log_info(str(layer.name()))
        for layer in self.layers['node']:
            if layer in self.visible_layers:
                self.controller.log_info(str(layer.name()))
                layer.removeSelection()
                self.iface.legendInterface().setLayerVisible(layer, True)

        self.canvas.clear()
        self.canvas.refresh()
        self.canvas.setMapTool(self.previous_map_tool)



    def get_visible_layers(self, return_as_list=True):
        """ Return list or string as {...} with all visible layer in TOC """

        visible_layer = []
        if return_as_list:
            for layer in self.iface.legendInterface().layers():
                if self.iface.legendInterface().isLayerVisible(layer):
                    visible_layer.append(layer)
            # visible_layer = [lyr for lyr in QgsMapLayerRegistry.instance().mapLayers().values()]
            return visible_layer

        for layer in self.iface.legendInterface().layers():
            if self.iface.legendInterface().isLayerVisible(layer):
                visible_layer += '"' + str(layer.name()) + '", '
        visible_layer = visible_layer[:-2] + "}"
        return visible_layer

    def save_default_values(self):
        cur_user = self.controller.get_current_user()
        campaign = wm.get_item_data(self.dlg_unit, self.dlg_unit.cmb_campaign, 0)
        work = wm.get_item_data(self.dlg_unit, self.dlg_unit.cmb_work, 0)
        self.controller.plugin_settings_set_value("PlanningUnit_cmb_campaign_" + cur_user, campaign)
        self.controller.plugin_settings_set_value("PlanningUnit_cmb_work_" + cur_user, work)


    def load_default_values(self):
        """ Load QGIS settings related with csv options """
        cur_user = self.controller.get_current_user()
        campaign = self.controller.plugin_settings_value('PlanningUnit_cmb_campaign_' + cur_user)
        work = self.controller.plugin_settings_value('PlanningUnit_cmb_work_' + cur_user)
        wm.set_combo_itemData(self.dlg_unit.cmb_campaign, str(campaign), 0)
        wm.set_combo_itemData(self.dlg_unit.cmb_work, str(work), 0)
