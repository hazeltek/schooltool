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
Note components
"""

from persistent import Persistent

from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.container.btree import BTreeContainer
from zope.container.contained import Contained
from zope.interface import implementer
from zope.interface import implements

from schooltool.person.interfaces import IPerson
from schooltool.relationship import RelationshipProperty
from schooltool.relationship import URIObject
from schooltool.relationship import RelationshipSchema
from schooltool.securitypolicy.crowds import Crowd

from schooltool.note.interfaces import INoteContainer
from schooltool.note.interfaces import INote


PERSON_NOTE_KEY = 'schooltool.peas.note.person'


URINoteEditors = URIObject(
    'http://schooltool.org/ns/peas/note/note_editors',
    'Note editors',
    'Editors of this note.')


URINote = URIObject(
    'http://schooltool.org/ns/peas/note/note',
    'Note',
    'A note.')


URINoteEditor = URIObject(
    'http://schooltool.org/ns/peas/note/note_editor',
    'Note editor',
    'A note editor.')


NoteEditors = RelationshipSchema(
    URINoteEditors,
    note=URINote,
    editor=URINoteEditor)


class NoteContainer(BTreeContainer):

    implements(INoteContainer)


class Note(Persistent, Contained):

    implements(INote)

    date = None
    category = None
    body = None

    editors = RelationshipProperty(URINoteEditors,
                                   URINote,
                                   URINoteEditor)


class NoteEditorsCrowd(Crowd):

    def contains(self, principal):
        person = IPerson(principal, None)
        if person is not None:
            return person in self.context.editors
        return False


@implementer(INoteContainer)
@adapter(IPerson)
def getPersonNoteContainer(person):
    ann = IAnnotations(person)
    try:
        return ann[PERSON_NOTE_KEY]
    except (KeyError,):
        ann[PERSON_NOTE_KEY] = NoteContainer()
        ann[PERSON_NOTE_KEY].__name__ = 'notes'
        ann[PERSON_NOTE_KEY].__parent__ = person
        return ann[PERSON_NOTE_KEY]


@implementer(IPerson)
@adapter(INoteContainer)
def getNoteContainerPerson(container):
    return container.__parent__
