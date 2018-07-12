# -*- coding: utf-8 -*-
"""
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from tree_manage.dao.table import Table, GenericDescriptor


class OmVisitXNode(Table):
    """ Class to serialize table 'om_visit_x_node' """

    id = GenericDescriptor(-1)
    visit_id = GenericDescriptor(None)
    node_id = GenericDescriptor(None)
    # is_last = GenericDescriptor(None)

    def __init__(self, controller):
        """ Class constructor """        
        Table.__init__(self, controller, 'om_visit_x_node', 'id')
        
