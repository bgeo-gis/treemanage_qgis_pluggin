"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
import os
import sys

from parent import ParentAction
from PyQt4.QtSql import QSqlTableModel
from PyQt4.QtGui import QAbstractItemView, QTableView, QLineEdit,QComboBox

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
        dlg_tree_manage.btn_accept.pressed.connect(partial(self.get_year, dlg_tree_manage))
        table_name = 'planning'
        self.populate_cmb_years(table_name, dlg_tree_manage.cbx_years)
        dlg_tree_manage.exec_()

    def populate_cmb_years(self, table_name, combo):
        sql = ("SELECT DISTINCT(plan_year)::text, plan_year::text FROM "+self.schema_name+"."+table_name +""
               " WHERE plan_year::text != ''")
        rows = self.controller.get_rows(sql, log_sql=True)
        utils.set_item_data(combo, rows, 1)


    def get_year(self, dialog):
        if utils.isChecked(dialog.chk_year):
            year = utils.get_item_data(dialog.cbx_years, 0)
        elif dialog.txt_year.text() != '':
            year = utils.getWidgetText(dialog.txt_year)
        else:
            return None

        self.close_dialog(dialog)
        self.tree_selector(year, utils.isChecked(dialog.chk_year))



    def tree_selector(self, year=None , recover=False):

        dlg_selector = Multirow_selector()
        utils.setDialog(dlg_selector)
        self.load_settings(dlg_selector)

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
        txt_selected_filter = dlg_selector.findChild(QLineEdit, "txt_selected_filter")

        tbl_all_rows = 'v_plan_mu'
        tbl_selected_rows = 'planning'
        id_table_left = 'mu_id'
        id_table_right = 'mu_id'

        # Filter field
        txt_search.textChanged.connect(partial(self.fill_main_table, qtable_all_rows, tbl_all_rows, txt_search, True))
        txt_selected_filter.textChanged.connect(partial(self.fill_table, qtable_selected_rows, tbl_selected_rows, txt_selected_filter, expr=True, year=year, set_edit_triggers=QTableView.NoEditTriggers))
        # Button selec
        dlg_selector.btn_select.pressed.connect(partial(self.rows_selector, qtable_all_rows, qtable_selected_rows, id_table_left, tbl_selected_rows, id_table_right, 'id', year))
        qtable_all_rows.doubleClicked.connect(partial(self.rows_selector, qtable_all_rows, qtable_selected_rows, id_table_left, tbl_selected_rows, id_table_right, 'id'))

        # Button unselect
        dlg_selector.btn_unselect.pressed.connect(partial(self.rows_unselector, tbl_all_rows, tbl_selected_rows, id_table_right, txt_search))

        self.fill_main_table(qtable_all_rows, tbl_all_rows)
        self.fill_table(qtable_selected_rows, tbl_selected_rows, txt_selected_filter, expr=True, year=year, set_edit_triggers=QTableView.NoEditTriggers)

        dlg_selector.btn_ok.pressed.connect(partial(self.accept_changes, qtable_selected_rows))
        dlg_selector.btn_ok.pressed.connect(partial(self.close_dialog, dlg_selector))
        dlg_selector.btn_cancel.pressed.connect(partial(self.close_dialog, dlg_selector))
        dlg_selector.rejected.connect(partial(self.close_dialog, dlg_selector))

        dlg_selector.exec_()

    def accept_changes(self, qtable):
        model = qtable.model()
        model.database().transaction()
        if model.submitAll():
            model.database().commit()
        else:
            model.database().rollback()

    def fill_main_table(self, widget, table_name, txt_search=None, expr=None, set_edit_triggers=QTableView.NoEditTriggers):
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

    def fill_table(self, widget, table_name,  txt_selected_filter, expr=False, year=None, set_edit_triggers=QTableView.NoEditTriggers):
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
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setSort(0, 0)
        model.select()

        widget.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())
        # Attach model to table view
        if expr:
            expression = " mu_id::text ILIKE '%" + txt_selected_filter.text() + "%'"
            if year is not None:
                expression += " AND plan_year ='" + str(year) + "'"
            widget.setModel(model)
            widget.model().setFilter(expression)
        else:
            widget.setModel(model)

        sql = ("SELECT * FROM " + self.schema_name+"."+table_name + " "
                " WHERE plan_year = "+year+" ORDER BY plan_year")

        rows = self.controller.get_rows(sql)
        for x in range(len(rows)):
            combo = QComboBox()
            sql = "SELECT DISTINCT(work_id) FROM " + self.schema_name+"."+table_name + " ORDER BY work_id"
            row = self.controller.get_rows(sql)
            utils.fillComboBox(combo, row, False)
            row = rows[x]
            priority = row[7]
            utils.setSelectedItem(combo, str(priority))
            i = widget.model().index(x, 7)
            widget.setIndexWidget(i, combo)
            combo.setStyleSheet("background:#E6E6E6")
            combo.currentIndexChanged.connect(partial(self.update_combobox_values, widget, combo, x))


    def update_combobox_values(self, widget, combo, x):
        """ Insert combobox.currentText into widget (QTableView) """
        index = widget.model().index(x, 7)
        widget.model().setData(index, combo.currentText())

    def rows_selector(self, qtable_all_rows, qtable_selected_rows, id_table_left, tableright, id_table_right, field_id, year):
        """ Copy the selected lines in the @qtable_all_rows and in the @table table """
        left_selected_list = qtable_all_rows.selectionModel().selectedRows()
        if len(left_selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message)
            return
        # Get all selected ids
        field_list = []
        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            id_ = qtable_all_rows.model().record(row).value(id_table_left)
            field_list.append(id_)

        # Select all rows and get all id
        qtable_selected_rows.selectAll()
        right_selected_list = qtable_selected_rows.selectionModel().selectedRows()
        right_field_list = []
        for i in range(0, len(right_selected_list)):
            row = right_selected_list[i].row()
            id_ = qtable_all_rows.model().record(row).value(id_table_right)
            right_field_list.append(id_)
        qtable_selected_rows.clearSelection()


        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
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

            # Check if expl_id already exists in expl_selector
            sql = ("SELECT " + id_table_right + ""
                   " FROM " + self.schema_name + "." + tableright + ""
                   " WHERE " + id_table_right + " = '" + str(field_list[i]) + "'")
            row = self.controller.get_row(str(sql))
            if row is not None:
                # if exist - show warning
                message = "Id already selected"
                self.controller.show_info_box(message, "Info", parameter=str(field_list[i]))
            else:
                sql = ("INSERT INTO " + self.schema_name + "." + tableright + ""
                       " (mu_id, work_id, year) "
                       " VALUES (" + values + ")")
                self.controller.execute_sql(sql)

        # Refresh
        #expr = " psector_id = '" + str(utils_giswater.getWidgetText('psector_id')) + "'"
        # Refresh model with selected filter
        self.fill_table(qtable_selected_rows, tableright, None, QTableView.DoubleClicked)
        self.set_table_columns(qtable_selected_rows, tableright)
    #
    def rows_unselector(self, tbl_selected_rows, tableright, field_id_right, txt_search):
        pass
    #     query = ("DELETE FROM " + self.schema_name + "." + tableright + ""
    #              " WHERE  " + tableright + "." + field_id_right + " = ")
    #     selected_list = tbl_selected_rows.selectionModel().selectedRows()
    #     if len(selected_list) == 0:
    #         message = "Any record selected"
    #         self.controller.show_warning(message)
    #         return
    #         field_list = []
    #     for i in range(0, len(selected_list)):
    #         row = selected_list[i].row()
    #         id_ = str(tbl_selected_rows.model().record(row).value(field_id_right))
    #         field_list.append(id_)
    #     for i in range(0, len(expl_id)):
    #         sql = (query + "'" + str(field_list[i]) + "'")
    #
    #         self.controller.execute_sql(sql)


        # Refresh model with selected filter
        self.fill_table(tbl_selected_rows, tableright, None, QTableView.DoubleClicked, True, txt_search)
        self.set_table_columns(tbl_selected_rows, tableright)









