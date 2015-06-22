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
Note related interfaces
"""

from zope.container.constraints import contains
from zope.html.field import HtmlFragment
from zope.interface import Attribute
from zope.interface import Interface
from zope.schema import Choice
from zope.schema import Date

from schooltool.app.utils import vocabulary
from schooltool.common import SchoolToolMessage as _


class INoteContainer(Interface):

    contains('.INote')


class INote(Interface):

    date = Date(title=_(u'Date'))

    editors = Attribute('IBasicPerson objects (see IRelationshipProperty)')

    category = Choice(
        title=_(u'Category'),
        vocabulary=vocabulary([
            ('attendance', _('Attendance')),
            ('attainment', _('Attainment / Performance')),
            ('behaviour', _('Behaviour')),
            ('extra', _('Extra responsibilities')),
            ('fees', _('Fees')),
            ('lesson', _('Teacher lesson observation')),
            ('other', _('Other')),
        ]))

    body = HtmlFragment(title=_('Note'))
