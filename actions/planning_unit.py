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

from qgis.core import QgsPoint, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.gui import QgsMapToolEmitPoint, QgsDateTimeEdit

import json
import os
import re
import subprocess
import sys
import webbrowser
from collections import OrderedDict
from functools import partial

from _utils import widget_manager as wm
from tree_manage.actions.parent import ParentAction
from tree_manage.ui_manager import PlaningUnit

class PlanningUnit(ParentAction):
    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class constructor """
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)
        self.iface = iface
        self.settings = settings
        self.controller = controller
        self.plugin_dir = plugin_dir

    def open_form(self):
        dlg_unit = PlaningUnit()
        self.load_settings(dlg_unit)
        self.set_icon(dlg_unit.btn_insert, "111")
        self.set_icon(dlg_unit.btn_delete, "112")
        self.set_icon(dlg_unit.btn_snapping, "137")

        validator = QIntValidator(1, 9999999)
        dlg_unit.txt_times.setValidator(validator)

        wm.set_qtv_config(dlg_unit.tbl_unit)

        sql = ("SELECT id, name FROM " + self.schema_name + ".cat_campaign")
        rows = self.controller.get_rows(sql, log_sql=True)
        wm.set_item_data(dlg_unit.cmb_campaign, rows, 1)
        sql = ("SELECT id, name FROM " + self.schema_name + ".cat_work")
        rows = self.controller.get_rows(sql, log_sql=True)
        wm.set_item_data(dlg_unit.cmb_work, rows, 1)

        table_name = "v_ui_planning_unit"
        self.update_table(dlg_unit.tbl_unit, table_name, dlg_unit.cmb_campaign)

        dlg_unit.cmb_campaign.currentIndexChanged.connect(
            partial(self.update_table, dlg_unit.tbl_unit, table_name, dlg_unit.cmb_campaign))

        dlg_unit.btn_close.clicked.connect(partial(self.close_dialog, dlg_unit))
        dlg_unit.exec_()

    def update_table(self, qtable, table_name, combo):
        id = wm.get_item_data(combo, 0)
        expr_filter = "campaign_id = " + str(id)
        self.fill_table(qtable, table_name, expr_filter=expr_filter)



