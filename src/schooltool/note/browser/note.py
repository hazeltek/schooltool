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
Note views
"""

import cgi
import re

from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.component import queryMultiAdapter
from zope.container.interfaces import INameChooser
from zope.i18n import translate
from zope.proxy import sameProxiedObjects
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser.absoluteurl import absoluteURL

from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form import widget
from z3c.form.interfaces import DISPLAY_MODE
from zc.table.column import GetterColumn

from schooltool.skin import flourish
from schooltool.common import getResourceURL
from schooltool.common.inlinept import InheritTemplate
from schooltool import table
from schooltool.common import SchoolToolMessage as _
from schooltool.note.interfaces import INoteContainer
from schooltool.note.interfaces import INote
from schooltool.note.note import Note
from schooltool.course.section import is_student
from schooltool.course.section import is_teacher
from schooltool.person.interfaces import IPerson


class PersonNotesViewlet(flourish.viewlet.Viewlet):

    template = ViewPageTemplateFile('templates/personnotes.pt')

    @property
    def canModify(self):
        return flourish.canEdit(self.notes)

    @Lazy
    def notes(self):
        return INoteContainer(self.context)

    def render(self, *args, **kw):
        user = IPerson(self.request.principal, None)
        if sameProxiedObjects(user, self.context):
            return ''
        if is_student(self.context) or is_teacher(self.context):
            return self.template(*args, **kw)
        return ''


def edit_cell_formatter(value, item, formatter):
    principal = IPerson(formatter.request.principal, None)
    if principal is None or principal not in item.editors:
        return ''
    template = '''
      <a class="modify" href="%(edit_url)s" title="%(link_title)s">
        <img src="%(edit_icon_url)s" alt="%(edit_title)s" />
      </a>'''
    request = formatter.request
    library = 'schooltool.skin.flourish'
    item_url = absoluteURL(item, request)
    person_url = absoluteURL(IPerson(item.__parent__), request)
    return template % {
        'edit_url': '%s/edit.html?camefrom=%s' % (item_url, person_url),
        # XXX translate
        'link_title': 'Edit this note',
        'edit_icon_url': getResourceURL(library, 'edit-icon.png', request),
        'edit_title': translate(_('Edit'), context=request),
    }


def category_cell_formatter(value, item, formatter):
    vocabulary = INote['category'].vocabulary
    try:
        term = vocabulary.getTermByToken(value)
        return term.title
    except (LookupError,):
        return ''


class DateColumn(table.column.DateColumn):

    def cell_formatter(self, maybe_date, item, formatter):
        view = queryMultiAdapter((maybe_date, formatter.request),
                                 name='shortDate',
                                 default=lambda: '')
        return view()


splits = re.compile(r'</?[p|br|strong|b|em|i|a][^>]*>')


def single_line(snippet, escape=False):
    if not snippet:
        return ''
    result = []
    for token in splits.split(snippet):
        if not token or token.isspace():
            continue
        text = flourish.report.unescapeHTMLEntities(unicode(token))
        if escape:
            text = cgi.escape(text)
        result.append(text.strip())
    return ' '.join(result)


class NoteContainerTable(table.ajax.Table):

    @property
    def visible_column_names(self):
        result = ['action', 'date', 'editors', 'category', 'body']
        if not self.view.canModify:
            result = result[1:]
        return result

    def sortOn(self):
        return (('date', False), ('editors', False))

    def columns(self):
        actions = self.getActionColumns()
        date = DateColumn(
            name='date',
            title=_('Date'),
            getter=lambda i, f: i.date,
            subsort=True)
        editors = GetterColumn(
            name='editors',
            # XXX: translate
            title=u'Author',
            getter=lambda i, f: ' '.join([removeSecurityProxy(e).title
                                          for e in i.editors]),
            subsort=True)
        category = GetterColumn(
            name='category',
            title=u'Category',
            getter=lambda i, f: i.category,
            cell_formatter=category_cell_formatter)
        body = GetterColumn(
            name='body',
            title=_('Note'),
            getter=lambda i, f: '%s...' % single_line(i.body, True)[:25],
            cell_formatter=table.table.url_cell_formatter)
        return actions + [date, editors, category, body]

    def getActionColumns(self):
        if self.view.canModify:
            return [
                GetterColumn(
                    name='action',
                    title=_('Edit'),
                    getter=lambda i, f: i,
                    cell_formatter=edit_cell_formatter)
            ]
        return []

    def updateFormatter(self):
        if self._table_formatter is None:
            self.setUp(table_formatter=self.table_formatter,
                       batch_size=self.batch_size,
                       prefix=self.__name__,
                       css_classes={'table': 'data notes'})


class NoteAddView(flourish.form.AddForm):

    template = InheritTemplate(flourish.page.Page.template)
    label = None
    # XXX translate
    legend = u'Note Information'
    fields = field.Fields(INote).omit('editors')
    factory = Note

    @Lazy
    def person(self):
        return IPerson(self.context)

    @property
    def title(self):
        return self.person.title

    def updateActions(self):
        super(NoteAddView, self).updateActions()
        self.actions['add'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    @button.buttonAndHandler(_('Submit'), name='add')
    def handleAdd(self, action):
        super(NoteAddView, self).handleAdd.func(self, action)

    @button.buttonAndHandler(_('Cancel'))
    def handleCancel(self, action):
        self.request.response.redirect(self.nextURL())

    def nextURL(self):
        if is_student(self.person):
            active_accordion = 6
        elif is_teacher(self.person):
            active_accordion = 4
        else:
            active_accordion = 0
        return '%s?active_accordion=%d' % (
            absoluteURL(self.person, self.request), active_accordion)

    def create(self, data):
        obj = self.factory()
        form.applyChanges(self, obj, data)
        return obj

    def add(self, obj):
        chooser = INameChooser(self.context)
        name = chooser.chooseName(u'', obj)
        self.context[name] = obj
        person = IPerson(self.request.principal, None)
        if person is not None:
            obj.editors.add(removeSecurityProxy(person))


AddNoteDefaultDate = widget.ComputedWidgetAttribute(
    lambda adapter: adapter.request.util.today,
    view=NoteAddView,
    field=INote['date']
    )


class NoteEditView(flourish.form.Form, form.EditForm):

    template = InheritTemplate(flourish.page.Page.template)
    content_template = ViewPageTemplateFile('templates/note_form.pt')
    # XXX: translate
    legend = 'Note Information'
    fields = field.Fields(INote).omit('editors')

    @Lazy
    def person(self):
        return IPerson(self.context.__parent__)

    @property
    def title(self):
        return self.person.title

    def update(self):
        form.EditForm.update(self)

    def updateActions(self):
        super(NoteEditView, self).updateActions()
        self.actions['submit'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    def nextURL(self):
        try:
            return self.request['camefrom']
        except (KeyError,):
            return '%s?active_accordion=6' % absoluteURL(self.person,
                                                         self.request)

    @button.buttonAndHandler(_('Submit'), name='submit')
    def handle_submit(self, action):
        super(NoteEditView, self).handleApply.func(self, action)
        if (self.status == self.successMessage or
           self.status == self.noChangesMessage):
            self.request.response.redirect(self.nextURL())

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handle_cancel(self, action):
        self.request.response.redirect(self.nextURL())


class NoteActionsLinks(flourish.page.RefineLinksViewlet):

    pass


class NoteDeleteLink(flourish.page.LinkViewlet):

    @property
    def url(self):
        return '%s/delete.html?delete.%s&CONFIRM' % (
            absoluteURL(self.context.__parent__, self.request),
            self.context.__name__.encode('utf-8'))


class NoteContainerDeleteView(flourish.containers.ContainerDeleteView):

    @Lazy
    def person(self):
        return IPerson(self.context)

    def nextURL(self):
        if 'CONFIRM' in self.request:
            return '%s?active_accordion=6' % absoluteURL(self.person,
                                                         self.request)
        return flourish.containers.ContainerDeleteView.nextURL(self)


class NoteView(flourish.page.Page):

    @property
    def title(self):
        return self.context.__parent__.__parent__.title


class NoteDetails(flourish.form.FormViewlet):

    template = ViewPageTemplateFile('templates/note.pt')
    fields = field.Fields(INote).omit('editors')
    mode = DISPLAY_MODE

    @property
    def canModify(self):
        return flourish.canEdit(self.notes)

    @Lazy
    def notes(self):
        return self.context.__parent__

    @Lazy
    def person(self):
        return self.context.__parent__.__parent__

    def done_link(self):
        return '%s?active_accordion=6' % absoluteURL(self.person, self.request)
