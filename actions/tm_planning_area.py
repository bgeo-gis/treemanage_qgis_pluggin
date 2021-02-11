"""
This file is part of TreeManage 1.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
import json

from qgis.PyQt.QtCore import QStringListModel, Qt, QDate
from qgis.PyQt.QtSql import QSqlTableModel
from qgis.PyQt.QtWidgets import QCompleter, QTableView, QGridLayout, QGroupBox, QLabel, QCheckBox


from functools import partial

from .. import utils_giswater
from .tm_multiple_selection import TmMultipleSelection
from .tm_parent import TmParentAction
from ..ui_manager import PlaningArea, PlaningAreaSelection


class TmPlanningArea(TmParentAction):

    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class constructor """

        TmParentAction.__init__(self, iface, settings, controller, plugin_dir)
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
        layer = self.controller.get_layer_by_tablename('v_edit_node_zone')
        if not layer:
            self.last_error = self.controller.tr("Layer not found") + ": v_edit_node_zone"
            return None
        self.layers['node'] = [layer]

        self.visible_layers = self.get_visible_layers()
        self.remove_selection()

        self.dlg_area = PlaningArea()
        self.load_settings(self.dlg_area)

        self.set_icon(self.dlg_area.btn_selection, "100")

        utils_giswater.set_qtv_config(self.dlg_area.tbl_area, edit_triggers=QTableView.NoEditTriggers)

        self.load_default_values()
        table_name = "v_ui_planning_unit_zone"
        self.update_table(self.dlg_area, self.dlg_area.tbl_area, table_name)

        # Signals
        self.dlg_area.cmb_element.currentIndexChanged.connect(
            partial(self.update_table, self.dlg_area, self.dlg_area.tbl_area, table_name))
        self.dlg_area.cmb_work.currentIndexChanged.connect(
            partial(self.update_table, self.dlg_area, self.dlg_area.tbl_area, table_name))
        self.dlg_area.cmb_priority.currentIndexChanged.connect(
            partial(self.update_table, self.dlg_area, self.dlg_area.tbl_area, table_name))
        self.dlg_area.start_date.dateChanged.connect(partial(self.update_table, self.dlg_area, self.dlg_area.tbl_area, table_name))
        self.dlg_area.end_date.dateChanged.connect(partial(self.update_table, self.dlg_area, self.dlg_area.tbl_area, table_name))
        self.dlg_area.cmb_element.currentIndexChanged.connect(
            partial(self.update_cmb_work))

        self.dlg_area.btn_close.clicked.connect(partial(self.save_default_values))
        self.dlg_area.btn_close.clicked.connect(partial(self.close_dialog, self.dlg_area))
        self.dlg_area.btn_close.clicked.connect(partial(self.remove_selection))
        self.dlg_area.rejected.connect(partial(self.save_default_values))
        self.dlg_area.rejected.connect(partial(self.close_dialog, self.dlg_area))
        self.dlg_area.rejected.connect(partial(self.remove_selection))
        self.dlg_area.btn_selection.clicked.connect(partial(self.open_selection_form))

        # set timeStart and timeEnd as the min/max dave values get from model
        current_date = QDate.currentDate()
        sql = ('SELECT MIN(plan_date), MAX(plan_date)'
               ' FROM v_ui_planning_unit_zone')
        row = self.controller.get_row(sql)
        if row:
            if row[0]:
                self.dlg_area.start_date.setDate(row[0])
            if row[1]:
                self.dlg_area.end_date.setDate(row[1])
            else:
                self.dlg_area.end_date.setDate(current_date)

        # Populate combos
        sql = "SELECT id, idval FROM om_visit_class"
        rows = self.controller.get_rows(sql, add_empty_row=True)
        utils_giswater.set_item_data(self.dlg_area.cmb_element, rows, 1)

        sql = "SELECT distinct(om_visit_parameter.descript), om_visit_parameter.descript param FROM verd_urba.om_visit_class " \
              "JOIN verd_urba.om_visit_class_x_parameter ON om_visit_class_x_parameter.class_id = om_visit_class.id " \
              "JOIN verd_urba.om_visit_parameter ON om_visit_class_x_parameter.parameter_id=om_visit_parameter.id"
        rows = self.controller.get_rows(sql, add_empty_row=True)
        utils_giswater.set_item_data(self.dlg_area.cmb_work, rows, 1)
        self.update_cmb_work()

        sql = "SELECT id, name FROM cat_priority"
        rows = self.controller.get_rows(sql, add_empty_row=True)
        utils_giswater.set_item_data(self.dlg_area.cmb_priority, rows, 1)

        self.open_dialog(self.dlg_area)


    def update_cmb_work(self):

        element_id = utils_giswater.get_item_data(self.dlg_area, self.dlg_area.cmb_element, 0)
        if element_id:
            sql = f"SELECT distinct(om_visit_parameter.descript), om_visit_parameter.descript param " \
                  f"FROM verd_urba.om_visit_class " \
                  f"JOIN verd_urba.om_visit_class_x_parameter ON om_visit_class_x_parameter.class_id = om_visit_class.id " \
                  f"JOIN verd_urba.om_visit_parameter ON om_visit_class_x_parameter.parameter_id=om_visit_parameter.id " \
                  f" WHERE om_visit_class.id = '{element_id}'"

            rows = self.controller.get_rows(sql, add_empty_row=True)
            utils_giswater.set_item_data(self.dlg_area.cmb_work, rows, 1)


    def open_selection_form(self):

        self.dlg_area_selection = PlaningAreaSelection()
        self.load_settings(self.dlg_area_selection)
        self.dlg_area_selection.rejected.connect(partial(self.close_dialog, self.dlg_area_selection))

        # Set snapping button icon
        self.set_icon(self.dlg_area_selection.btn_snapping, "137")

        # Populate widgets
        sql = "SELECT id, name FROM cat_priority"
        rows = self.controller.get_rows(sql, add_empty_row=True)
        utils_giswater.set_item_data(self.dlg_area_selection.cmb_priority, rows, 1)

        utils_giswater.setCalendarDate(self.dlg_area_selection, self.dlg_area_selection.executed_date, None, True)

        body = self.create_body()
        result = self.controller.get_json('tm_fct_getplanform', body)

        main_layout = self.dlg_area_selection.findChild(QGridLayout, 'grl_main')

        for row in result['body']['data']['info']:
            keys = row.keys()
            for key in keys:
                group_box = QGroupBox(key)
                group_box.setObjectName(key)
                grid_layout = QGridLayout()
                i = 0
                for value in row[key]:
                    lbl = QLabel()
                    lbl.setObjectName(f"lbl_{value}")
                    lbl.setText(f"{value}")
                    lbl.setMinimumSize(160, 0)
                    grid_layout.addWidget(lbl, i, 0)

                    chk = QCheckBox()
                    chk.setObjectName(f"{value}")
                    chk.setLayoutDirection(Qt.RightToLeft)
                    grid_layout.addWidget(chk, i, 1)
                    i = i+1

                group_box.setLayout(grid_layout)
                main_layout.addWidget(group_box)


        # Set listeners
        self.dlg_area_selection.btn_accept.clicked.connect(partial(self.manage_area_accepted))
        self.dlg_area_selection.btn_close.clicked.connect(partial(self.save_default_values))
        self.dlg_area_selection.btn_close.clicked.connect(partial(self.close_dialog, self.dlg_area_selection))
        self.dlg_area_selection.btn_close.clicked.connect(partial(self.remove_selection))
        self.dlg_area_selection.rejected.connect(partial(self.save_default_values))
        self.dlg_area_selection.rejected.connect(partial(self.close_dialog, self.dlg_area_selection))
        self.dlg_area_selection.rejected.connect(partial(self.remove_selection))

        self.dlg_area_selection.btn_snapping.clicked.connect(partial(self.selection_init))

        self.open_dialog(self.dlg_area_selection)


    def manage_area_accepted(self):

        json_values = {}
        grbox_list = self.dlg_area_selection.findChildren(QGroupBox)
        for grbox in grbox_list:
            chk_values = []
            chk_list = grbox.findChildren(QCheckBox)
            for chk in chk_list:
                if chk.isChecked():
                    chk_values.append(f"{chk.objectName()}")
            if chk_values != []:
                json_values[f"{grbox.objectName()}"] = chk_values

        extras = f'"ids":{json.dumps(self.ids)}, "values":{json.dumps(json_values)}, ' \
                 f'"plan_execute_date":"{utils_giswater.getCalendarDate(self.dlg_area_selection, self.dlg_area_selection.executed_date)}"'

        priority = utils_giswater.get_item_data(self.dlg_area_selection, self.dlg_area_selection.cmb_priority, 0)
        if priority != "":
            extras += f', "priority":{priority}'
        else:
            extras += f', "priority":null'

        body = self.create_body(extras=extras)
        self.controller.get_json('tm_fct_setplan_zone', body, log_sql=True)

        # Close dialog
        self.close_dialog(self.dlg_area_selection)



    def selection_init(self):
        """ Set canvas map tool to an instance of class 'MultipleSelection' """

        multiple_selection = TmMultipleSelection(self.iface, self.controller, self.layers['node'], parent_manage=self)
        self.disconnect_signal_selection_changed()
        self.canvas.setMapTool(multiple_selection)
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
            if layer.selectedFeatureCount() > 0 and self.controller.is_layer_visible(layer):
                # Get selected features of the layer
                features = layer.selectedFeatures()
                for feature in features:
                    # Append 'feature_id' into the list
                    selected_id = feature.attribute(field_id)
                    if selected_id not in self.ids:
                        self.ids.append(selected_id)
        self.iface.actionPan().trigger()



    def update_table(self, dialog, qtable, table_name):

        element_id = utils_giswater.get_item_data(dialog, dialog.cmb_element, 1)
        work_id = utils_giswater.get_item_data(dialog, dialog.cmb_work, 1, add_quote=True)
        priority = utils_giswater.get_item_data(dialog, dialog.cmb_priority, 1)

        # Create interval dates
        format_date = 'yyyy/MM/dd'
        start_date = dialog.start_date.date()
        end_date = dialog.end_date.date()
        interval = f"'{start_date.toString(format_date)}'::timestamp AND '{end_date.toString(format_date)}'::timestamp"


        # expr_filter = f" plan_date::timestamp BETWEEN {interval}"
        expr_filter = f" 1=1 "
        if str(element_id) not in "-1": expr_filter += f" AND work like '%{element_id}%'"
        if str(work_id) not in "-1": expr_filter += f" AND work like '%{work_id}%'"
        if str(priority) not in "-1": expr_filter += f" AND priority = '{priority}'"

        self.fill_table_area(qtable, table_name, expr_filter=expr_filter)

        # self.get_id_list()


    def fill_table_area(self, qtable, table_name,  expr_filter=None):
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
            print(f"aa -> {is_valid}")
            print(f"bb -> {expr}")
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
        column_index = utils_giswater.get_col_index_by_col_name(self.dlg_area.tbl_area, 'node_id')
        for x in range(0, self.dlg_area.tbl_area.model().rowCount()):
            _id = self.dlg_area.tbl_area.model().data(self.dlg_area.tbl_area.model().index(x, column_index))
            self.ids.append(_id)


    def remove_selection(self):
        """ Remove all previous selections """

        for layer in self.layers['node']:
            if layer in self.visible_layers:
                self.controller.set_layer_visible(layer, False)
        for layer in self.layers['node']:
            if layer in self.visible_layers:
                layer.removeSelection()
                self.controller.set_layer_visible(layer, True)

        self.canvas.refresh()


    def get_visible_layers(self, return_as_list=True):
        """ Return list or string as {...} with all visible layer in TOC """

        visible_layer = []
        layers = self.controller.get_layers()
        if return_as_list:
            for layer in layers:
                if self.controller.is_layer_visible(layer):
                    visible_layer.append(layer)
            return visible_layer

        for layer in layers:
            if self.controller.is_layer_visible(layer):
                visible_layer += f'"{layer.name()}", '
        visible_layer = visible_layer[:-2] + "}"

        return visible_layer


    def save_default_values(self):
        return


    def load_default_values(self):
        """ Load QGIS settings related with csv options """
        return

