"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
import os
import sys

from PyQt4.QtGui import QLayout

from parent import ParentAction
from PyQt4.QtSql import QSqlTableModel
from PyQt4.QtGui import QAbstractItemView, QTableView, QLineEdit

from ..ui.tree_manage import TreeManage
from ..ui.multirow_selector import Multirow_selector
import utils

from functools import partial

plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(plugin_path)


class Basic(ParentAction):
    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'basic' """
        self.minor_version = "3.0"
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)

    def set_tree_manage(self, tree_manage):
        self.tree_manage = tree_manage

    def set_project_type(self, project_type):
        self.project_type = project_type

    def main_tree_manage(self):
        """ Button 01: Tree selector """

        dlg_tree_manage = TreeManage()
        utils.setDialog(dlg_tree_manage)
        dlg_tree_manage.setFixedSize(300, 170)

        self.load_settings(dlg_tree_manage)
        dlg_tree_manage.rejected.connect(partial(self.close_dialog, dlg_tree_manage))
        dlg_tree_manage.btn_cancel.pressed.connect(partial(self.close_dialog, dlg_tree_manage))
        dlg_tree_manage.btn_accept.pressed.connect(partial(self.get_parameters, dlg_tree_manage))
        table_name = 'planning'
        self.populate_cmb_years(table_name, dlg_tree_manage.cbx_years)
        dlg_tree_manage.exec_()

    def populate_cmb_years(self, table_name, combo):
        sql = ("SELECT DISTINCT(plan_year)::text, plan_year::text FROM "+self.schema_name+"."+table_name +""
               " WHERE plan_year::text != ''")
        rows = self.controller.get_rows(sql, log_sql=True)
        self.controller.log_info(str(rows))
        utils.set_item_data(combo, rows, 1)


    def get_parameters(self, dialog):
        if utils.isChecked(dialog.chk_year):
            year = utils.get_item_data(dialog.cbx_years, 0)
            self.close_dialog(dialog)
            self.tree_selector(year)



    def tree_selector(self, year):
        dlg_selector = Multirow_selector()
        utils.setDialog(dlg_selector)
        self.load_settings(dlg_selector)
        dlg_selector.btn_ok.pressed.connect(partial(self.close_dialog, dlg_selector))
        dlg_selector.rejected.connect(partial(self.close_dialog, dlg_selector))
        dlg_selector.setWindowTitle("Tree selector")
        # tableleft = "node"
        # tableright = "v_edit_node"
        # field_id_left = "node_id"
        # field_id_right = "node_id"
        # self.multi_row_selector(self.dlg_selector, tableleft, tableright, field_id_left, field_id_right)
        qtable_all_rows = dlg_selector.findChild(QTableView, "all_rows")
        qtable_all_rows.setSelectionBehavior(QAbstractItemView.SelectRows)
        qtable_selected_rows = dlg_selector.findChild(QTableView, "selected_rows")
        qtable_selected_rows.setSelectionBehavior(QAbstractItemView.SelectRows)
        txt_search = dlg_selector.findChild(QLineEdit, "txt_search")


        tbl_all_rows = 'v_plan_mu'
        tbl_selected_rows = 'planning'
        id_table_left = 'mu_id'
        id_table_right = 'mu_id'

        # Filter field
        txt_search.textChanged.connect(partial(self.fill_table, qtable_all_rows, tbl_all_rows, QTableView.DoubleClicked, True, txt_search))
        # Button selec
        dlg_selector.btn_select.pressed.connect(partial(self.rows_selector, qtable_all_rows, qtable_selected_rows, id_table_left, tbl_selected_rows, id_table_right, 'id'))
        qtable_all_rows.doubleClicked.connect(partial(self.rows_selector, qtable_all_rows, qtable_selected_rows, id_table_left, tbl_selected_rows, id_table_right, 'id'))

        # Button unselect
        dlg_selector.btn_unselect.pressed.connect(partial(self.rows_unselector, tbl_all_rows, tbl_selected_rows, id_table_right, txt_search))

        self.fill_table(qtable_all_rows, tbl_all_rows)
        self.fill_table(qtable_selected_rows, tbl_selected_rows)

        dlg_selector.exec_()


    def fill_table(self, widget, table_name, set_edit_triggers=QTableView.NoEditTriggers, expr=False, txt_search=None):
        """ Set a model with selected filter.
        Attach that model to selected table
        @setEditStrategy:
            0: OnFieldChange
            1: OnRowChange
            2: OnManualSubmit
        """

        # Set model
        model = QSqlTableModel()
        model.setTable(self.schema_name + "." + table_name)
        model.setEditStrategy(QSqlTableModel.OnFieldChange)
        model.setSort(0, 0)
        model.select()

        widget.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())
        # Attach model to table view
        if expr:
            expression = " mu_name ILIKE '%" + txt_search.text() + "%'"
            widget.setModel(model)
            widget.model().setFilter(expression)
        else:
            widget.setModel(model)

    def rows_selector(self, qtable_all_rows, qtable_selected_rows, id_table_left, tableright, id_table_right, field_id):
        """ Copy the selected lines in the @qtable_all_rows and in the @table table """
        selected_list = qtable_all_rows.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message)
            return
        field_list = []
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            id_ = qtable_all_rows.model().record(row).value(id_table_left)
            self.controller.log_info(str(id_))
            field_list.append(id_)

        self.controller.log_info(str(field_list))
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            values = ""


            if qtable_all_rows.model().record(row).value(id_table_left) != None:
                values += "'" + str(qtable_all_rows.model().record(row).value(id_table_left)) + "', "
            else:
                values += 'null, '
            if qtable_all_rows.model().record(row).value('work_id') != None:
                values += "'" + str(qtable_all_rows.model().record(row).value('work_id')) + "', "
            else:
                values += 'null, '

            values = values[:len(values) - 2]
            self.controller.log_info(str("VALUES: ")+str(values))
            # Check if expl_id already exists in expl_selector
            sql = ("SELECT " + id_table_right + ""
                   " FROM " + self.schema_name + "." + tableright + ""
                   " WHERE " + id_table_right + " = '" + str(field_list[i]) + "'")

            self.controller.log_info(str(sql))
            row = self.controller.get_row(str(sql))
            self.controller.log_info(str(row))
            if row is not None:
                # if exist - show warning
                message = "Id already selected"
                self.controller.show_info_box(message, "Info", parameter=str(field_list[i]))
            else:
                sql = ("INSERT INTO " + self.schema_name + "." + tableright + ""
                       " (mu_id, work_id) "
                       " VALUES (" + values + ")")
                self.controller.execute_sql(sql)

        # Refresh
        #expr = " psector_id = '" + str(utils_giswater.getWidgetText('psector_id')) + "'"
        # Refresh model with selected filter
        self.fill_table(qtable_selected_rows, tableright, QTableView.DoubleClicked)
        self.set_table_columns(qtable_selected_rows, tableright)

    def rows_unselector(self, tbl_selected_rows, tableright, field_id_right, txt_search):
        query = ("DELETE FROM " + self.schema_name + "." + tableright + ""
                 " WHERE  " + tableright + "." + field_id_right + " = ")
        selected_list = tbl_selected_rows.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message)
            return
            field_list = []
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            id_ = str(tbl_selected_rows.model().record(row).value(field_id_right))
            field_list.append(id_)
        for i in range(0, len(expl_id)):
            sql = (query + "'" + str(field_list[i]) + "'")

            self.controller.execute_sql(sql)


        # Refresh model with selected filter
        self.fill_table(tbl_selected_rows, tableright,  QTableView.DoubleClicked, True, txt_search)
        self.set_table_columns(tbl_selected_rows, tableright)









