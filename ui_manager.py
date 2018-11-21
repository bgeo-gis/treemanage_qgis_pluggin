# -*- coding: utf-8 -*-
from PyQt4 import QtGui, uic
import os


def get_ui_class(ui_file_name):
    """ Get UI Python class from @ui_file_name """

    # Folder that contains UI files
    ui_folder_path = os.path.dirname(__file__) + os.sep + 'ui'
    ui_file_path = os.path.abspath(os.path.join(ui_folder_path, ui_file_name))
    return uic.loadUiType(ui_file_path)[0]




FORM_CLASS = get_ui_class('add_visit.ui')
class AddVisit(QtGui.QDialog, FORM_CLASS):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)

FORM_CLASS = get_ui_class('event_standard.ui')
class EventStandard(QtGui.QDialog, FORM_CLASS):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)

FORM_CLASS = get_ui_class('planning_unit.ui')
class PlaningUnit(QtGui.QDialog, FORM_CLASS):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)