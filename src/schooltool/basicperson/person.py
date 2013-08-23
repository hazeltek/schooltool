#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2007 Shuttleworth Foundation
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
Lyceum person specific code.
"""
from zope.catalog.text import TextIndex
from zope.index.text.interfaces import ISearchableText
from zope.interface import implements
from zope.component import adapts

from schooltool.person.person import Person
from schooltool.person.interfaces import IPersonFactory
from schooltool.course.section import PersonInstructorsCrowd
from schooltool.person.person import PersonCalendarCrowd
from schooltool.table.catalog import IndexedLocaleAwareGetterColumn
from schooltool.table.table import url_cell_formatter
from schooltool.relationship import RelationshipProperty
from schooltool.basicperson.advisor import URIAdvisor, URIAdvising, URIStudent
from schooltool.basicperson.interfaces import IBasicPerson
from schooltool.app.catalog import AttributeCatalog
from schooltool.common import SchoolToolMessage as _


class BasicPerson(Person):
    implements(IBasicPerson)

    prefix = None
    middle_name = None
    suffix = None
    preferred_name = None
    gender = None
    birth_date = None

    def __init__(self, username, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

    @property
    def title(self):
        return "%s, %s" % (self.last_name, self.first_name)

    advisors = RelationshipProperty(rel_type=URIAdvising,
                                    my_role=URIStudent,
                                    other_role=URIAdvisor)

    advisees = RelationshipProperty(rel_type=URIAdvising,
                                    my_role=URIAdvisor,
                                    other_role=URIStudent)


class PersonFactoryUtility(object):

    implements(IPersonFactory)

    def columns(self):
        first_name = IndexedLocaleAwareGetterColumn(
            index='first_name',
            name='first_name',
            cell_formatter=url_cell_formatter,
            title=_(u'First Name'),
            getter=lambda i, f: i.first_name,
            subsort=True)
        last_name = IndexedLocaleAwareGetterColumn(
            index='last_name',
            name='last_name',
            cell_formatter=url_cell_formatter,
            title=_(u'Last Name'),
            getter=lambda i, f: i.last_name,
            subsort=True)

        return [first_name, last_name]

    def createManagerUser(self, username, system_name):
        return self(username, system_name, "Administrator")

    def sortOn(self):
        return (("last_name", False),)

    def groupBy(self):
        return (("grade", False),)

    def __call__(self, *args, **kw):
        result = BasicPerson(*args, **kw)
        return result


class BasicPersonCalendarCrowd(PersonCalendarCrowd):
    """Crowd that allows instructor of a person access persons calendar.

    XXX write functional test.
    """
    adapts(IBasicPerson)

    def contains(self, principal):
        return (PersonCalendarCrowd.contains(self, principal) or
                PersonInstructorsCrowd(self.context).contains(principal))


class PersonCatalog(AttributeCatalog):

    version = '2 - added text index'
    interface = IBasicPerson
    attributes = ('__name__', 'title', 'first_name', 'last_name')

    def setIndexes(self, catalog):
        super(PersonCatalog, self).setIndexes(catalog)
        catalog['text'] = TextIndex('getSearchableText', ISearchableText, True)


getPersonCatalog = PersonCatalog.get


class SearchableTextPerson(object):

    adapts(IBasicPerson)
    implements(ISearchableText)

    def __init__(self, context):
        self.context = context

    def getSearchableText(self):
        result = [self.context.first_name, self.context.last_name,
                  self.context.username]
        return ' '.join(result)
