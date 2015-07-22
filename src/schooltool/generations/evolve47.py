#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2015 Shuttleworth Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Upgrade SchoolTool to generation 47.

Add new contact relationship states
"""

from zope.app.generations.utility import getRootFolder
from zope.component.hooks import getSite, setSite

from schooltool.app.interfaces import IRelationshipStateContainer
from schooltool.contact.contact import ACTIVE
from schooltool.contact.contact import PARENT
from schooltool.common import SchoolToolMessage as _


def evolve(context):
    root = getRootFolder(context)
    old_site = getSite()
    app = root
    setSite(app)
    container = IRelationshipStateContainer(app)
    if 'contact-relationship' in container:
        target = container['contact-relationship']
        states = target.states
        order = list(states.keys())
        added = []
        if 'tp' not in states:
            target.add(_('Father'), ACTIVE+PARENT, 'tp')
            added.append('tp')
        if 'mp' not in states:
            target.add(_('Mother'), ACTIVE+PARENT, 'mp')
            added.append('mp')
        if added:
            idx = order.index('a') + 1
            for i, code in enumerate(added):
                order.insert(idx + i, code)
            states.updateOrder(order)
    setSite(old_site)
