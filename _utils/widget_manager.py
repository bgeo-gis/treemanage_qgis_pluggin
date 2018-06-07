"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
""" Module with utility functions to interact with dialog and its widgets """
from qgis.gui import QgsDateTimeEdit
from PyQt4.QtGui import QLineEdit, QComboBox, QWidget, QPixmap, QDoubleSpinBox, QCheckBox, QLabel, QTextEdit, QDateEdit, QSpinBox, QTimeEdit
from PyQt4.QtGui import QAbstractItemView, QCompleter, QSortFilterProxyModel, QStringListModel, QDateTimeEdit
from PyQt4.Qt import QDate, QDateTime
from PyQt4.QtCore import QTime

from functools import partial
import inspect
import os
import sys
import operator
class WidgetManager(object):
    def __init__(self, dialog):
        self.setDialog(dialog)

    if 'nt' in sys.builtin_module_names:
        import _winreg

    def setDialog(self, p_dialog):
        self.dialog = p_dialog

    def getDialog(self):
        return self.dialog

    def get_item_data(self, widget, index=0):
        """ Get item data of current index of the @widget """

        code = -1
        if type(widget) is str or type(widget) is unicode:
            widget = self.dialog.findChild(QWidget, widget)
        if widget:
            if type(widget) is QComboBox:
                current_index = widget.currentIndex()
                elem = widget.itemData(current_index)
                code = elem[index]

        return code

    def getWidget(self, widget):

        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        return widget

    def set_combo_itemData(self, combo, value, item1):
        """ Set text to combobox populate with more than 1 item for row
            @item1: element to compare
            @item2: element to show
        """
        for i in range(0, combo.count()):
            elem = combo.itemData(i)
            if value == str(elem[item1]):
                combo.setCurrentIndex(i)

    def set_item_data(self, combo, rows, index_to_show=0, combo_clear=True):
        """ Populate @combo with list @rows and show field @index_to_show """

        records = []
        if rows is None:
            return
        for row in rows:
            elem = [row[0], row[1]]
            records.append(elem)

        combo.blockSignals(True)
        if combo_clear:
            combo.clear()

        records_sorted = sorted(records, key=operator.itemgetter(1))
        for record in records_sorted:
            combo.addItem(record[index_to_show], record)
            combo.blockSignals(False)

    def getWidgetText(self, widget, add_quote=False, return_string_null=True):

        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        if not widget:
            return None
        text = None
        if type(widget) is QLineEdit or type(widget) is QTextEdit or type(widget) is QDoubleSpinBox:
            text = self.getText(widget, return_string_null)
        elif type(widget) is QComboBox:
            text = self.getSelectedItem(widget, return_string_null)
        if add_quote and text <> "null":
            text = "'" + text + "'"
        return text


    def getText(self, widget, return_string_null=True):

        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        if widget:
            if type(widget) is QLineEdit or type(widget) is QDoubleSpinBox or type(widget) is QSpinBox:
                text = widget.text()
            elif type(widget) is QTextEdit:
                text = widget.toPlainText()
            if text:
                elem_text = text
            elif return_string_null:
                elem_text = "null"
            else:
                elem_text = ""
        else:
            if return_string_null:
                elem_text = "null"
            else:
                elem_text = ""
        return elem_text


    def setWidgetText(self, widget, text):

        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        if not widget:
            return
        if type(widget) is QLineEdit or type(widget) is QTextEdit or type(widget) is QTimeEdit:
            self.setText(widget, text)
        elif type(widget) is QDoubleSpinBox:
            self.setText(widget, text)
        elif type(widget) is QComboBox:
            self.setSelectedItem(widget, text)


    def setText(self, widget, text):

        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        if not widget:
            return

        value = unicode(text)
        if type(widget) is QLineEdit or type(widget) is QTextEdit or type(widget) is QLabel:
            if value == 'None':
                value = ""
            widget.setText(value)
        elif type(widget) is QDoubleSpinBox or type(widget) is QSpinBox:
            if value == 'None':
                value = 0
            widget.setValue(float(value))


    def getCalendarDate(self, widget, date_format="yyyy/MM/dd", datetime_format="yyyy/MM/dd hh:mm:ss"):

        date = None
        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        if not widget:
            return
        if type(widget) is QDateEdit:
            date = widget.date().toString(date_format)
        elif type(widget) is QDateTimeEdit:
            date = widget.dateTime().toString(datetime_format)
        elif type(widget) is QgsDateTimeEdit and widget.displayFormat() == 'dd/MM/yyyy':
            date = widget.dateTime().toString(date_format)
        elif type(widget) is QgsDateTimeEdit and widget.displayFormat() == 'dd/MM/yyyy hh:mm:ss':
            date = widget.dateTime().toString(datetime_format)

        return date


    def setCalendarDate(self, widget, date, default_current_date=True):

        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        if not widget:
            return
        if type(widget) is QDateEdit \
                or (type(widget) is QgsDateTimeEdit and widget.displayFormat() == 'dd/MM/yyyy'):
            if date is None:
                if default_current_date:
                    date = QDate.currentDate()
                else:
                    date = QDate.fromString('01/01/2000', 'dd/MM/yyyy')
            widget.setDate(date)
        elif type(widget) is QDateTimeEdit \
                or (type(widget) is QgsDateTimeEdit and widget.displayFormat() == 'dd/MM/yyyy hh:mm:ss'):
            if date is None:
                date = QDateTime.currentDateTime()
            widget.setDateTime(date)


    def setTimeEdit(self, widget, time):

        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        if not widget:
            return
        if type(widget) is QTimeEdit:
            if time is None:
                time = QTime(00, 00, 00)
            widget.setTime(time)


    def setSelectedItem(self, widget, text):

        if type(widget) is str:
            widget = self.dialog.findChild(QComboBox, widget)
        if widget:
            index = widget.findText(text)
            if index == -1:
                index = 0
            widget.setCurrentIndex(index)


    def isChecked(self, widget):

        if type(widget) is str:
            widget = self.dialog.findChild(QCheckBox, widget)
        checked = False
        if widget:
            checked = widget.isChecked()
        return checked

    def setChecked(self, widget, checked=True):

        if type(widget) is str:
            widget = self.dialog.findChild(QWidget, widget)
        if not widget:
            return
        if type(widget) is QCheckBox:
            widget.setChecked(bool(checked))


    def getSelectedItem(self, widget, return_string_null=True):

        if type(widget) is str:
            widget = self.dialog.findChild(QComboBox, widget)
        if return_string_null:
            widget_text = "null"
        else:
            widget_text = ""
        if widget:
            if widget.currentText():
                widget_text = widget.currentText()
        return widget_text

    def fillComboBox(self, widget, rows, allow_nulls=True, clear_combo=True):

        if rows is None:
            return
        if type(widget) is str:
            widget = self.dialog.findChild(QComboBox, widget)
        if clear_combo:
            widget.clear()
        if allow_nulls:
            widget.addItem('')
        for row in rows:
            if len(row) > 1:
                elem = row[0][0]
                userData = row[1]
            else:
                elem = row[0]
                userData = None
            if elem:
                try:
                    if isinstance(elem, int) or isinstance(elem, float):
                        widget.addItem(str(elem), userData)
                    else:
                        widget.addItem(elem, userData)
                except:
                    widget.addItem(str(elem), userData)