#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2005 Shuttleworth Foundation
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
SchoolTool libraries and application
"""

VERSION='SVN'

from zope.i18n import MessageIDFactory
SchoolToolMessageID = MessageIDFactory("schooltool")



# This utility function is located here in order to avoid circular imports
# between schooltool.app and schooltool.timetable

from zope.app.component.hooks import getSite


def getSchoolToolApplication():
    """Return the nearest ISchoolToolApplication."""
    from schooltool.interfaces import ISchoolToolApplication

    candidate = getSite()
    if ISchoolToolApplication.providedBy(candidate):
        return candidate
    else:
        raise ValueError("can't get a SchoolToolApplication")
