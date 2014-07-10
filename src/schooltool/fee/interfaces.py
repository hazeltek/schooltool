#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2014 Shuttleworth Foundation
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
Fee related interfaces
"""

from zope.container.constraints import contains
from zope.interface import Interface
from zope.schema import Date
from zope.schema import Decimal
from zope.schema import Text
from zope.schema import TextLine

from schooltool.common import SchoolToolMessage as _


class IFeeContainer(Interface):

    contains('.IAmount')


class IAmount(Interface):

    date = Date(title=_(u'Date'))

    title = TextLine(title=_(u'Title'), required=False)

    description = Text(title=_(u'Description'), required=False)

    amount = Decimal(title=_(u'Amount'))


class IDebit(IAmount):

    title = TextLine(title=_(u'Title'))


class ICredit(IAmount):

    pass
