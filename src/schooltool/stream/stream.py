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
Stream components
"""

from persistent import Persistent

from zope.annotation.interfaces import IAttributeAnnotatable
from zope.catalog.text import TextIndex
from zope.component import adapter
from zope.component import adapts
from zope.component import getUtility
from zope.container.btree import BTreeContainer
from zope.container.contained import Contained
from zope.index.text.interfaces import ISearchableText
from zope.interface import implementer
from zope.interface import implements
from zope.intid.interfaces import IIntIds

from schooltool.app.app import StartUpBase
from schooltool.app.catalog import AttributeCatalog
from schooltool.app.interfaces import ISchoolToolApplication
from schooltool.relationship import RelationshipProperty
from schooltool.relationship import RelationshipSchema
from schooltool.relationship import URIObject
from schooltool.relationship.temporal import TemporalURIObject
from schooltool.schoolyear.interfaces import ISchoolYear
from schooltool.stream.interfaces import IStream
from schooltool.stream.interfaces import IStreamContainer
from schooltool.stream.interfaces import IStreamContainerContainer
from schooltool.table.catalog import ConvertingIndex


STREAM_CONTAINER_KEY = 'schooltool.stream.stream'


URIStreamMembers = TemporalURIObject(
    'http://schooltool.org/ns/stream/members',
    'Stream Members',
    'The members of a stream.')


URIStream = URIObject(
    'http://schooltool.org/ns/stream/stream',
    'Stream',
    'A stream with members and sections.')


URIStreamMember = URIObject(
    'http://schooltool.org/ns/stream/members/member',
    'Stream Member',
    'Member of a stream.')


URIStreamSections = URIObject(
    'http://schooltool.org/ns/stream/sections',
    'Stream Sections',
    'The sections of a stream.')


URIStreamSection = URIObject(
    'http://schooltool.org/ns/stream/sections/section',
    'Stream Section',
    'Section of a stream.')


StreamMembers = RelationshipSchema(URIStreamMembers,
                                   stream=URIStream,
                                   member=URIStreamMember)


StreamSections = RelationshipSchema(URIStreamSections,
                                    stream=URIStream,
                                    member=URIStreamSection)


class StreamContainer(BTreeContainer):

    implements(IStreamContainer, IAttributeAnnotatable)


class StreamContainerContainer(BTreeContainer):

    implements(IStreamContainerContainer, IAttributeAnnotatable)


class StreamStartUp(StartUpBase):

    def __call__(self):
        if STREAM_CONTAINER_KEY not in self.app:
            self.app[STREAM_CONTAINER_KEY] = StreamContainerContainer()


class Stream(Persistent, Contained):

    implements(IStream, IAttributeAnnotatable)

    title = None
    description = None

    members = RelationshipProperty(URIStreamMembers,
                                   URIStream,
                                   URIStreamMember)

    sections = RelationshipProperty(URIStreamSections,
                                    URIStream,
                                    URIStreamSection)


def getSchoolYearID(stream):
    int_ids = getUtility(IIntIds)
    schoolyear = ISchoolYear(stream)
    return int_ids.getId(schoolyear)


def getStreamContainerID(stream):
    int_ids = getUtility(IIntIds)
    container = IStreamContainer(stream)
    return int_ids.getId(container)


class StreamCatalog(AttributeCatalog):

    version = '1 - initial'
    interface = IStream
    attributes = ('title', 'description')

    def setIndexes(self, catalog):
        super(StreamCatalog, self).setIndexes(catalog)
        catalog['text'] = TextIndex('getSearchableText', ISearchableText, True)
        catalog['container_id'] = ConvertingIndex(
            converter=getStreamContainerID)
        catalog['schoolyear_id'] = ConvertingIndex(converter=getSchoolYearID)


getStreamCatalog = StreamCatalog.get


class SearchableTextStream(object):

    adapts(IStream)
    implements(ISearchableText)

    def __init__(self, context):
        self.context = context

    def getSearchableText(self):
        result = [
            self.context.title or '',
            self.context.description or '',
        ]
        return ' '.join(result)


@adapter(IStreamContainer)
@implementer(ISchoolYear)
def getSchoolYearForStreamContainer(stream_container):
    container_id = int(stream_container.__name__)
    int_ids = getUtility(IIntIds)
    container = int_ids.getObject(container_id)
    return container


@adapter(ISchoolYear)
@implementer(IStreamContainer)
def getStreamContainer(sy):
    int_ids = getUtility(IIntIds)
    sy_id = str(int_ids.getId(sy))
    app = ISchoolToolApplication(None)
    container = app[STREAM_CONTAINER_KEY].get(sy_id, None)
    if container is None:
        container = app[STREAM_CONTAINER_KEY][sy_id] = StreamContainer()
    return container

@adapter(IStream)
@implementer(IStreamContainer)
def getStreamContainerForStream(stream):
    return stream.__parent__


@adapter(IStream)
@implementer(ISchoolYear)
def getSchoolYearForStream(stream):
    return ISchoolYear(IStreamContainer(stream))
