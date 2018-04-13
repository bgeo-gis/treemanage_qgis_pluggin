"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
import os
import sys

plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(plugin_path)
import utils

from ui.multirow_selector import Multirow_selector         
from parent import ParentAction


class Basic(ParentAction):

    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'basic' """
        self.minor_version = "3.0"
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)

        

    def set_tree_manage(self, tree_manage):
        self.tree_manage = tree_manage
        
        
    def set_project_type(self, project_type):
        self.project_type = project_type


    def tree_selector(self):
        """ Button 01: Tree selector """
                
        self.dlg = Multirow_selector()
        utils.setDialog(self.dlg)
        self.dlg.btn_ok.pressed.connect(self.close_dialog)
        self.dlg.setWindowTitle("Tree selector")
        tableleft = "exploitation"
        tableright = "selector_expl"
        field_id_left = "expl_id"
        field_id_right = "expl_id"
        self.multi_row_selector(self.dlg, tableleft, tableright, field_id_left, field_id_right)
        self.dlg.exec_()



