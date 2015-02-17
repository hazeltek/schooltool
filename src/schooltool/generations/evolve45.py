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
Upgrade SchoolTool to generation 45.

Update teacher attendance states
"""

from zope.app.generations.utility import getRootFolder
from zope.component.hooks import getSite, setSite

from schooltool.app.interfaces import IRelationshipStateContainer
from schooltool.app.states import IGNORED
from schooltool.app.states import INACTIVE
from schooltool.app.states import ACTIVE
from schooltool.common import SchoolToolMessage as _


def evolve(context):
    root = getRootFolder(context)
    old_site = getSite()
    app = root
    setSite(app)
    container = IRelationshipStateContainer(app)
    states = container.get('teacher-attendance')
    if states is not None:
        # New states
        states.add(_('Present but at Internal commitments or CPD'), ACTIVE, 'c')
        states.add(_('Not timetabled'), INACTIVE+IGNORED, 't')
        states.add(_('Suspended'), INACTIVE+IGNORED, 'u')
        states.describe(INACTIVE+IGNORED, _('Ignored'))
        # Update existing states
        states.states['s'].title = _('Absent - sick')
        states.states['z'].title = _('Absent - authorised')
        states.states['i'].title = _('Absent - unauthorised')
        states.states['l'].title = _('Present but late and / or left early')
        # Update order
        order = ['a', 'l', 'c', 's', 'z', 'i', 't', 'u']
        states.states.updateOrder(order)
    setSite(old_site)
