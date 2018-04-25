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

from ..ui.tree_manage import TreeManage
from ..ui.multirow_selector import Multirow_selector
import utils

from functools import partial

plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(plugin_path)
class Month():
    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'basic' """
        self.minor_version = "3.0"
        #ParentAction.__init__(self, iface, settings, controller, plugin_dir)
        self.selected_year = None
        self.plan_year = None
    def set_project_type(self, project_type):
        self.project_type = project_type
    # def set_month(self, month):
    #     self.month = month
    def manage_months(self):
        """ Button 01: Tree selector """
        self.controller.log_info(str("TEST MONTH"))