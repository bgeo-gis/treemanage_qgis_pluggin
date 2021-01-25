# -*- coding: utf-8 -*-
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
import os


def get_ui_class(ui_file_name):
    """ Get UI Python class from @ui_file_name """

    # Folder that contains UI files
    ui_folder_path = os.path.dirname(__file__) + os.sep + 'ui'
    ui_file_path = os.path.abspath(os.path.join(ui_folder_path, ui_file_name))
    return uic.loadUiType(ui_file_path)[0]


FORM_CLASS = get_ui_class('add_visit.ui')
class AddVisit(QDialog, FORM_CLASS):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)


FORM_CLASS = get_ui_class('event_standard.ui')
class EventStandard(QDialog, FORM_CLASS):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)


FORM_CLASS = get_ui_class('planning_unit.ui')
class PlaningUnit(QDialog, FORM_CLASS):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)

