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
Stream view components
"""

from urllib import urlencode

import xlwt
from zope.cachedescriptors.property import Lazy
from zope.catalog.interfaces import ICatalog
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.container.interfaces import INameChooser
from zope.event import notify
from zope.interface import implements
from zope.intid.interfaces import IIntIds
from zope.i18n.interfaces.locales import ICollator
from zope.i18n import translate
from zope.proxy import sameProxiedObjects
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser.absoluteurl import absoluteURL
from zope.traversing.browser.interfaces import IAbsoluteURL

from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form import widget
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.browser.checkbox import SingleCheckBoxFieldWidget

from schooltool import table
from schooltool.app.browser.app import ActiveSchoolYearContentMixin
from schooltool.app.browser.app import ContainerSearchContent
from schooltool.app.browser.app import JSONSearchViewBase
from schooltool.app.browser.app import RelationshipAddTableMixin
from schooltool.app.browser.app import RelationshipRemoveTableMixin
from schooltool.app.browser.states import EditRelationships
from schooltool.app.catalog import buildQueryString
from schooltool.app.interfaces import IRelationshipStateContainer
from schooltool.app.interfaces import ISchoolToolApplication
from schooltool.course.section import is_student
from schooltool.course.section import Section
from schooltool.course.interfaces import ICourseContainer
from schooltool.export.export import RequestXLSReportDialog
from schooltool.export.export import RemoteMegaExporter
from schooltool.export.export import Header
from schooltool.export.export import Text
from schooltool.export.export import Date
from schooltool.group.interfaces import IGroupContainer
from schooltool.group.group import defaultGroups
from schooltool.relationship.temporal import ACTIVE
from schooltool.relationship.temporal import ACTIVE_CODE
from schooltool.relationship.temporal import INACTIVE
from schooltool.relationship.temporal import INACTIVE_CODE
from schooltool.report.report import ReportLinkViewlet
from schooltool.basicperson.browser.person import EditPersonTemporalRelationships
from schooltool.common import SchoolToolMessage as _
from schooltool.course.browser.section import SectionsTableBase
from schooltool.course.interfaces import ISectionContainer
from schooltool.person.interfaces import IPersonFactory
from schooltool.schoolyear.interfaces import ISchoolYear
from schooltool.schoolyear.interfaces import ISchoolYearContainer
from schooltool.skin import flourish
from schooltool.stream.interfaces import GroupConvertedToStreamEvent
from schooltool.stream.interfaces import IStream
from schooltool.stream.interfaces import IStreamContainer
from schooltool.stream.stream import Stream
from schooltool.stream.stream import StreamMembers
from schooltool.task.progress import normalized_progress
from schooltool.term.interfaces import IDateManager
from schooltool.term.interfaces import ITerm


class StreamContainerAbsoluteURLAdapter(BrowserView):

    adapts(IStreamContainer, IBrowserRequest)
    implements(IAbsoluteURL)

    def __str__(self):
        container_id = int(self.context.__name__)
        int_ids = getUtility(IIntIds)
        container = int_ids.getObject(container_id)
        url = str(getMultiAdapter((container, self.request),
                                  name='absolute_url'))
        return url + '/streams'

    __call__ = __str__


class ManageStreamsOverview(ContainerSearchContent):

    add_view_name = 'addStream.html'
    hint = _('Manage streams')
    title = _('Streams')

    @property
    def container(self):
        return IStreamContainer(self.schoolyear)

    def container_url(self):
        return self.url_with_schoolyear_id(self.context, view_name='streams')

    @property
    def json_url(self):
        app = ISchoolToolApplication(None)
        return '%s/streams_json' % absoluteURL(app, self.request)


class StreamsJSONSearchView(JSONSearchViewBase,
                            ActiveSchoolYearContentMixin):

    @property
    def catalog(self):
        container = IStreamContainer(self.schoolyear)
        return ICatalog(container)

    @property
    def items(self):
        result = set()
        if self.text_query and self.schoolyear:
            int_ids = getUtility(IIntIds)
            schoolyear_id = int_ids.getId(self.schoolyear)
            schoolyear_query = {'any_of': [schoolyear_id]}
            params = {
                'text': self.text_query,
                'schoolyear_id': schoolyear_query,
            }
            for stream in self.catalog.searchResults(**params):
                result.add(stream)
        return result

    def encode(self, stream):
        label = stream.title
        return {
            'label': label,
            'value': label,
            'url': absoluteURL(stream, self.request),
        }


class StreamAddView(flourish.form.AddForm):

    template = flourish.templates.Inherit(flourish.page.Page.template)
    label = None
    legend = _('Stream Information')

    fields = field.Fields(IStream).select(
        'title',
        'description',
        'attendance_group')
    fields['attendance_group'].widgetFactory = SingleCheckBoxFieldWidget

    def updateActions(self):
        super(StreamAddView, self).updateActions()
        self.actions['add'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    @button.buttonAndHandler(_('Submit'), name='add')
    def handleAdd(self, action):
        super(StreamAddView, self).handleAdd.func(self, action)

    @button.buttonAndHandler(_('Cancel'))
    def handle_cancel_action(self, action):
        if 'camefrom' in self.request:
            url = self.request['camefrom']
            self.request.response.redirect(url)
            return
        app = ISchoolToolApplication(None)
        url = self.url_with_schoolyear_id(app, view_name='streams')
        self.request.response.redirect(url)

    def create(self, data):
        stream = Stream()
        form.applyChanges(self, stream, data)
        return stream

    def add(self, stream):
        chooser = INameChooser(self.context)
        name = chooser.chooseName(u'', stream)
        self.context[name] = stream
        self._stream = stream
        return stream

    def nextURL(self):
        return absoluteURL(self._stream, self.request)

    @property
    def schoolyear(self):
        return ISchoolYear(self.context)

    @property
    def title(self):
        return _('Streams for ${schoolyear}',
                 mapping={'schoolyear': self.schoolyear.title})


class StreamsView(flourish.page.Page,
                  ActiveSchoolYearContentMixin):

    content_template = flourish.templates.Inline('''
      <div>
        <tal:block content="structure view/container/schooltool:content/ajax/table" />
      </div>
    ''')

    @property
    def title(self):
        schoolyear = self.schoolyear
        return _('Streams for ${schoolyear}',
                 mapping={'schoolyear': schoolyear.title})

    @property
    def container(self):
        schoolyear = self.schoolyear
        return IStreamContainer(schoolyear)


class StreamsTable(table.ajax.IndexedTable):

    def columns(self):
        title = table.column.IndexedLocaleAwareGetterColumn(
            index='title',
            name='title',
            title=_(u'Title'),
            getter=lambda i, f: i.title,
            subsort=True)
        description = table.column.IndexedLocaleAwareGetterColumn(
            index='description',
            name='description',
            title=_('Description'),
            getter=lambda i, f: i.description or '',
            subsort=True)
        return [title, description]


class StreamsTableFilter(table.ajax.IndexedTableFilter):

    template = flourish.templates.File('templates/streams_table_filter.pt')

    title = _("Title or description")

    @property
    def search_id(self):
        return self.manager.html_id+'-search'

    @property
    def search_title_id(self):
        return self.manager.html_id+"-title"

    def query(self, items, params):
        result = self.catalog.searchResults(**params)
        return [item for item in items if item['id'] in result.uids]

    def filter(self, items):
        container_id = getUtility(IIntIds).getId(self.source)
        params = {'container_id': {'any_of': [container_id]}}
        if not self.ignoreRequest:
            searchstr = self.request.get(self.search_title_id, '')
            if searchstr:
                params['text'] = buildQueryString(searchstr)
        return self.query(items, params)


class StreamsTertiaryNavigationManager(flourish.page.TertiaryNavigationManager,
                                       ActiveSchoolYearContentMixin):

    template = flourish.templates.Inline("""
        <ul tal:attributes="class view/list_class">
          <li tal:repeat="item view/items"
              tal:attributes="class item/class"
              tal:content="structure item/viewlet">
          </li>
        </ul>
    """)

    @property
    def items(self):
        result = []
        active = self.schoolyear
        schoolyears = active.__parent__ if active is not None else {}
        for schoolyear in schoolyears.values():
            url = '%s/%s?schoolyear_id=%s' % (
                absoluteURL(self.context, self.request),
                'streams',
                schoolyear.__name__)
            result.append({
                    'class': schoolyear.first == active.first and 'active' or None,
                    'viewlet': u'<a href="%s">%s</a>' % (url, schoolyear.title),
                    })
        return result


class StreamsAddLinks(flourish.page.RefineLinksViewlet):

    pass


class StreamAddLinkViewlet(flourish.page.LinkViewlet,
                           ActiveSchoolYearContentMixin):

    @property
    def url(self):
        container = IStreamContainer(self.schoolyear)
        return '%s/%s' % (absoluteURL(container, self.request),
                          'addStream.html')


class StreamView(flourish.form.DisplayForm):

    template = flourish.templates.Inherit(flourish.page.Page.template)
    content_template = flourish.templates.File('templates/stream.pt')
    fields = field.Fields(IStream).select(
        'title',
        'description',
        'attendance_group')

    @property
    def schoolyear(self):
        return ISchoolYear(self.context)

    @property
    def title(self):
        return _('Streams for ${schoolyear}',
                 mapping={'schoolyear': self.schoolyear.title})

    @property
    def subtitle(self):
        return self.context.title

    def updateWidgets(self):
        super(StreamView, self).updateWidgets()
        for widget in self.widgets.values():
            if not widget.value:
                widget.mode = HIDDEN_MODE

    def has_members(self):
        return self.context.members

    @property
    def canModify(self):
        return flourish.hasPermission(self.context, 'schooltool.edit')

    @property
    def sections(self):
        return self.context.sections


class StreamEditView(flourish.form.Form, form.EditForm):

    template = flourish.templates.Inherit(flourish.page.Page.template)
    label = None
    legend = _('Stream Information')
    fields = field.Fields(IStream).select(
        'title',
        'description',
        'attendance_group')
    fields['attendance_group'].widgetFactory = SingleCheckBoxFieldWidget

    @property
    def title(self):
        return self.context.title

    def update(self):
        return form.EditForm.update(self)

    def updateActions(self):
        super(StreamEditView, self).updateActions()
        self.actions['apply'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    @button.buttonAndHandler(_('Submit'), name='apply')
    def handleApply(self, action):
        super(StreamEditView, self).handleApply.func(self, action)
        # XXX: hacky sucessful submit check
        if (self.status == self.successMessage or
            self.status == self.noChangesMessage):
            url = absoluteURL(self.context, self.request)
            self.request.response.redirect(url)

    @button.buttonAndHandler(_("Cancel"))
    def handle_cancel_action(self, action):
        url = absoluteURL(self.context, self.request)
        self.request.response.redirect(url)


class OtherStreamsBase(object):

    def other_streams(self, member, date):
        result = []
        links = StreamMembers.bind(member=member).on(date).relationships
        for link_info in links:
            if sameProxiedObjects(link_info.target, self.context):
                continue
            result.append(link_info.target)
        return result



class StreamStudentsView(EditPersonTemporalRelationships,
                         OtherStreamsBase):
    """View for adding learners to a Section."""

    app_states_name = "section-membership"
    dialog_title_template = _("Enroll ${target}")

    current_title = _("Current students")
    available_title = _("Add students")

    @property
    def title(self):
        return self.context.title

    def getCollection(self):
        return self.context.members

    def add(self, item, state=None, code=None, date=None):
        super(StreamStudentsView, self).add(item, state, code, date)
        sections = removeSecurityProxy(self.context.sections)
        meaning = state.active if state is not None else ACTIVE
        for section in sections:
            if item not in section.members.on(date):
                section.members.on(date).relate(item, meaning, code)

    def remove(self, item, state=None, code=None, date=None):
        super(StreamStudentsView, self).remove(item, state, code, date)
        sections = removeSecurityProxy(self.context.sections)
        meaning = state.active if state is not None else INACTIVE
        other_streams = self.other_streams(item, date)
        for section in sections:
            section_in_other_stream = False
            for stream in other_streams:
                if section in stream.sections:
                    section_in_other_stream = True
                    break
            if section_in_other_stream:
                continue
            if item in section.members.on(date):
                section.members.on(date).relate(item, meaning, code)


class StreamSectionsView(EditRelationships,
                         OtherStreamsBase):

    app_states_name = "section-membership"
    current_title = _('Current sections')
    available_title = _('Available sections')
    default_active_code = ACTIVE_CODE
    default_inactive_code = INACTIVE_CODE

    @property
    def title(self):
        return self.context.title

    def getCollection(self):
        return self.context.sections

    def getAvailableItemsContainer(self):
        return self.items_container

    @Lazy
    def items_container(self):
        sections = {}
        schoolyear = ISchoolYear(self.context)
        for term in schoolyear.values():
            term_section_container = ISectionContainer(term)
            for section in term_section_container.values():
                name = self.getKey(section)
                sections[name] = section
        return sections

    def getKey(self, section):
        term = ITerm(section)
        schoolyear = ISchoolYear(term)
        return '%s.%s.%s' % (
            schoolyear.__name__, term.__name__, section.__name__
        )

    def add(self, section):
        super(StreamSectionsView, self).add(section)
        members = removeSecurityProxy(self.context.members)
        state = self.default_active_state
        date = self.today
        for member in members:
            if member not in section.members.on(date):
                section.members.on(date).relate(
                    member, state.active, state.code)

    def remove(self, section):
        super(StreamSectionsView, self).remove(section)
        members = removeSecurityProxy(self.context.members)
        state = self.default_inactive_state
        date = self.today
        for member in members:
            if member in section.members.on(date):
                section_in_other_stream = False
                other_streams = self.other_streams(member, date)
                for stream in other_streams:
                    if section in stream.sections:
                        section_in_other_stream = True
                        break
                if section_in_other_stream:
                    continue
                section.members.on(date).relate(
                    member, state.active, state.code)

    @Lazy
    def today(self):
        return getUtility(IDateManager).today

    @Lazy
    def default_active_state(self):
        app = ISchoolToolApplication(None)
        container = IRelationshipStateContainer(app)
        app_states = container.get(self.app_states_name, None)
        if app_states is not None:
            for state in app_states.states.values():
                if state.code == self.default_active_code:
                    return state
            for state in app_states.states.values():
                if state.active == ACTIVE:
                    return state

    @Lazy
    def default_inactive_state(self):
        app = ISchoolToolApplication(None)
        container = IRelationshipStateContainer(app)
        app_states = container.get(self.app_states_name, None)
        if app_states is not None:
            for state in app_states.states.values():
                if state.code == self.default_inactive_code:
                    return state
            for state in app_states.states.values():
                if state.active == INACTIVE:
                    return state


class StreamSectionsTableBase(SectionsTableBase):

    visible_column_names = ['action', 'title', 'term', 'instructors']

    def sortOn(self):
        return (('term', True), ('courses', False), ('title', False))


class StreamSectionsListTable(StreamSectionsTableBase):

    visible_column_names = ['title', 'term', 'instructors']

    def items(self):
        return self.context.sections


class SectionAddRelationshipTable(RelationshipAddTableMixin,
                                  StreamSectionsTableBase):

    pass


class SectionRemoveRelationshipTable(RelationshipRemoveTableMixin,
                                     StreamSectionsTableBase):

    pass


class StreamsVocabulary(SimpleVocabulary):

    implements(IContextSourceBinder)

    def __init__(self, context):
        self.context = context
        terms = self.createTerms()
        SimpleVocabulary.__init__(self, terms)

    def createTerms(self):
        result = []
        result.append(self.createTerm(
            None,
            widget.SequenceWidget.noValueToken,
            _('Select a stream'),
        ))
        app = ISchoolToolApplication(None)
        schoolyear = ISchoolYearContainer(app).getActiveSchoolYear()
        container = IStreamContainer(schoolyear)
        for group in sorted(container.values(), key=lambda g: g.title):
            result.append(self.createTerm(
                group,
                group.__name__.encode('utf-8'),
                group.title,
            ))
        return result


def StreamsVocabularyFactory():
    return StreamsVocabulary


class StreamDoneLink(flourish.viewlet.Viewlet, ActiveSchoolYearContentMixin):

    template = flourish.templates.Inline('''
      <h3 class="done-link">
        <a tal:attributes="href view/done_link"
           i18n:translate="">Done</a>
      </h3>
    ''')

    def done_link(self):
        url = self.request.get('done_link', None)
        if url is not None:
            return url
        app = ISchoolToolApplication(None)
        return self.url_with_schoolyear_id(app, view_name='streams')


class StreamsAccordionViewlet(flourish.viewlet.Viewlet,
                              ActiveSchoolYearContentMixin):

    template = flourish.templates.File('templates/streams_accordion.pt')

    def render(self, *args, **kw):
        if is_student(self.context):
            return self.template(*args, **kw)
        return ''

    def app_states(self, key):
        app = ISchoolToolApplication(None)
        states = IRelationshipStateContainer(app)[key]
        return states

    def stream_current_states(self, link_info, app_states):
        states = []
        for date, active, code in link_info.state.all():
            state = app_states.states.get(code)
            title = state.title if state is not None else ''
            states.append({
                'date': date,
                'title': title,
                })
        return states

    def update(self):
        self.collator = ICollator(self.request.locale)
        relationships = StreamMembers.bind(member=self.context).all().relationships
        app_states = self.app_states('section-membership')
        schoolyears_data = {}
        for link_info in relationships:
            stream = removeSecurityProxy(link_info.target)
            sy = ISchoolYear(stream.__parent__)
            if sy not in schoolyears_data:
                schoolyears_data[sy] = []
            schoolyears_data[sy].append((stream, link_info))
        self.schoolyears = []
        for sy in sorted(schoolyears_data, key=lambda x:x.first, reverse=True):
            sy_info = {
                'obj': sy,
                'css_class': 'active' if sy is self.schoolyear else 'inactive',
                'streams': [],
                }
            for stream, link_info in sorted(schoolyears_data[sy],
                                            key=lambda x:self.collator.key(
                                                x[0].title)):
                states = self.stream_current_states(link_info, app_states)
                stream_info = {
                    'obj': stream,
                    'title': stream.title,
                    'states': states,
                    }
                sy_info['streams'].append(stream_info)
            self.schoolyears.append(sy_info)


class StreamActionsLinks(flourish.page.RefineLinksViewlet):

    pass


class StreamAddLinks(flourish.page.RefineLinksViewlet):

    pass


class StreamDeleteLink(flourish.page.ModalFormLinkViewlet):

    @property
    def enabled(self):
        if not flourish.canDelete(self.context):
            return False
        return super(StreamDeleteLink, self).enabled

    @property
    def dialog_title(self):
        title = _(u'Delete ${stream}',
                  mapping={'stream': self.context.title})
        return translate(title, context=self.request)


class StreamContainerDeleteView(flourish.containers.ContainerDeleteView):

    def nextURL(self):
        if 'CONFIRM' in self.request:
            schoolyear = ISchoolYear(self.context)
            params = {'schoolyear_id': schoolyear.__name__.encode('utf-8')}
            url = '%s/streams?%s' % (
                absoluteURL(ISchoolToolApplication(None), self.request),
                urlencode(params))
            return url
        return flourish.containers.ContainerDeleteView.nextURL(self)


class StreamDeleteView(flourish.form.DialogForm, form.EditForm):

    dialog_submit_actions = ('apply',)
    dialog_close_actions = ('cancel',)
    label = None

    @button.buttonAndHandler(_("Delete"), name='apply')
    def handleDelete(self, action):
        url = '%s/delete.html?delete.%s&CONFIRM' % (
            absoluteURL(self.context.__parent__, self.request),
            self.context.__name__.encode('utf-8'))
        self.request.response.redirect(url)
        # We never have errors, so just close the dialog.
        self.ajax_settings['dialog'] = 'close'

    @button.buttonAndHandler(_("Cancel"))
    def handle_cancel_action(self, action):
        pass

    def updateActions(self):
        super(StreamDeleteView, self).updateActions()
        self.actions['apply'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')


class PreviousYearStreamExportReportLink(ReportLinkViewlet,
                                         ActiveSchoolYearContentMixin):

    @property
    def extra_params(self):
        return {
            'schoolyear_id': self.schoolyear.__name__,
        }

    def render(self, *args, **kw):
        if self.schoolyear is None or self.previousYear is None:
            return ''
        return super(PreviousYearStreamExportReportLink, self).render(
            *args, **kw)


class PreviousYearStreamsExportRequestView(RequestXLSReportDialog):

    report_builder = 'previous_year_streams_export.xls'

    template = flourish.templates.File(
        'templates/previous_year_streams_export_form.pt')

    def resetForm(self):
        RequestXLSReportDialog.resetForm(self)
        self.form_params['schoolyear_id'] = self.request.get('schoolyear_id')

    def updateTaskParams(self, task):
        task.request_params['schoolyear_id'] = self.form_params['schoolyear_id']


class PreviousYearStreamsExporter(RemoteMegaExporter,
                                  ActiveSchoolYearContentMixin):

    base_filename = 'previous_year_streams'
    message_title = _('previous year streams')

    def format_stream(self, stream, ws, offset):
        fields = [lambda i: ("Stream Title", i.title, None),
                  lambda i: ("ID", i.__name__, None),
                  lambda i: ("School Year", self.schoolyear.__name__, None),
                  lambda i: ("Description", i.description, None)]

        offset = self.listFields(stream, fields, ws, offset)

        offset += self.print_table(
            self.format_membership_block(stream.members, [Header('Members')]),
            ws, row=offset, col=0)

        return offset

    def export_streams(self, wb):
        self.task_progress.force('export_streams', active=True)
        ws = wb.add_sheet("Streams")
        school_years = [self.previousYear]
        row = 0
        for ny, school_year in enumerate(sorted(school_years, key=lambda i: i.last)):
            streams = IStreamContainer(school_year)
            for ns, stream in enumerate(sorted(streams.values(), key=lambda i: i.__name__)):
                row = self.format_stream(stream, ws, row) + 1
                self.progress('export_streams', normalized_progress(
                        ny, len(school_years), ns, len(streams)
                        ))
        self.finish('export_streams')

    def addImporters(self, progress):
        progress.add('export_streams', active=False,
                     title=_('Streams'), progress=0.0)

    def format_membership_block(self, relationship, headers):
        items = sorted(relationship,
                       key=lambda item: item.__name__)
        if not items:
            return []
        table = [headers]
        collator = ICollator(self.request.locale)
        factory = getUtility(IPersonFactory)
        sorting_key = lambda x: factory.getSortingKey(x, collator)
        for item in sorted(items, key=sorting_key):
            cells = [
                Text(item.__name__),
                Text(item.title),
                Date(self.schoolyear.first),
                Text(ACTIVE_CODE),
            ]
            table.append(cells)
        table.append([])
        return table

    def __call__(self):
        self.makeProgress()
        self.task_progress.title = _("Exporting school data")
        self.addImporters(self.task_progress)

        wb = xlwt.Workbook()
        self.export_streams(wb)
        self.task_progress.title = _("Export complete")
        self.task_progress.force('overall', progress=1.0)
        data = self.render(wb)
        return data


class StreamSectionsAddLinks(flourish.page.RefineLinksViewlet):

    pass


class AddSectionsLinkViewlet(flourish.page.LinkViewlet):

    @property
    def enabled(self):
        return self.has_terms

    @property
    def has_terms(self):
        return ISchoolYear(self.context)


class AddSectionsView(flourish.page.Page):

    subtitle = _('Add Sections')
    content_template = flourish.templates.File('templates/add_sections.pt')
    no_value_token = '--NOVALUE--'
    container_class = 'container widecontainer'

    @property
    def title(self):
        return self.context.title

    @Lazy
    def schoolyear(self):
        return ISchoolYear(self.context)

    @Lazy
    def courses(self):
        courses = ICourseContainer(self.schoolyear)
        result = []
        # XXX: use ICollator
        for course in sorted(courses.values(), key=lambda course: course.title):
            result.append({
                'obj': course,
                'title': course.title,
                'section_title': '%s %s' % (self.context.title, course.title),
                'add_selector_id': self.add_selector_id(course),
                'instructor_selector_id': self.instructor_selector_id(course),
                'title_selector_id': self.title_selector_id(course),
                'term_start_selector_id': self.term_start_selector_id(course),
                'term_end_selector_id': self.term_end_selector_id(course),
            })
        return result

    def add_selector_id(self, course):
        return 'add.%s' % course.__name__

    def instructor_selector_id(self, course):
        return 'instructor.%s' % course.__name__

    def title_selector_id(self, course):
        return 'title.%s' % course.__name__

    def term_start_selector_id(self, course):
        return 'term_start.%s' % course.__name__

    def term_end_selector_id(self, course):
        return 'term_end.%s' % course.__name__

    @Lazy
    def sorted_terms(self):
        return sorted(self.schoolyear.values(), key=lambda term: term.first)

    @Lazy
    def term_start(self):
        return self.sorted_terms[0]

    @Lazy
    def term_end(self):
        return self.sorted_terms[-1]

    def redirect(self):
        url = '%s/sections.html' % absoluteURL(self.context, self.request)
        self.request.response.redirect(url)

    def update(self):
        if 'CANCEL' in self.request:
            self.redirect()
            return
        elif 'SUBMIT' in self.request:
            for course_info in self.courses:
                add_submitted = self.request.get(
                    course_info['add_selector_id'])
                if add_submitted == course_info['obj'].__name__:
                    self.create_sections(course_info)
            self.redirect()

    @Lazy
    def instructors(self):
        teachers = IGroupContainer(self.schoolyear)['teachers']
        result = []
        # XXX: use ICollator
        # XXX: remove .all()?
        for teacher in sorted(teachers.members.all(),
                              key=lambda teacher: teacher.title):
            result.append({
                'value': teacher.__name__,
                'title': teacher.title,
            })
        return result

    def term_start_selected(self, course, term):
        requested = self.request.get(self.term_start_selector_id(course))
        return ((requested and requested == term.__name__) or
                term is self.term_start)

    def term_end_selected(self, course, term):
        requested = self.request.get(self.term_end_selector_id(course))
        return ((requested and requested == term.__name__) or 
                term is self.term_end)

    def term_span(self, start, end):
        result = []
        for term in self.sorted_terms:
            if (start.first <= term.first) or (term.last <= end.last):
                result.append(term)
        return result

    @Lazy
    def persons(self):
        return ISchoolToolApplication(None)['persons']

    def create_sections(self, course_info):
        course = course_info['obj']
        requested_instructor = self.request.get(
            course_info['instructor_selector_id'])
        requested_term_start = self.request.get(
            course_info['term_start_selector_id'])
        instructor = self.persons.get(requested_instructor)
        term_start = self.schoolyear[requested_term_start]
        requested_term_end = self.request.get(
            course_info['term_end_selector_id'])
        term_end = self.schoolyear[requested_term_end]

        section = Section()
        sections = ISectionContainer(term_start)
        name = INameChooser(sections).chooseName('', section)
        title = self.request.get(course_info['title_selector_id'])
        if not title:
            title = u"%s (%s)" % (course.title, name)
        section.title = title
        sections[name] = section
        stream_sections = removeSecurityProxy(self.context).sections
        stream_sections.add(section)
        section.courses.add(removeSecurityProxy(course))
        if instructor is not None:
            section.instructors.on(term_start.first).add(instructor)
        # XXX: remove .all()?
        for student in self.context.members.all():
            section.members.on(term_start.first).add(
                removeSecurityProxy(student))

        terms = self.term_span(term_start, term_end)
        # copy and link section in other selected terms
        for term in terms[1:]:
            new_section = copySection(section, term)
            new_section.previous = section
            stream_sections.add(new_section)
            section = new_section


def copySection(section, target_term):
    """Create a copy of a section in a desired term."""
    section_copy = Section(section.title, section.description)
    sections = ISectionContainer(target_term)
    name = section.__name__
    if name in sections:
        name = INameChooser(sections).chooseName(name, section_copy)
    sections[name] = section_copy
    for course in section.courses:
        section_copy.courses.add(course)
    for instructor in section.instructors.on(ITerm(section).first):
        # XXX: add as pre-enrolled from today
        section_copy.instructors.on(target_term.first).add(instructor)
    for member in section.members.on(ITerm(section).first):
        # XXX: add as pre-enrolled from today
        section_copy.members.on(target_term.first).add(member)
    return section_copy


class StreamsActionsLinks(flourish.page.RefineLinksViewlet):

    pass


class ConvertGroupsLinkViewlet(flourish.page.LinkViewlet,
                               ActiveSchoolYearContentMixin):

    @property
    def url(self):
        return '%s/convert_groups_to_streams.html' % (
            absoluteURL(self.schoolyear, self.request))


class ConvertGroupsToStreamsView(flourish.page.Page):

    def update(self):
        groups = IGroupContainer(self.context)
        for group in groups.values():
            if (group.__name__ not in defaultGroups and
                group.__name__ not in self.streams):
                self.convert_group(group)
        self.request.response.redirect(self.nextURL)

    def convert_group(self, group):
        stream = Stream()
        stream.title = group.title
        stream.description = group.description
        self.streams[group.__name__] = stream
        for member in group.members:
            stream.members.on(self.context.first).add(member)
        notify(GroupConvertedToStreamEvent(stream))

    @Lazy
    def streams(self):
        return IStreamContainer(self.context)

    @property
    def nextURL(self):
        return '%s/streams?schoolyear_id=%s' % (
            absoluteURL(ISchoolToolApplication(None), self.request),
            self.context.__name__.encode('utf-8'))
