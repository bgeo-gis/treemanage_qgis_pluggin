"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
from qgis.core import QgsExpression
from PyQt4.QtCore import Qt, QSettings
from PyQt4.QtGui import QStringListModel, QCompleter


import os
import sys
import webbrowser
import ConfigParser
from functools import partial
import gw_utilities

class ParentAction(object):
    def __init__(self, iface, settings, controller, plugin_dir):
        ''' Class constructor '''

        # Initialize instance attributes
        self.tree_manage_version = "1.0"
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.settings = settings
        self.controller = controller
        self.plugin_dir = plugin_dir
        self.dao = self.controller.dao
        self.schema_name = self.controller.schema_name
        self.project_type = None
        self.file_gsw = None
        self.gsw_settings = None


    def set_controller(self, controller):
        """ Set controller class """

        self.controller = controller
        self.schema_name = self.controller.schema_name

    def get_plugin_version(self):
        ''' Get plugin version from metadata.txt file '''

        # Check if metadata file exists
        metadata_file = os.path.join(self.plugin_dir, 'metadata.txt')
        if not os.path.exists(metadata_file):
            message = "Metadata file not found" + metadata_file
            self.controller.show_warning(message, parameter=metadata_file)
            return None

        metadata = ConfigParser.ConfigParser()
        metadata.read(metadata_file)
        plugin_version = metadata.get('general', 'version')
        if plugin_version is None:
            message = "Plugin version not found"
            self.controller.show_warning(message)

        return plugin_version







    def load_settings(self, dialog=None):
        """ Load QGIS settings related with dialog position and size """

        if dialog is None:
            dialog = self.dlg

        try:
            width = self.controller.plugin_settings_value(dialog.objectName() + "_width", dialog.width())
            height = self.controller.plugin_settings_value(dialog.objectName() + "_height", dialog.height())
            x = self.controller.plugin_settings_value(dialog.objectName() + "_x")
            y = self.controller.plugin_settings_value(dialog.objectName() + "_y")
            if int(x) < 0 or int(y) < 0:
                dialog.resize(int(width), int(height))
            else:
                dialog.setGeometry(int(x), int(y), int(width), int(height))
        except:
            pass

    def save_settings(self, dialog=None):
        """ Save QGIS settings related with dialog position and size """

        if dialog is None:
            dialog = self.dlg

        self.controller.plugin_settings_set_value(dialog.objectName() + "_width", dialog.width())
        self.controller.plugin_settings_set_value(dialog.objectName() + "_height", dialog.height())
        self.controller.plugin_settings_set_value(dialog.objectName() + "_x", dialog.pos().x() + 8)
        self.controller.plugin_settings_set_value(dialog.objectName() + "_y", dialog.pos().y() + 31)

    def open_dialog(self, dlg=None, dlg_name=None, maximize_button=True, stay_on_top=True):
        """ Open dialog """

        if dlg is None or type(dlg) is bool:
            dlg = self.dlg

        # Manage i18n of the dialog
        if dlg_name:
            self.controller.manage_translation(dlg_name, dlg)

            # Manage stay on top and maximize button
        if maximize_button and stay_on_top:
            dlg.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
        elif not maximize_button and stay_on_top:
            dlg.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowStaysOnTopHint)
        elif maximize_button and not stay_on_top:
            dlg.setWindowFlags(Qt.WindowMaximizeButtonHint)

            # Open dialog
        dlg.open()

    def close_dialog(self, dlg=None):
        """ Close dialog """

        # if dlg is None or type(dlg) is bool:
        #     dlg = self.dlg
        try:
            self.save_settings(dlg)
            dlg.close()
            map_tool = self.canvas.mapTool()
            # If selected map tool is from the plugin, set 'Pan' as current one
            if map_tool.toolName() == '':
                self.iface.actionPan().trigger()
        except AttributeError:
            pass



    def hide_colums(self, widget, comuns_to_hide):
        for i in range(0, len(comuns_to_hide)):
            widget.hideColumn(comuns_to_hide[i])




    def check_expression(self, expr_filter, log_info=False):
        """ Check if expression filter @expr_filter is valid """

        if log_info:
            self.controller.log_info(expr_filter)
        expr = QgsExpression(expr_filter)
        if expr.hasParserError():
            message = "Expression Error"
            self.controller.log_warning(message, parameter=expr_filter)
            return (False, expr)
        return (True, expr)




    def set_table_columns(self, widget, table_name, project_type=None):
        """ Configuration of tables. Set visibility and width of columns """

        widget = gw_utilities.getWidget(widget)
        if not widget:
            return

        # Set width and alias of visible columns
        columns_to_delete = []
        sql = ("SELECT column_index, width, alias, status"
               " FROM " + self.schema_name + ".config_client_forms"
               " WHERE table_id = '" + table_name + "'")
        if project_type is not None:
            sql += (" AND project_type = '" + project_type + "' ")
        sql += (" ORDER BY column_index")


        rows = self.controller.get_rows(sql, log_info=False)
        if not rows:
            return

        for row in rows:
            if not row['status']:
                columns_to_delete.append(row['column_index'] - 1)
            else:
                width = row['width']
                if width is not None:
                    widget.setColumnWidth(row['column_index'] - 1, width)
                widget.model().setHeaderData(row['column_index'] - 1, Qt.Horizontal, row['alias'])

        # Set order
        # widget.model().setSort(0, Qt.AscendingOrder)
        widget.model().select()

        # Delete columns
        for column in columns_to_delete:
            widget.hideColumn(column)

    def set_completer_object(self, tablename, widget, field_id):
        """ Set autocomplete of widget @table_object + "_id"
            getting id's from selected @table_object
        """
        if not widget:
            return

        # Set SQL
        sql = ("SELECT DISTINCT(" + field_id + ")"
               " FROM " + self.schema_name + "." + tablename + ""
               " ORDER BY " + field_id + "")
        row = self.controller.get_rows(sql)
        for i in range(0, len(row)):
            aux = row[i]
            row[i] = str(aux[0])

        # Set completer and model: add autocomplete in the widget
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        widget.setCompleter(self.completer)
        model = QStringListModel()
        model.setStringList(row)
        self.completer.setModel(model)




