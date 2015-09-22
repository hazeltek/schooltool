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

from zope.cachedescriptors.property import Lazy
from zope.catalog.interfaces import ICatalog
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.container.interfaces import INameChooser
from zope.interface import implements
from zope.intid.interfaces import IIntIds
from zope.i18n.interfaces.locales import ICollator
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
from schooltool.relationship.temporal import ACTIVE
from schooltool.relationship.temporal import ACTIVE_CODE
from schooltool.relationship.temporal import INACTIVE
from schooltool.relationship.temporal import INACTIVE_CODE
from schooltool.basicperson.browser.person import EditPersonTemporalRelationships
from schooltool.common import SchoolToolMessage as _
from schooltool.course.browser.section import SectionsTableBase
from schooltool.course.interfaces import ISectionContainer
from schooltool.schoolyear.interfaces import ISchoolYear
from schooltool.schoolyear.interfaces import ISchoolYearContainer
from schooltool.skin import flourish
from schooltool.stream.interfaces import IStream
from schooltool.stream.interfaces import IStreamContainer
from schooltool.stream.stream import Stream
from schooltool.stream.stream import StreamMembers
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

    fields = field.Fields(IStream).select('title', 'description')

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
    fields = field.Fields(IStream).select('title', 'description')

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
    fields = field.Fields(IStream).select('title', 'description')

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
