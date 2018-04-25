"""
This file is part of tree_manage 1.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
import os
import sys
import datetime


from parent import ParentAction
from PyQt4.QtSql import QSqlTableModel
from PyQt4.QtGui import QAbstractItemView, QTableView, QIntValidator, QComboBox

from ..ui.month_manage import MonthManage
from ..ui.month_selector import MonthSelector

from ..ui.tree_selector import TreeSelector
from ..ui.tree_manage import TreeManage

import utils

from functools import partial

plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(plugin_path)


class Basic(ParentAction):
    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'basic' """
        self.minor_version = "3.0"
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)

        self.selected_year = None
        self.plan_year = None

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

        validator = QIntValidator(1, 9999999)
        dlg_tree_manage.txt_year.setValidator(validator)
        table_name = 'planning'
        self.populate_cmb_years(table_name, dlg_tree_manage.cbx_years)
        dlg_tree_manage.rejected.connect(partial(self.close_dialog, dlg_tree_manage))
        dlg_tree_manage.btn_cancel.pressed.connect(partial(self.close_dialog, dlg_tree_manage))
        dlg_tree_manage.btn_accept.pressed.connect(partial(self.get_year, dlg_tree_manage))
      
        #TODO borrar estas tres lineas
        now = datetime.datetime.now()
        utils.setWidgetText(dlg_tree_manage.txt_year, str(now.year + 1))
        utils.setChecked(dlg_tree_manage.chk_year, True)
        utils.set_combo_itemData(dlg_tree_manage.cbx_years, str(now.year + 1), 1)

        dlg_tree_manage.exec_()

    def populate_cmb_years(self, table_name, combo, reverse=False):
        """
        sql = ("SELECT current_database()")
        rows = self.controller.get_rows(sql)
        self.controller.log_info(str(rows))
        """
        sql = ("SELECT DISTINCT(plan_year)::text, plan_year::text FROM "+self.schema_name+"."+table_name + ""
               " WHERE plan_year::text != ''")
        rows = self.controller.get_rows(sql, log_sql=True)
        if rows is None:
            return

        utils.set_item_data(combo, rows, 1, reverse)


    def get_year(self, dialog):
        update = False
        self.selected_year = None

        if dialog.txt_year.text() != '':
            self.plan_year = utils.getWidgetText(dialog.txt_year)
            sql = ("SELECT year from "+self.schema_name+".v_plan_mu "
                   " WHERE year='"+self.plan_year+"'")
            row = self.controller.get_row(sql)
            if row is None:
                message = "No hi ha preus per aquest any"
                self.controller.show_warning(message)
                return None
            if utils.isChecked(dialog.chk_year) and utils.get_item_data(dialog.cbx_years, 0) != -1:
                self.selected_year = utils.get_item_data(dialog.cbx_years, 0)
                sql = ("SELECT DISTINCT(plan_year) FROM " + self.schema_name + ".planning"
                       " WHERE plan_year ='" + str(self.selected_year) + "'")
                row = self.controller.get_row(sql)
                if row:
                    update = True
            else:
                self.selected_year = self.plan_year
            self.close_dialog(dialog)
            self.tree_selector(update)

        else:
            message = "Any recuperat es obligatori"
            self.controller.show_warning(message)
            return None


    def tree_selector(self, update=False):

        dlg_selector = TreeSelector()
        utils.setDialog(dlg_selector)
        self.load_settings(dlg_selector)

        dlg_selector.setWindowTitle("Tree selector")

        tableleft = 'v_plan_mu'
        tableright = 'planning'
        id_table_left = 'mu_id'
        id_table_right = 'mu_id'

        dlg_selector.all_rows.setSelectionBehavior(QAbstractItemView.SelectRows)
        dlg_selector.selected_rows.setSelectionBehavior(QAbstractItemView.SelectRows)

        sql = ("SELECT DISTINCT(work_id), work_name FROM "+self.schema_name + "." + tableleft)
        rows = self.controller.get_rows(sql)
        utils.set_item_data(dlg_selector.cmb_poda_type, rows, 1)

        # CheckBox
        dlg_selector.chk_permanent.stateChanged.connect(partial(self.force_chk_current, dlg_selector))

        # Button selec
        dlg_selector.btn_select.pressed.connect(partial(self.rows_selector, dlg_selector, id_table_left, tableright, id_table_right, tableleft))
        dlg_selector.all_rows.doubleClicked.connect(partial(self.rows_selector, dlg_selector, id_table_left, tableright, id_table_right, tableleft))

        # Button unselect
        dlg_selector.btn_unselect.pressed.connect(partial(self.rows_unselector, dlg_selector, tableright, id_table_right, tableleft))
        dlg_selector.selected_rows.doubleClicked.connect(partial(self.rows_unselector, dlg_selector, tableright, id_table_right, tableleft))

        # Populate QTableView
        self.fill_table(dlg_selector, tableright, set_edit_triggers=QTableView.NoEditTriggers, update=True)
        if update:
            self.insert_into_planning(dlg_selector, id_table_left, tableright)

        # Need fill table before set table columns, and need re-fill table for upgrade fields
        self.set_table_columns(dlg_selector.selected_rows, tableright)

        self.fill_table(dlg_selector, tableright, QTableView.DoubleClicked)
        self.fill_main_table(dlg_selector, tableleft)
        self.set_table_columns(dlg_selector.all_rows, tableleft)
        # # Filter field
        dlg_selector.txt_search.textChanged.connect(partial(self.fill_main_table, dlg_selector, tableleft))
        dlg_selector.txt_selected_filter.textChanged.connect(partial(self.fill_table, dlg_selector, tableright, tableleft))

        dlg_selector.btn_close.pressed.connect(partial(self.close_dialog, dlg_selector))
        dlg_selector.btn_close.pressed.connect(partial(self.close_dialog, dlg_selector))

        dlg_selector.rejected.connect(partial(self.close_dialog, dlg_selector))
        dlg_selector.rejected.connect(partial(self.close_dialog, dlg_selector))

        dlg_selector.exec_()


    def force_chk_current(self, dialog):
        if utils.isChecked(dialog.chk_permanent):
            utils.setChecked(dialog.chk_current, True)


    def fill_main_table(self, dialog, table_name,  set_edit_triggers=QTableView.NoEditTriggers):
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

        dialog.all_rows.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())

        # Get all ids from Qtable selected_rows
        id_all_selected_rows = self.select_all_rows(dialog.selected_rows, 'mu_id')

        # Convert id_all_selected_rows to string
        ids = "0, "
        for x in range(0, len(id_all_selected_rows)):
            ids += str(id_all_selected_rows[x]) + ", "
        ids = ids[:-2] + ""

        # Attach model to table view
        expr = " mu_name ILIKE '%" + dialog.txt_search.text() + "%'"
        expr += " AND mu_id NOT IN ("+ids+")"
        expr += " AND year::text ILIKE '%"+str(self.plan_year)+"%'"
        dialog.all_rows.setModel(model)
        dialog.all_rows.model().setFilter(expr)


    def fill_table(self, dialog, tableright, set_edit_triggers=QTableView.NoEditTriggers, update=False):
        """ Set a model with selected filter.
        Attach that model to selected table
        @setEditStrategy:
            0: OnFieldChange
            1: OnRowChange
            2: OnManualSubmit
        """

        # Set model
        model = QSqlTableModel()
        model.setTable(self.schema_name + "." + tableright)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setSort(0, 0)
        model.select()
        dialog.selected_rows.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())

        # Create expresion
        expr = " mu_id::text ILIKE '%" + dialog.txt_selected_filter.text() + "%'"
        if self.selected_year is not None:
            expr += " AND plan_year ='" + str(self.plan_year) + "'"
            if update:
                expr += " OR plan_year ='" + str(self.selected_year) + "'"

        # Attach model to table or view
        dialog.selected_rows.setModel(model)
        dialog.selected_rows.model().setFilter(expr)

        # Set year to plan to all rows in list
        for x in range(0, model.rowCount()):
            i = int(dialog.selected_rows.model().fieldIndex('plan_year'))
            index = dialog.selected_rows.model().index(x, i)
            model.setData(index, self.plan_year)
        self.calculate_total_price(dialog)


    def calculate_total_price(self, dialog):
        """ Update QLabel @lbl_totala_price with sum of all price in @select_rows """
        selected_list = dialog.selected_rows.model()
        if selected_list is None:
            return
        total = 0

        for x in range(0, selected_list.rowCount()):
            if str(dialog.selected_rows.model().record(x).value('plan_year')) == str(self.plan_year):
                if str(dialog.selected_rows.model().record(x).value('price')) != 'NULL':
                    total += float(dialog.selected_rows.model().record(x).value('price'))
        utils.setText(dialog.lbl_totala_price, str(total))


    def insert_into_planning(self, dialog, id_table_left, tableright):
        dialog.selected_rows.selectAll()
        left_selected_list = dialog.selected_rows.selectionModel().selectedRows()
        if len(left_selected_list) == 0:
            return

        field_list = []
        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            id_ = dialog.selected_rows.model().record(row).value(id_table_left)
            field_list.append(id_)

        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            insert_values = ""
            function_values = ""
            if dialog.selected_rows.model().record(row).value('mu_id') is not None:
                insert_values += "'" + str(dialog.selected_rows.model().record(row).value('mu_id')) + "', "
                function_values += "'" + str(dialog.selected_rows.model().record(row).value('mu_id')) + "', "
            else:
                insert_values += 'null, '
            if dialog.selected_rows.model().record(row).value('work_id') is not None:
                insert_values += "'" + str(dialog.selected_rows.model().record(row).value('work_id')) + "', "
                function_values += "'" + str(dialog.selected_rows.model().record(row).value('work_id')) + "', "
            else:
                insert_values += 'null, '
            if str(dialog.selected_rows.model().record(row).value('price')) != 'NULL':
                insert_values += "'" + str(dialog.selected_rows.model().record(row).value('price')) + "', "
            else:
                insert_values += 'null, '
            insert_values += "'"+self.plan_year+"', "
            insert_values = insert_values[:len(insert_values) - 2]
            function_values += ""+self.plan_year+", "
            function_values = function_values[:len(function_values) - 2]

            # Check if mul_id and year_ already exists in planning
            sql = ("SELECT  mu_id  "
                   " FROM " + self.schema_name + "." + tableright + ""
                   " WHERE mu_id = '" + str(field_list[i]) + "'"
                   " AND plan_year ='"+str(self.plan_year)+"'")
            row = self.controller.get_row(sql)

            if row is None:
                #     # Put a new row in QTableView
                #     # dialog.selected_rows.model().insertRow(dialog.selected_rows.verticalHeader().count())
                #
                sql = ("INSERT INTO " + self.schema_name + "." + tableright + ""
                       " (mu_id, work_id, price, plan_year) "
                       " VALUES (" + insert_values + ")")
                self.controller.execute_sql(sql)
                sql = ("SELECT " + self.schema_name + ".set_plan_price(" + function_values + ")")
                self.controller.execute_sql(sql)


    def rows_selector(self, dialog, id_table_left, tableright, id_table_right, tableleft):
        """ Copy the selected lines in the qtable_all_rows and in the table """
        left_selected_list = dialog.all_rows.selectionModel().selectedRows()
        if len(left_selected_list) == 0:
            message = "Cap registre seleccionat"
            self.controller.show_warning(message)
            return
        # Get all selected ids
        field_list = []
        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            id_ = dialog.all_rows.model().record(row).value(id_table_left)
            field_list.append(id_)

        # Select all rows and get all id
        self.select_all_rows(dialog.selected_rows, id_table_right)
        if utils.isChecked(dialog.chk_current):
            current_poda_type = utils.get_item_data(dialog.cmb_poda_type, 0)
            if current_poda_type is None:
                message = "No heu seleccionat cap poda"
                self.controller.show_warning(message)
                return
        if utils.isChecked(dialog.chk_permanent):
            for i in range(0, len(left_selected_list)):
                row = left_selected_list[i].row()
                sql = ("UPDATE " + self.schema_name + ".cat_mu "
                       " SET work_id ='"+str(current_poda_type)+"' "
                       " WHERE id ='"+str(dialog.all_rows.model().record(row).value('mu_id'))+"'")
                self.controller.execute_sql(sql)

        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            values = ""
            if dialog.all_rows.model().record(row).value('mu_id') is not None:
                values += "'" + str(dialog.all_rows.model().record(row).value('mu_id')) + "', "
            else:
                values += 'null, '
            if dialog.all_rows.model().record(row).value('work_id') is not None:
                if utils.isChecked(dialog.chk_current):
                    values += "'" + str(current_poda_type) + "', "
                else:
                    values += "'" + str(dialog.all_rows.model().record(row).value('work_id')) + "', "
            else:
                values += 'null, '
            values += "'"+self.plan_year+"', "
            values = values[:len(values) - 2]

            # Check if mul_id and year_ already exists in planning
            sql = ("SELECT " + id_table_right + ""
                   " FROM " + self.schema_name + "." + tableright + ""
                   " WHERE " + id_table_right + " = '" + str(field_list[i]) + "'"
                   " AND plan_year ='"+str(self.plan_year)+"'")
            row = self.controller.get_row(sql)
            if row is not None:
                # if exist - show warning
                message = "Aquest registre ja esta seleccionat"
                self.controller.show_info_box(message, "Info", parameter=str(field_list[i]))
            else:
                # Put a new row in QTableView
                # dialog.selected_rows.model().insertRow(dialog.selected_rows.verticalHeader().count())

                sql = ("INSERT INTO " + self.schema_name + "." + tableright + ""
                       " (mu_id, work_id, plan_year) "
                       " VALUES (" + values + ")")
                self.controller.execute_sql(sql)
                sql = ("SELECT " + self.schema_name + ".set_plan_price(" + values + ")")
                self.controller.execute_sql(sql)

        # Refresh
        self.fill_table(dialog, tableright)
        self.fill_main_table(dialog, tableleft)





    def rows_unselector(self, dialog, tableright, field_id_right, tableleft):

        query = ("DELETE FROM " + self.schema_name + "." + tableright + ""
                 " WHERE  plan_year='" + self.plan_year + "' AND " + field_id_right + " = ")
        selected_list = dialog.selected_rows.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Cap registre seleccionat"
            self.controller.show_warning(message)
            return
        field_list = []
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            id_ = str(dialog.selected_rows.model().record(row).value(field_id_right))
            field_list.append(id_)
        for i in range(0, len(field_list)):
            sql = (query + "'" + str(field_list[i]) + "'")
            self.controller.execute_sql(sql)
        # Refresh model with selected filter
        self.fill_table(dialog, tableright)
        self.fill_main_table(dialog, tableleft)





    def basic_month_manage(self):
        """ Button 02: Planned year manage """
        dlg_month_manage = MonthManage()
        utils.setDialog(dlg_month_manage)
        self.load_settings(dlg_month_manage)
        dlg_month_manage.setWindowTitle("Planificador mensual")

        table_name = 'planning'
        self.populate_cmb_years(table_name, dlg_month_manage.cbx_years, reverse=True)

        dlg_month_manage.rejected.connect(partial(self.close_dialog, dlg_month_manage))
        dlg_month_manage.btn_cancel.pressed.connect(partial(self.close_dialog, dlg_month_manage))
        dlg_month_manage.btn_accept.pressed.connect(partial(self.get_planned_year, dlg_month_manage))

        dlg_month_manage.exec_()


    def get_planned_year(self, dialog):

        if str(utils.getWidgetText(dialog.txt_info)) == 'null':
            message = "El camp text a no pot estar vuit"
            self.controller.show_warning(message)
            return


        self.text = str(utils.getWidgetText(dialog.txt_info))
        self.planned_year = utils.get_item_data(dialog.cbx_years, 0)
        self.controller.log_info(str(self.planned_year))
        self.close_dialog(dialog)
        self.month_selector()




    def month_selector(self):
        dlg_month_selector = MonthSelector()
        utils.setDialog(dlg_month_selector)
        self.load_settings(dlg_month_selector)
        dlg_month_selector.setWindowTitle("Planificador mensual")
        tableright = 'planning'
        self.controller.log_info(str(self.text))
        dlg_month_selector.lbl_info.setText(self.text)

        self.fill_table_planned_year(dlg_month_selector, tableright, set_edit_triggers=QTableView.NoEditTriggers)


        # Filter field
        #dlg_month_selector.txt_search.textChanged.connect(partial(self.filter_by_text, dlg_month_selector.all_rows, tableright, 'mu_id'))
        dlg_month_selector.txt_selected_filter.textChanged.connect(partial(self.fill_table, dlg_selector, tableright, tableleft))

        dlg_month_selector.exec_()
    def filter_by_text(self, table, widget_txt, tablename, field):

        result_select = utils.getWidgetText(widget_txt)
        if result_select != 'null':
            expr = field + "  ILIKE '%" + result_select + "%'"
            # Refresh model with selected filter
            table.model().setFilter(expr)
            table.model().select()
        else:
            self.fill_table_planned_year(table, tablename)

    def fill_table_planned_year(self, dialog, tableright, set_edit_triggers=QTableView.NoEditTriggers):

        """ Set a model with selected filter.
        Attach that model to selected table
        @setEditStrategy:
            0: OnFieldChange
            1: OnRowChange
            2: OnManualSubmit
        """

        # Set model
        model = QSqlTableModel()
        model.setTable(self.schema_name + "." + tableright)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setSort(0, 0)
        model.select()
        #dialog.all_rows.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())
        # Create expresion
        expr = " plan_year = '" + str(self.planned_year) + "'"
        dialog.all_rows.setModel(model)
        dialog.all_rows.model().setFilter(expr)


    def select_all_rows(self, qtable, id, clear_selection=True):
        """ retrun list of index in @qtable"""
        # Select all rows and get all id
        qtable.selectAll()
        right_selected_list = qtable.selectionModel().selectedRows()
        right_field_list = []
        for i in range(0, len(right_selected_list)):
            row = right_selected_list[i].row()
            id_ = qtable.model().record(row).value(id)
            right_field_list.append(id_)
        if clear_selection:
            qtable.clearSelection()
        return right_field_list

    def get_table_columns(self, tablename):
        # Get columns name in order of the table
        sql = ("SELECT column_name FROM information_schema.columns"
               " WHERE table_name = '" + tablename + "'"
               " AND table_schema = '" + self.schema_name.replace('"', '') + "'"
               " ORDER BY ordinal_position")
        column_name = self.controller.get_rows(sql)
        return column_name


    def accept_changes(self, dialog, tableleft):
        model = dialog.selected_rows.model()
        model.database().transaction()
        if model.submitAll():
            model.database().commit()

            dialog.selected_rows.selectAll()
            id_all_selected_rows = dialog.selected_rows.selectionModel().selectedRows()

            for x in range(0, len(id_all_selected_rows)):
                row = id_all_selected_rows[x].row()
                if dialog.selected_rows.model().record(row).value('work_id') is not None:
                    work_id = str(dialog.selected_rows.model().record(row).value('work_id'))
                    mu_id = str(dialog.selected_rows.model().record(row).value('mu_id'))
                    sql = ("UPDATE " + self.schema_name+"."+tableleft + ""
                           " SET work_id= '"+str(work_id)+"' "
                           " WHERE mu_id= '"+str(mu_id)+"'")
                    self.controller.execute_sql(sql)
        else:
            model.database().rollback()


    def cancel_changes(self, dialog):
        model = dialog.selected_rows.model()
        model.revertAll()
        model.database().rollback()




        # def populate_combos(self, dialog, tableleft, tableright):
        #     """ Set one column of a QtableView as QComboBox with values from database. """
        #     sql = ("SELECT * FROM " + self.schema_name + "." + tableright + " "
        #            " WHERE plan_year = " + self.selected_year + " order by id")
        #     rows = self.controller.get_rows(sql)
        #     for x in range(0, len(rows)):
        #         combo = QComboBox()
        #         sql = "SELECT DISTINCT(work_id) FROM " + self.schema_name+"."+tableleft + " ORDER BY work_id"
        #         row = self.controller.get_rows(sql)
        #
        #         utils.fillComboBox(combo, row, False)
        #         row = rows[x]
        #         priority = row[7]
        #
        #         utils.setSelectedItem(combo, str(priority))
        #         i = dialog.selected_rows.model().index(x, 7)
        #
        #         dialog.selected_rows.setIndexWidget(i, combo)
        #         combo.setStyleSheet("background:#E6E6E6")
        #         combo.currentIndexChanged.connect(partial(self.update_combobox_values, dialog.selected_rows, combo, x))
        #
        #
        # def update_combobox_values(self, qtable, combo, x):
        #     """ Insert combobox.currentText into widget (QTableView) """
        #     index = qtable.model().index(x, 7)
        #     qtable.model().setData(index, combo.currentText())
        #
        #
        # def refresh_table(self, dialog, tableright, set_edit_triggers=QTableView.NoEditTriggers):
        #     """ Refresh qTableView 'selected_rows' """
        #     # Set model
        #     model = QSqlTableModel()
        #
        #     model.setTable(self.schema_name + "." + tableright)
        #     model.setEditStrategy(QSqlTableModel.OnFieldChange)
        #     model.setSort(0, 0)
        #     model.select()
        #     dialog.selected_rows.setEditTriggers(set_edit_triggers)
        #     # Check for errors
        #     if model.lastError().isValid():
        #         self.controller.show_warning(model.lastError().text())
        #     # Attach model to table view
        #
        #     expr = " mu_id::text ILIKE '%" + dialog.txt_selected_filter.text() + "%'"
        #
        #     if self.selected_year is not None:
        #         expr += " AND plan_year ='" + str(self.selected_year) + "'"
        #     dialog.selected_rows.setModel(model)
        #     dialog.selected_rows.model().setFilter(expr)