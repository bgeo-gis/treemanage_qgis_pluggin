"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
from qgis.core import QgsFeatureRequest
from qgis.gui import QgsMapToolEmitPoint
from PyQt4.Qt import QDate
from PyQt4.QtGui import QCompleter, QStringListModel, QAbstractItemView, QTableView, QDateEdit, QLineEdit, QTextEdit, QDateTimeEdit, QComboBox
from PyQt4.QtSql import QSqlTableModel
from PyQt4.QtCore import Qt

from functools import partial


from parent import ParentAction
from ..actions.multiple_selection import MultipleSelection


class ParentManage(ParentAction, object):

    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to keep common functions of classes
            'ManageDocument', 'ManageElement' and 'ManageVisit' of toolbar 'edit'."""
        super(ParentManage, self).__init__(iface, settings, controller, plugin_dir)

        self.x = ""
        self.y = ""
        self.canvas = self.iface.mapCanvas()
        self.plan_om = None
        self.previous_map_tool = None
        self.autocommit = True
        self.lazy_widget = None
        self.workcat_id_end = None


    def reset_lists(self):
        """ Reset list of selected records """
        self.ids = []
        self.list_ids = {}
        self.list_ids['node'] = []


    def reset_layers(self):
        """ Reset list of layers """
        self.layers = {}
        self.layers['node'] = []


    def remove_selection(self, remove_groups=True):
        """ Remove all previous selections """
        layer = self.controller.get_layer_by_tablename("v_edit_node")
        if layer:
            layer.removeSelection()
        try:
            if remove_groups:
                for layer in self.layers['node']:
                    layer.removeSelection()
        except:
            pass
        self.canvas.refresh()


    # def tab_feature_changed(self, table_object):
    #     """ Set geom_type and layer depending selected tab
    #         @table_object = ['doc' | 'element' | 'cat_work']
    #     """
    #     self.get_values_from_form()
    #     if self.dlg.tab_feature.currentIndex() == 3:
    #         self.dlg.btn_snapping.setEnabled(False)
    #     else:
    #         self.dlg.btn_snapping.setEnabled(True)
    #
    #     tab_position = self.dlg.tab_feature.currentIndex()
    #     if tab_position == 0:
    #         self.geom_type = "arc"
    #     elif tab_position == 1:
    #         self.geom_type = "node"
    #     elif tab_position == 2:
    #         self.geom_type = "connec"
    #     elif tab_position == 3:
    #         self.geom_type = "element"
    #     elif tab_position == 4:
    #         self.geom_type = "gully"
    #
    #     self.hide_generic_layers()
    #     widget_name = "tbl_" + table_object + "_x_" + str(self.geom_type)
    #     viewname = "v_edit_" + str(self.geom_type)
    #     self.widget = utils_giswater.getWidget(widget_name)
    #
    #     # Adding auto-completion to a QLineEdit
    #     self.set_completer_feature_id(self.geom_type, viewname)
    #
    #     self.iface.actionPan().trigger()


    def set_completer_feature_id(self, widget, geom_type, viewname):
        """ Set autocomplete of widget 'feature_id'
            getting id's from selected @viewname
        """

        # Adding auto-completion to a QLineEdit
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        widget.setCompleter(self.completer)
        model = QStringListModel()

        sql = ("SELECT " + geom_type + "_id"
               " FROM " + self.schema_name + "." + viewname)
        row = self.controller.get_rows(sql, commit=self.autocommit)
        if row:
            for i in range(0, len(row)):
                aux = row[i]
                row[i] = str(aux[0])

            model.setStringList(row)
            self.completer.setModel(model)


    def set_table_model(self, qtable, geom_type, expr_filter):
        """ Sets a TableModel to @widget_name attached to
            @table_name and filter @expr_filter
        """

        expr = None
        if expr_filter:
            # Check expression
            (is_valid, expr) = self.check_expression(expr_filter)  # @UnusedVariable
            if not is_valid:
                return expr

        # Set a model with selected filter expression
        table_name = "v_edit_" + geom_type
        if self.schema_name not in table_name:
            table_name = self.schema_name + "." + table_name

        # Set the model
        model = QSqlTableModel()
        model.setTable(table_name)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.select()
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())
            return expr

        # Attach model to selected widget
        if type(qtable) is QTableView:
            widget = qtable
        else:
            message = "Table_object is not a table name or QTableView"
            self.controller.log_info(message)
            return expr

        if expr_filter:
            widget.setModel(model)
            widget.model().setFilter(expr_filter)
            widget.model().select()
        else:
            widget.setModel(None)

        return expr

    def apply_lazy_init(self, widget):
        """Apply the init function related to the model. It's necessary
        a lazy init because model is changed everytime is loaded."""
        if self.lazy_widget is None:
            return
        if widget != self.lazy_widget:
            return
        self.lazy_init_function(self.lazy_widget)

    def lazy_configuration(self, widget, init_function):
        """set the init_function where all necessary events are set.
        This is necessary to allow a lazy setup of the events because set_table_events
        can create a table with a None model loosing any event connection."""
        # TODO: create a dictionary with key:widged.objectName value:initFuction
        # to allow multiple lazy initialization
        self.lazy_widget = widget
        self.lazy_init_function = init_function


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



    def connect_signal_selection_changed(self, table_object):
        """ Connect signal selectionChanged """

        try:
            self.canvas.selectionChanged.connect(partial(self.selection_changed, table_object, self.geom_type))
        except Exception:
            pass

    def disconnect_signal_selection_changed(self):
        """ Disconnect signal selectionChanged """

        try:
            self.canvas.selectionChanged.disconnect()
        except Exception:
            pass


    def selection_changed(self, qtable, geom_type):
        """ Slot function for signal 'canvas.selectionChanged' """

        self.disconnect_signal_selection_changed()

        field_id = geom_type + "_id"
        self.ids = []

        # Iterate over all layers of the group
        for layer in self.layers[self.geom_type]:
            if layer.selectedFeatureCount() > 0:
                # Get selected features of the layer
                features = layer.selectedFeatures()
                for feature in features:
                    # Append 'feature_id' into the list
                    selected_id = feature.attribute(field_id)
                    if selected_id not in self.ids:
                        self.ids.append(selected_id)

        if geom_type == 'node':
            self.list_ids['node'] = self.ids

        expr_filter = None
        if len(self.ids) > 0:
            # Set 'expr_filter' with features that are in the list
            expr_filter = "\"" + field_id + "\" IN ("
            for i in range(len(self.ids)):
                expr_filter += "'" + str(self.ids[i]) + "', "
            expr_filter = expr_filter[:-2] + ")"

            # Check expression
            (is_valid, expr) = self.check_expression(expr_filter)  # @UnusedVariable
            if not is_valid:
                return

            self.select_features_by_ids(geom_type, expr)

        # Reload contents of table 'tbl_@table_object_x_@geom_type'
        self.reload_table(qtable, self.geom_type, expr_filter)
        self.apply_lazy_init(qtable)
        # Remove selection in generic 'v_edit' layers
        self.remove_selection(False)

        self.connect_signal_selection_changed(qtable)


    def reload_table(self, qtable, geom_type, expr_filter):
        """ Reload @widget with contents of @tablename applying selected @expr_filter """

        if type(qtable) is QTableView:
            widget = qtable
        else:
            message = "Table_object is not a table name or QTableView"
            self.controller.log_info(message)
            return None

        expr = self.set_table_model(widget, geom_type, expr_filter)
        return expr