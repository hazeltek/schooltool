#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2016 Shuttleworth Foundation
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
Upgrade SchoolTool to generation 49.

Set ups new _order attribute in course containers
"""

from persistent.list import PersistentList

from zope.app.generations.utility import getRootFolder
from zope.component.hooks import getSite, setSite

from schooltool.schoolyear.interfaces import ISchoolYearContainer
from schooltool.course.interfaces import ICourseContainer


def evolve(context):
    root = getRootFolder(context)
    old_site = getSite()
    app = root
    setSite(app)
    schoolyears = ISchoolYearContainer(app)
    for schoolyear in schoolyears.values():
        container = ICourseContainer(schoolyear)
        order = sorted(container._SampleContainer__data.keys())
        container._order = PersistentList(order)
    setSite(old_site)
