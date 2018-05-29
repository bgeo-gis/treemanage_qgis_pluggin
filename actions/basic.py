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
from PyQt4.Qt import QDate
from PyQt4.QtSql import QSqlTableModel
from PyQt4.QtGui import QAbstractItemView, QTableView, QIntValidator, QComboBox


from ..actions.manage_visit import ManageVisit
from ..ui.new_prices import NewPrices
from ..ui.month_manage import MonthManage
from ..ui.month_selector import MonthSelector
from ..ui.price_management import PriceManagement
from ..ui.tree_manage import TreeManage
from ..ui.tree_selector import TreeSelector
from ..utils.widget_manager import WidgetManager


from functools import partial

plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(plugin_path)


class Basic(ParentAction):
    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'basic' """
        self.minor_version = "3.0"
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)
        self.manage_visit = ManageVisit(iface, settings, controller, plugin_dir)
        self.selected_year = None
        self.plan_year = None

    def set_tree_manage(self, tree_manage):
        self.tree_manage = tree_manage

    def set_project_type(self, project_type):
        self.project_type = project_type

    def basic_new_prices(self, dialog=None):
        """ Button 03: Price generator """
        # Close previous dialog
        if dialog is not None:
            self.close_dialog(dialog)
        self.dlg_new_prices = WidgetManager(NewPrices())
        self.load_settings(self.dlg_new_prices.dialog)

        validator = QIntValidator(1, 9999999)
        self.dlg_new_prices.dialog.txt_year.setValidator(validator)
        table_name = 'cat_price'
        field_id = 'year'
        field_name = 'year'

        self.dlg_new_prices.dialog.rejected.connect(partial(self.close_dialog, self.dlg_new_prices.dialog))
        self.dlg_new_prices.dialog.btn_cancel.clicked.connect(partial(self.close_dialog, self.dlg_new_prices.dialog))
        self.dlg_new_prices.dialog.btn_accept.clicked.connect(partial(self.manage_new_price_catalog))
        self.populate_cmb_years(self.dlg_new_prices, table_name, field_id, field_name,  self.dlg_new_prices.dialog.cbx_years)
        self.set_completer_object(table_name, self.dlg_new_prices.dialog.txt_year, 'year')
        self.dlg_new_prices.dialog.exec_()


    def manage_new_price_catalog(self):

        table_name = "cat_price"
        new_year = self.dlg_new_prices.dialog.txt_year.text()

        if new_year is None or new_year == '':
            msg = "Has de possar l'any corresponent"
            self.controller.show_warning(msg)
            return

        copy_years = self.dlg_new_prices.dialog.chk_year.isChecked()
        if copy_years:
            old_year = self.dlg_new_prices.get_item_data(self.dlg_new_prices.dialog.cbx_years)
            if old_year == -1:
                msg = "No tens cap any seleccionat, desmarca l'opcio de copiar preus"
                self.controller.show_warning(msg)
                return
        else:
            old_year = 0

        sql = ("SELECT DISTINCT(year) FROM " + self.schema_name + "." + str(table_name) + " "
               " WHERE year = '" + str(new_year) + "'")
        row = self.controller.get_row(sql)
        if not row or row is None:
            sql = ("SELECT " + self.schema_name + ".create_price('" + str(new_year) + "','" + str(old_year) + "')")
            self.controller.execute_sql(sql)
        else:
            message = ("Estas a punt de sobreescriure els preus de l'any " + str(new_year) + " ")
            answer = self.controller.ask_question(message, "Warning")
            if not answer:
                return
            else:
                sql = ("SELECT " + self.schema_name + ".create_price('" + str(new_year) + "','" + str(old_year) + "')")
                self.controller.execute_sql(sql)


        # Close perevious dialog
        self.close_dialog(self.dlg_new_prices.dialog)

        # Set dialog and signals
        dlg_prices_management = WidgetManager(PriceManagement())
        self.load_settings(dlg_prices_management.dialog)
        dlg_prices_management.dialog.btn_close.clicked.connect(partial(self.close_dialog, dlg_prices_management.dialog))
        dlg_prices_management.dialog.rejected.connect(partial(self.close_dialog, dlg_prices_management.dialog))
        # Populate QTableView
        table_view = 'v_edit_price'
        self.fill_table_prices(dlg_prices_management.dialog.tbl_price_list, table_view, new_year, set_edit_triggers=QTableView.DoubleClicked)
        self.set_table_columns(dlg_prices_management.dialog.tbl_price_list, table_view, 'basic_cat_price')
        dlg_prices_management.dialog.exec_()


    def fill_table_prices(self, qtable, table_view, new_year, set_edit_triggers=QTableView.NoEditTriggers):
        """ Set a model with selected filter.
        Attach that model to selected table
        @setEditStrategy:
            0: OnFieldChange
            1: OnRowChange
            2: OnManualSubmit
        """

        # Set model
        model = QSqlTableModel()
        model.setTable(self.schema_name + "." + table_view)
        model.setEditStrategy(QSqlTableModel.OnFieldChange)
        model.setSort(2, 0)
        model.select()

        qtable.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())
        # Attach model to table view
        expr = "year = '"+new_year+"'"
        qtable.setModel(model)
        qtable.model().setFilter(expr)




    def main_tree_manage(self):
        """ Button 01: Tree selector """

        dlg_tree_manage = WidgetManager(TreeManage())
        #dlg_tree_manage.dialog.setFixedSize(300, 170)
        self.load_settings(dlg_tree_manage.dialog)

        validator = QIntValidator(1, 9999999)
        dlg_tree_manage.dialog.txt_year.setValidator(validator)
        table_name = 'planning'
        field_id = 'plan_year'
        field_name = 'plan_year'
        self.populate_cmb_years(dlg_tree_manage, table_name,  field_id, field_name, dlg_tree_manage.dialog.cbx_years)


      
        #TODO borrar estas tres lineas
        # now = datetime.datetime.now()
        # dlg_tree_manage.setWidgetText(dlg_tree_manage.dialog.txt_year, str(now.year + 1))
        # dlg_tree_manage.setChecked(dlg_tree_manage.dialog.chk_year, True)
        # dlg_tree_manage.set_combo_itemData(dlg_tree_manage.dialog.cbx_years, str(now.year + 1), 1)


        dlg_tree_manage.dialog.rejected.connect(partial(self.close_dialog, dlg_tree_manage.dialog))
        dlg_tree_manage.dialog.btn_cancel.clicked.connect(partial(self.close_dialog, dlg_tree_manage.dialog))
        dlg_tree_manage.dialog.btn_accept.clicked.connect(partial(self.get_year, dlg_tree_manage))

        dlg_tree_manage.dialog.exec_()


    def populate_cmb_years(self, widget_manager, table_name, field_id, field_name, combo, reverse=False):
        """
        sql = ("SELECT current_database()")
        rows = self.controller.get_rows(sql)
        self.controller.log_info(str(rows))
        """
        sql = ("SELECT DISTINCT(" + str(field_id) + ")::text, " + str(field_name) + "::text FROM "+self.schema_name+"."+table_name + ""
               " WHERE " + str(field_name) + "::text != ''")
        rows = self.controller.get_rows(sql)
        if rows is None:
            return

        widget_manager.set_item_data(combo, rows, 1, reverse)


    def get_year(self, wm):
        update = False
        self.selected_year = None

        if wm.dialog.txt_year.text() != '':
            self.plan_year = wm.getWidgetText(wm.dialog.txt_year)
            sql = ("SELECT year from "+self.schema_name+".v_plan_mu "
                   " WHERE year='"+self.plan_year+"'")
            row = self.controller.get_row(sql)
            if row is None:
                message = "No hi ha preus per aquest any"
                self.controller.show_warning(message)
                return None

            if wm.isChecked(wm.dialog.chk_year) and wm.get_item_data(wm.dialog.cbx_years, 0) != -1:
                self.selected_year = wm.get_item_data(wm.dialog.cbx_years, 0)
                sql = ("SELECT DISTINCT(plan_year) FROM " + self.schema_name + ".planning"
                       " WHERE plan_year ='" + str(self.selected_year) + "'")
                row = self.controller.get_row(sql)
                if row:
                    update = True
            else:
                self.selected_year = self.plan_year
            self.close_dialog(wm.dialog)
            self.tree_selector(update)

        else:
            message = "Any recuperat es obligatori"
            self.controller.show_warning(message)
            return None


    def tree_selector(self, update=False):

        dlg_selector = WidgetManager(TreeSelector())
        self.load_settings(dlg_selector.dialog)

        dlg_selector.dialog.setWindowTitle("Tree selector")
        dlg_selector.dialog.lbl_year.setText(self.plan_year)

        tableleft = 'v_plan_mu'
        tableright = 'planning'
        table_view = 'v_plan_mu_year'
        id_table_left = 'mu_id'
        id_table_right = 'mu_id'

        dlg_selector.dialog.all_rows.setSelectionBehavior(QAbstractItemView.SelectRows)
        dlg_selector.dialog.selected_rows.setSelectionBehavior(QAbstractItemView.SelectRows)
        #dlg_selector.all_rows.horizontalHeader().setStyleSheet("QHeaderView { font-size: 10pt; }")

        sql = ("SELECT DISTINCT(work_id), work_name FROM "+self.schema_name + "." + tableleft)
        rows = self.controller.get_rows(sql)
        dlg_selector.set_item_data(dlg_selector.dialog.cmb_poda_type, rows, 1)

        # CheckBox
        dlg_selector.dialog.chk_permanent.stateChanged.connect(partial(self.force_chk_current, dlg_selector.dialog))

        # Button selec
        dlg_selector.dialog.btn_select.clicked.connect(partial(self.rows_selector, dlg_selector, id_table_left, tableright, id_table_right, tableleft, table_view))
        dlg_selector.dialog.all_rows.doubleClicked.connect(partial(self.rows_selector, dlg_selector, id_table_left, tableright, id_table_right, tableleft, table_view))

        # Button unselect
        dlg_selector.dialog.btn_unselect.clicked.connect(partial(self.rows_unselector, dlg_selector, tableright, id_table_right, tableleft, table_view))
        dlg_selector.dialog.selected_rows.doubleClicked.connect(partial(self.rows_unselector, dlg_selector, tableright, id_table_right, tableleft, table_view))

        # Populate QTableView
        self.fill_table(dlg_selector, table_view, set_edit_triggers=QTableView.NoEditTriggers, update=True)
        if update:
            self.insert_into_planning(tableright)

        # Need fill table before set table columns, and need re-fill table for upgrade fields
        self.set_table_columns(dlg_selector.dialog.selected_rows, table_view, 'basic_year_right')
        self.fill_table(dlg_selector, table_view, set_edit_triggers=QTableView.NoEditTriggers)

        self.fill_main_table(dlg_selector, tableleft)
        self.set_table_columns(dlg_selector.dialog.all_rows, tableleft, 'basic_year_left')

        # Filter field
        dlg_selector.dialog.txt_search.textChanged.connect(partial(self.fill_main_table, dlg_selector, tableleft, set_edit_triggers=QTableView.NoEditTriggers))
        dlg_selector.dialog.txt_selected_filter.textChanged.connect(partial(self.fill_table, dlg_selector, table_view, set_edit_triggers=QTableView.NoEditTriggers))

        dlg_selector.dialog.btn_close.clicked.connect(partial(self.close_dialog, dlg_selector.dialog))
        dlg_selector.dialog.btn_close.clicked.connect(partial(self.close_dialog, dlg_selector.dialog))
        dlg_selector.dialog.rejected.connect(partial(self.close_dialog, dlg_selector))

        dlg_selector.dialog.exec_()


    def force_chk_current(self, dialog):
        if dialog.chk_permanent.isChecked():
            dialog.chk_current.setChecked(True)


    def fill_main_table(self, wm, table_name, set_edit_triggers=QTableView.NoEditTriggers):
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
        model.setSort(2, 0)
        model.select()

        wm.dialog.all_rows.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())

        # Get all ids from Qtable selected_rows
        id_all_selected_rows = self.select_all_rows(wm.dialog.selected_rows, 'mu_id')

        # Convert id_all_selected_rows to string
        ids = "0, "
        for x in range(0, len(id_all_selected_rows)):
            ids += str(id_all_selected_rows[x]) + ", "
        ids = ids[:-2] + ""

        # Attach model to table view
        expr = " mu_name ILIKE '%" + wm.dialog.txt_search.text() + "%'"
        expr += " AND mu_id NOT IN ("+ids+")"
        expr += " AND year::text ILIKE '%" + str(self.plan_year) + "%'"
        wm.dialog.all_rows.setModel(model)
        wm.dialog.all_rows.model().setFilter(expr)


    def fill_table(self, wm,  table_view, set_edit_triggers=QTableView.NoEditTriggers, update=False):
        """ Set a model with selected filter.
        Attach that model to selected table
        @setEditStrategy:
            0: OnFieldChange
            1: OnRowChange
            2: OnManualSubmit
        """

        # Set model
        model = QSqlTableModel()
        model.setTable(self.schema_name + "." + table_view)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setSort(2, 0)
        model.select()
        wm.dialog.selected_rows.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())

        # Create expresion
        expr = " mu_name ILIKE '%" + wm.dialog.txt_selected_filter.text() + "%'"
        if self.selected_year is not None:
            expr += " AND plan_year ='" + str(self.plan_year) + "'"
            if update:
                expr += " OR plan_year ='" + str(self.selected_year) + "'"

        # Attach model to table or view
        wm.dialog.selected_rows.setModel(model)
        wm.dialog.selected_rows.model().setFilter(expr)

        # Set year to plan to all rows in list
        for x in range(0, model.rowCount()):
            i = int(wm.dialog.selected_rows.model().fieldIndex('plan_year'))
            index = wm.dialog.selected_rows.model().index(x, i)
            model.setData(index, self.plan_year)
        self.calculate_total_price(wm, self.plan_year)


    def calculate_total_price(self, wm, year):
        """ Update QLabel @lbl_total_price with sum of all price in @select_rows """
        selected_list = wm.dialog.selected_rows.model()
        if selected_list is None:
            return
        total = 0
        # Sum all price
        for x in range(0, selected_list.rowCount()):
            if str(wm.dialog.selected_rows.model().record(x).value('plan_year')) == str(year):
                if str(wm.dialog.selected_rows.model().record(x).value('price')) != 'NULL':
                    total += float(wm.dialog.selected_rows.model().record(x).value('price'))
        wm.setText(wm.dialog.lbl_total_price, str(total))


    def insert_into_planning(self, tableright):
        sql = ("SELECT * FROM " + self.schema_name+"."+tableright + " "
               " WHERE plan_year::text ='"+str(self.selected_year) + "'")
        rows = self.controller.get_rows(sql)

        if rows:
            for row in rows:
                insert_values = ""
                function_values = ""
                if row['mu_id'] is not None:
                    insert_values += "'" + str(row['mu_id']) + "', "
                    function_values += "'" + str(row['mu_id']) + "', "
                else:
                    insert_values += 'null, '
                if row['work_id'] is not None:
                    insert_values += "'" + str(row['work_id']) + "', "
                    function_values += "'" + str(row['work_id']) + "', "
                else:
                    insert_values += 'null, '
                if str(row['price']) != 'NULL':
                    insert_values += "'" + str(row['price']) + "', "
                else:
                    insert_values += 'null, '
                insert_values += "'" + self.plan_year + "', "
                insert_values = insert_values[:len(insert_values) - 2]
                function_values += "" + self.plan_year + ", "
                function_values = function_values[:len(function_values) - 2]
                # Check if mul_id and year_ already exists in planning
                sql = ("SELECT  mu_id  "
                       " FROM " + self.schema_name + "." + tableright + ""
                       " WHERE mu_id = '" + str(row['mu_id']) + "'"
                       " AND plan_year ='" + str(self.plan_year) + "'")
                rowx = self.controller.get_row(sql)

                if rowx is None:
                    #     # Put a new row in QTableView
                    #     # dialog.selected_rows.model().insertRow(dialog.selected_rows.verticalHeader().count())
                    #
                    sql = ("INSERT INTO " + self.schema_name + "." + tableright + ""
                           " (mu_id,  work_id,  price, plan_year) "
                           " VALUES (" + insert_values + ")")
                    self.controller.execute_sql(sql)
                    sql = ("SELECT " + self.schema_name + ".set_plan_price(" + function_values + ")")
                    self.controller.execute_sql(sql)


    def rows_selector(self, wm, id_table_left, tableright, id_table_right, tableleft, table_view):
        """ Copy the selected lines in the qtable_all_rows and in the table """
        left_selected_list = wm.dialog.all_rows.selectionModel().selectedRows()
        if len(left_selected_list) == 0:
            message = "Cap registre seleccionat"
            self.controller.show_warning(message)
            return
        # Get all selected ids
        field_list = []
        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            id_ = wm.dialog.all_rows.model().record(row).value(id_table_left)
            field_list.append(id_)

        # Select all rows and get all id
        self.select_all_rows(wm.dialog.selected_rows, id_table_right)
        if wm.isChecked(wm.dialog.chk_current):
            current_poda_type = wm.get_item_data(wm.dialog.cmb_poda_type, 0)
            current_poda_name = wm.get_item_data(wm.dialog.cmb_poda_type, 1)
            if current_poda_type is None:
                message = "No heu seleccionat cap poda"
                self.controller.show_warning(message)
                return
        if wm.isChecked(wm.dialog.chk_permanent):
            for i in range(0, len(left_selected_list)):
                row = left_selected_list[i].row()
                sql = ("UPDATE " + self.schema_name + ".cat_mu "
                       " SET work_id ='"+str(current_poda_type)+"' "
                       " WHERE id ='"+str(wm.dialog.all_rows.model().record(row).value('mu_id'))+"'")
                self.controller.execute_sql(sql)

        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            values = ""
            function_values = ""
            if wm.dialog.all_rows.model().record(row).value('mu_id') is not None:
                values += "'" + str(wm.dialog.all_rows.model().record(row).value('mu_id')) + "', "
                function_values += "'" + str(wm.dialog.all_rows.model().record(row).value('mu_id')) + "', "
            else:
                values += 'null, '

            if wm.dialog.all_rows.model().record(row).value('work_id') is not None:
                if wm.isChecked(wm.dialog.chk_current):
                    values += "'" + str(current_poda_type) + "', "
                    function_values += "'" + str(current_poda_type) + "', "
                else:
                    values += "'" + str(wm.dialog.all_rows.model().record(row).value('work_id')) + "', "
                    function_values += "'" + str(wm.dialog.all_rows.model().record(row).value('work_id')) + "', "
            else:
                values += 'null, '

            values += "'"+self.plan_year+"', "
            values = values[:len(values) - 2]
            function_values += "'"+self.plan_year+"', "
            function_values = function_values[:len(function_values) - 2]

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
                       " (mu_id,  work_id,  plan_year) "
                       " VALUES (" + values + ")")
                self.controller.execute_sql(sql)
                sql = ("SELECT " + self.schema_name + ".set_plan_price(" + function_values + ")")
                self.controller.execute_sql(sql)

        # Refresh
        self.fill_table(wm, table_view, set_edit_triggers=QTableView.NoEditTriggers)
        self.fill_main_table(wm, tableleft)


    def rows_unselector(self, wm, tableright, field_id_right, tableleft, table_view):

        query = ("DELETE FROM " + self.schema_name + "." + tableright + ""
                 " WHERE  plan_year='" + self.plan_year + "' AND " + field_id_right + " = ")
        selected_list = wm.dialog.selected_rows.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Cap registre seleccionat"
            self.controller.show_warning(message)
            return
        field_list = []
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            id_ = str(wm.dialog.selected_rows.model().record(row).value(field_id_right))
            field_list.append(id_)
        for i in range(0, len(field_list)):
            sql = (query + "'" + str(field_list[i]) + "'")
            self.controller.execute_sql(sql)
        # Refresh model with selected filter
        self.fill_table(wm, table_view, set_edit_triggers=QTableView.NoEditTriggers)
        self.fill_main_table(wm, tableleft)


    def basic_month_manage(self):
        """ Button 02: Planned year manage """
        month_manage = WidgetManager(MonthManage())

        self.load_settings(month_manage.dialog)
        month_manage.dialog.setWindowTitle("Planificador mensual")
        # TODO borrar esta linea
        month_manage.setWidgetText(month_manage.dialog.txt_plan_code, "")
        table_name = 'planning'
        field_id = 'plan_year'
        field_name = 'plan_year'
        self.set_completer_object(table_name, month_manage.dialog.txt_plan_code, 'plan_code')
        self.populate_cmb_years(month_manage, table_name, field_id, field_name, month_manage.dialog.cbx_years, reverse=True)

        month_manage.dialog.rejected.connect(partial(self.close_dialog, month_manage.dialog))
        month_manage.dialog.btn_cancel.clicked.connect(partial(self.close_dialog, month_manage.dialog))
        month_manage.dialog.btn_accept.clicked.connect(partial(self.get_planned_year, month_manage))

        month_manage.dialog.exec_()


    def get_planned_year(self, wm):

        if str(wm.getWidgetText(wm.dialog.txt_plan_code)) == 'null':
            message = "El camp text a no pot estar vuit"
            self.controller.show_warning(message)
            return

        self.plan_code = str(wm.getWidgetText(wm.dialog.txt_plan_code))
        self.planned_year = wm.get_item_data(wm.dialog.cbx_years, 0)
        
        if self.planned_year == -1:
            message = "No hi ha cap any planificat"
            self.controller.show_warning(message)
            return
        self.close_dialog(wm.dialog)
        self.month_selector()


    def month_selector(self):
        month_selector = WidgetManager(MonthSelector())

        
        self.load_settings(month_selector.dialog)
        month_selector.dialog.all_rows.setSelectionBehavior(QAbstractItemView.SelectRows)
        month_selector.dialog.selected_rows.setSelectionBehavior(QAbstractItemView.SelectRows)
        month_selector.dialog.setWindowTitle("Planificador mensual")

        # Set label with selected text from previus dialog
        month_selector.dialog.lbl_plan_code.setText(self.plan_code)
        month_selector.dialog.lbl_year.setText(str(self.planned_year))
        year_to_set = 0
        if self.planned_year > int(QDate.currentDate().year()):
            year_to_set = (int(self.planned_year) - int(QDate.currentDate().year()))

        # Set default dates to actual day (today) and actual day +1 (tomorrow)
        month_selector.setCalendarDate(month_selector.dialog.date_inici, QDate.currentDate().addYears(year_to_set), True)
        # Get date as string
        data_fi = month_selector.getCalendarDate(month_selector.dialog.date_inici)
        # Convert string date to QDate
        data_fi = QDate.fromString(data_fi, 'yyyy/MM/dd')
        # Set calendar with date_fi as QDate + 1 day
        month_selector.setCalendarDate(month_selector.dialog.date_fi, data_fi.addDays(1))


        view_name = 'v_plan_mu_year'
        tableleft = 'planning'
        id_table_left = 'mu_id'

        # Left QTableView
        expr = " AND (plan_code != '" + str(self.plan_code) + "'"
        expr += " OR plan_code is NULL)"
        self.fill_table_planned_month(month_selector.dialog.all_rows, month_selector.dialog.txt_search, view_name, expr)
        month_selector.dialog.txt_search.textChanged.connect(partial(self.fill_table_planned_month, month_selector.dialog.all_rows, month_selector.dialog.txt_search, view_name, expr, QTableView.NoEditTriggers))
        month_selector.dialog.btn_select.clicked.connect(partial(self.month_selector_row, month_selector, id_table_left, tableleft, view_name))
        self.set_table_columns(month_selector.dialog.all_rows, view_name, 'basic_month_left')

        # Right QTableView
        expr = " AND plan_code = '" + str(self.plan_code) + "'"
        self.fill_table_planned_month(month_selector.dialog.selected_rows, month_selector.dialog.txt_selected_filter, view_name, expr)
        month_selector.dialog.txt_selected_filter.textChanged.connect(partial(self.fill_table_planned_month, month_selector.dialog.selected_rows, month_selector.dialog.txt_selected_filter, view_name, expr, QTableView.NoEditTriggers))
        month_selector.dialog.btn_unselect.clicked.connect(partial(self.month_unselector_row, month_selector, id_table_left, tableleft, view_name))
        self.set_table_columns(month_selector.dialog.selected_rows, view_name, 'basic_month_right')

        self.calculate_total_price(month_selector, self.planned_year)

        month_selector.dialog.btn_close.clicked.connect(partial(self.close_dialog, month_selector.dialog))
        month_selector.dialog.rejected.connect(partial(self.close_dialog, month_selector.dialog))

        month_selector.dialog.exec_()


    def month_selector_row(self, wm, id_table_left, tableleft, view_name):
        left_selected_list = wm.dialog.all_rows.selectionModel().selectedRows()
        if len(left_selected_list) == 0:
            message = "Cap registre seleccionat"
            self.controller.show_warning(message)
            return

        # Get all selected ids
        field_list = []
        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            id_ = wm.dialog.all_rows.model().record(row).value(id_table_left)
            field_list.append(id_)

        # Get dates
        plan_month_start = wm.getCalendarDate(wm.dialog.date_inici)
        plan_month_end = wm.getCalendarDate(wm.dialog.date_fi)

        # Get year from string
        calendar_year = QDate.fromString(plan_month_start, 'yyyy/MM/dd').year()
        if int(calendar_year) < int(self.planned_year):
            self.controller.show_details(detail_text="La data d'inici no pot ser anterior a 'Any planificacio'")
            return

        if plan_month_start > plan_month_end:
            self.controller.show_details(detail_text="La data d'inici no pot ser posterior a la data final")
            return

        # Update values
        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            sql = ("UPDATE " + self.schema_name + "." + tableleft + " "
                   " SET plan_code ='" + str(self.plan_code) + "', "
                   " plan_month_start = '"+plan_month_start+"', "
                   " plan_month_end = '"+plan_month_end+"' "
                   " WHERE id='" + str(wm.dialog.all_rows.model().record(row).value('id')) + "'"
                   " AND mu_id ='" + str(wm.dialog.all_rows.model().record(row).value('mu_id')) + "'"
                   " AND plan_year = '"+self.planned_year+"'")
            self.controller.execute_sql(sql)

        # Refresh QTableViews and recalculate price
        expr = " AND (plan_code != '" + str(self.plan_code) + "'"
        expr += " OR plan_code is NULL)"
        self.fill_table_planned_month(wm.dialog.all_rows, wm.dialog.txt_search, view_name, expr)
        expr = " AND plan_code = '" + str(self.plan_code) + "'"
        self.fill_table_planned_month(wm.dialog.selected_rows, wm.dialog.txt_selected_filter, view_name, expr)
        self.calculate_total_price(wm, self.planned_year)


    def month_unselector_row(self, wm, id_table_left, tableleft, view_name):
        left_selected_list = wm.dialog.selected_rows.selectionModel().selectedRows()
        if len(left_selected_list) == 0:
            message = "Cap registre seleccionat"
            self.controller.show_warning(message)
            return
        # Get all selected ids
        field_list = []
        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            id_ = wm.dialog.selected_rows.model().record(row).value(id_table_left)
            field_list.append(id_)

        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            sql = ("UPDATE " + self.schema_name + "." + tableleft + " "
                   " SET plan_code = null, "
                   " plan_month_start = null, "
                   " plan_month_end = null "
                   " WHERE mu_id ='" + str(wm.dialog.selected_rows.model().record(row).value('mu_id')) + "'"
                   " AND plan_year = '"+self.planned_year+"'")
            self.controller.execute_sql(sql)

        # Refresh QTableViews and recalculate price
        expr = " AND (plan_code != '" + str(self.plan_code) + "'"
        expr += " OR plan_code is NULL)"
        self.fill_table_planned_month(wm.dialog.all_rows, wm.dialog.txt_search, view_name, expr)
        expr = " AND plan_code = '" + str(self.plan_code) + "'"
        self.fill_table_planned_month(wm.dialog.selected_rows, wm.dialog.txt_selected_filter, view_name, expr)
        self.calculate_total_price(wm, self.planned_year)



    def fill_table_planned_month(self, qtable, txt_filter, tableright, expression=None, set_edit_triggers=QTableView.NoEditTriggers):

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
        model.setSort(2, 0)
        model.select()
        qtable.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())

        # Create expresion
        expr = " mu_name ILIKE '%" + str(txt_filter.text()) + "%' "
        expr += " AND plan_year = '" + str(self.planned_year) + "' "
        if expression is not None:
            expr += expression

        qtable.setModel(model)
        qtable.model().setFilter(expr)


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


    def add_visit(self):
        """ Button 04: Add visit """
        self.manage_visit.manage_visit()