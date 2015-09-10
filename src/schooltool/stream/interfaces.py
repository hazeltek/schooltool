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
Stream interfaces
"""

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer
from zope.interface import Attribute
from zope.schema import Text
from zope.schema import TextLine

from schooltool.common import SchoolToolMessage as _


class IStreamContainer(IContainer):

    pass


class IStreamContainerContainer(IContainer):

    pass


class IStream(IContained):

    title = TextLine(title=_('Title'))

    description = Text(title=_('Description'), required=False)

    members = Attribute('Relationship with person objects')

    sections = Attribute('Relationship with section objects')
