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
Upgrade SchoolTool to generation 46.

Updates leave school demographics fields
"""

from zope.app.dependable.interfaces import IDependable
from zope.app.generations.utility import getRootFolder
from zope.component.hooks import getSite, setSite

from schooltool.basicperson.demographics import EnumFieldDescription
from schooltool.basicperson.demographics import TextFieldDescription
from schooltool.basicperson.interfaces import IDemographicsFields
from schooltool.common import SchoolToolMessage as _


def evolve(context):
    root = getRootFolder(context)
    old_site = getSite()
    app = root
    setSite(app)
    dfs = IDemographicsFields(app)
    REASON_KEY = 'leave_reason'
    if REASON_KEY in dfs:
        item = _('Other')
        if item not in dfs[REASON_KEY].items:
            dfs[REASON_KEY].items.append(item)
    DESTINATION_KEY = 'leave_destination'
    if DESTINATION_KEY in dfs:
        if isinstance(dfs[DESTINATION_KEY], EnumFieldDescription):
            current_order = list(dfs.keys())
            title = dfs[DESTINATION_KEY].title
            limit_keys = dfs[DESTINATION_KEY].limit_keys[:]
            IDependable(dfs[DESTINATION_KEY]).removePath('')
            del dfs[DESTINATION_KEY]
            dfs[DESTINATION_KEY] = TextFieldDescription(
                DESTINATION_KEY, title, limit_keys=limit_keys)
            IDependable(dfs[DESTINATION_KEY]).addDependent('')
            dfs.updateOrder(current_order)
    setSite(old_site)
