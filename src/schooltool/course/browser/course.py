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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
course browser views.
"""

from urllib import urlencode

from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.catalog.interfaces import ICatalog
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.component import getUtility
from zope.container.interfaces import INameChooser
from zope.interface import Interface
from zope.intid.interfaces import IIntIds
from zope.app.form.browser.add import AddView
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import BrowserView
from zope.schema import Choice
from zope.security.checker import canAccess
from zope.security import checkPermission
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser.interfaces import IAbsoluteURL
from zope.traversing.browser.absoluteurl import absoluteURL
from zope.i18n.interfaces.locales import ICollator
from zope.i18n import translate
from zope.viewlet.viewlet import ViewletBase
from z3c.form import field, button, form
from z3c.form.interfaces import HIDDEN_MODE
from zc.table.column import GetterColumn

from schooltool.app.catalog import buildQueryString
from schooltool.app.interfaces import ISchoolToolApplication
from schooltool.app.interfaces import IRelationshipStateContainer
from schooltool.app.browser.app import ContentTitle
from schooltool.app.browser.app import ContainerSearchContent
from schooltool.app.browser.app import ActiveSchoolYearContentMixin
from schooltool.app.browser.app import JSONSearchViewBase
from schooltool.app.membership import Membership
from schooltool.app.relationships import Instruction
from schooltool.common.inlinept import InheritTemplate
from schooltool.common.inlinept import InlineViewPageTemplate
from schooltool.term.interfaces import IDateManager
from schooltool.term.interfaces import ITerm
from schooltool.schoolyear.interfaces import ISchoolYear
from schooltool.skin.containers import ContainerView
from schooltool.course.interfaces import ICourse, ICourseContainer
from schooltool.course.interfaces import ISectionContainer
from schooltool.course.interfaces import ILearner, IInstructor
from schooltool.course.interfaces import ISection
from schooltool.course.course import Course
from schooltool.group.interfaces import IGroupContainer
from schooltool.level.interfaces import ILevelContainer
from schooltool.skin import flourish
from schooltool.skin.flourish.viewlet import Viewlet
from schooltool.skin.flourish.containers import ContainerDeleteView
from schooltool.skin.flourish.page import RefineLinksViewlet
from schooltool.skin.flourish.page import LinkViewlet
from schooltool.skin.flourish.page import Page
from schooltool.skin.flourish.page import Content
from schooltool.skin.flourish.page import ModalFormLinkViewlet
from schooltool.skin.flourish.form import Form
from schooltool.skin.flourish.form import AddForm
from schooltool.skin.flourish.form import DialogForm
from schooltool.skin.flourish.form import DisplayForm
from schooltool.skin.flourish.page import TertiaryNavigationManager
from schooltool.course.section import COMPLETED
from schooltool import table
from schooltool.common import SchoolToolMessage as _


class CourseContainerAbsoluteURLAdapter(BrowserView):

    adapts(ICourseContainer, IBrowserRequest)
    implements(IAbsoluteURL)

    def __str__(self):
        container_id = int(self.context.__name__)
        int_ids = getUtility(IIntIds)
        container = int_ids.getObject(container_id)
        url = str(getMultiAdapter((container, self.request), name='absolute_url'))
        return url + '/courses'

    __call__ = __str__


class CourseContainerView(ContainerView):
    """A Course Container view."""

    __used_for__ = ICourseContainer

    index_title = _("Course index")

    @property
    def school_year(self):
        return ISchoolYear(self.context)


class CourseView(BrowserView):
    """A view for courses."""

    __used_for__ = ICourse

    @property
    def school_year(self):
        return ISchoolYear(self.context)

    @property
    def details(self):
        details = []
        for name in ['course_id', 'government_id', 'credits']:
            value = getattr(self.context, name)
            if value is not None and unicode(value).strip():
                details.append({
                    'title': ICourse[name].title,
                    'value': value,
                    })
        return details

    @property
    def sections(self):
        items = []
        for section in self.context.sections:
            term = ITerm(section, None)
            items.append({
                'section': section,
                'term': term,
                })
        def sortKey(item):
            # I consider it acceptable to violate security for sorting purposes
            # in this case.
            section = removeSecurityProxy(item['section'])
            term = removeSecurityProxy(item['term'])
            return u'%s%s%s' % (section.label,
                                term.first,
                                section.__name__)
        return sorted(items, key=sortKey)


class CourseAddView(AddView):
    """A view for adding Courses."""

    def nextURL(self):
        return absoluteURL(self.context.context, self.request)

    def update(self):
        if 'CANCEL' in self.request:
            self.request.response.redirect(self.nextURL())
        else:
            return AddView.update(self)


class CoursesViewlet(ViewletBase):
    """A viewlet showing the courses a person is in."""

    def __init__(self, *args, **kw):
        super(CoursesViewlet, self).__init__(*args, **kw)
        self.collator = ICollator(self.request.locale)

    def update(self):
        self.instructorOf = self.sectionsAsTeacher()
        self.learnerOf = self.sectionsAsLearner()

    def isTeacher(self):
        """Find out if the person is an instructor for any sections."""
        return bool(self.instructorOf)

    def isLearner(self):
        """Find out if the person is a member of any sections."""
        return bool(self.learnerOf)

    def sectionsAsTeacher(self):
        """Get the sections the person instructs."""
        return self.sectionsAs(IInstructor)

    def sectionsAsLearner(self):
        """Get the sections the person is a member of."""
        return self.sectionsAs(ILearner)

    def sectionsAs(self, role_interface):
        schoolyears_data = {}
        for section in role_interface(self.context).sections():
            sy = ISchoolYear(section)
            if sy not in schoolyears_data:
                schoolyears_data[sy] = {}
            term = ITerm(section)
            if term not in schoolyears_data[sy]:
                schoolyears_data[sy][term] = []
            schoolyears_data[sy][term].append(section)
        result = []
        for sy in sorted(schoolyears_data, key=lambda x:x.first, reverse=True):
            sy_info = {'obj': sy, 'terms': []}
            for term in sorted(schoolyears_data[sy], key=lambda x:x.first):
                sortingKey = lambda section:{'course':
                                             ', '.join([course.title
                                                        for course in
                                                        section.courses]),
                                             'section_title': section.title}
                term_info = {'obj': term, 'sections': []}
                for section in sorted(schoolyears_data[sy][term],
                                      cmp=self.sortByCourseAndSection,
                                      key=sortingKey):
                    section_info = {'obj': section,
                                    'title': '%s -- %s' % \
                                    (', '.join(course.title
                                               for course in section.courses),
                                     section.title)}
                    term_info['sections'].append(section_info)
                sy_info['terms'].append(term_info)
            result.append(sy_info)
        return result

    def sortByCourseAndSection(self, this, other):
        if this['course'] is other['course']:
            return self.collator.cmp(this['section_title'],
                                     other['section_title'])
        return self.collator.cmp(this['course'], other['course'])


class FlourishCoursesViewlet(Viewlet, ActiveSchoolYearContentMixin):
    """A flourish viewlet showing the courses a person is in."""

    template = ViewPageTemplateFile('templates/f_coursesviewlet.pt')
    render = lambda self, *a, **kw: self.template(*a, **kw)

    def __init__(self, *args, **kw):
        super(FlourishCoursesViewlet, self).__init__(*args, **kw)
        self.collator = ICollator(self.request.locale)

    def update(self):
        self.instructorOf = self.sectionsAsTeacher()
        self.learnerOf = self.sectionsAsLearner()

    def inTeachersGroup(self):
        if self.active_schoolyear is not None:
            group = IGroupContainer(self.active_schoolyear)['teachers']
            return self.context in group.members

    def inStudentsGroup(self):
        if self.active_schoolyear is not None:
            group = IGroupContainer(self.active_schoolyear)['students']
            return self.context in group.members

    def isTeacher(self):
        """Find out if the person is an instructor for any sections."""
        return bool(self.instructorOf)

    def isLearner(self):
        """Find out if the person is a member of any sections."""
        return bool(self.learnerOf)

    def sectionsAsTeacher(self):
        """Get the sections the person instructs."""
        app_states = self.app_states('section-instruction')
        relationships = Instruction.bind(instructor=self.context).all().relationships
        return self.sectionsAs(app_states, relationships)

    def sectionsAsLearner(self):
        """Get the sections the person is a member of."""
        app_states = self.app_states('section-membership')
        relationships = Membership.bind(member=self.context).all().relationships
        return self.sectionsAs(app_states, relationships)

    def sectionsAs(self, app_states, relationships):
        schoolyears_data = {}
        for link_info in relationships:
            if not ISection.providedBy(link_info.target):
                continue
            section = removeSecurityProxy(link_info.target)
            sy = ISchoolYear(section)
            if sy not in schoolyears_data:
                schoolyears_data[sy] = {}
            term = ITerm(section)
            if term not in schoolyears_data[sy]:
                schoolyears_data[sy][term] = []
            schoolyears_data[sy][term].append((section, link_info))
        result = []
        for sy in sorted(schoolyears_data, key=lambda x:x.first):
            sy_info = {
                'obj': sy,
                'css_class': 'active' if sy is self.schoolyear else 'inactive',
                'terms': [],
                }
            for term in sorted(schoolyears_data[sy],
                               key=lambda x:x.first):
                is_active = term == getUtility(IDateManager).current_term
                term_info = {
                    'obj': term,
                    'sections': [],
                    'css_class': 'active' if is_active else 'inactive',
                }
                for section, link_info in sorted(schoolyears_data[sy][term],
                                                 key=self.sortingKey):
                    states = self.section_current_states(
                        section, app_states, link_info)
                    section_info = {
                        'obj': section,
                        'title': section.title,
                        'states': states,
                        }
                    term_info['sections'].append(section_info)
                sy_info['terms'].append(term_info)
            result.append(sy_info)
        return result

    def sortingKey(self, t):
        section, link = t
        course_title = ', '.join([c.title for c in section.courses])
        return (self.collator.key(course_title),
                self.collator.key(section.title))

    def app_states(self, key):
        app = ISchoolToolApplication(None)
        states = IRelationshipStateContainer(app)[key]
        return states

    def section_current_states(self, section, app_states, link_info):
        states = []
        for date, active, code in link_info.state.all():
            state = app_states.states.get(code)
            title = state.title if state is not None else ''
            states.append({
                'date': date,
                'title': title,
                })
        return states

    @property
    def canModify(self):
        return canAccess(self.context.__parent__, '__delitem__')


class FlourishCompletedCoursesViewlet(Viewlet, ActiveSchoolYearContentMixin):
    """A flourish viewlet showing the courses a person completed."""

    template = ViewPageTemplateFile('templates/f_completedcoursesviewlet.pt')
    body_template = None

    def __init__(self, *args, **kw):
        Viewlet.__init__(self, *args, **kw)
        self.collator = ICollator(self.request.locale)

    def render(self, *args, **kw):
        if not self.courses:
            return ''
        return self.template(*args, **kw)

    def update(self):
        self.courses = self.collectCourses()

    @property
    def completed_state_codes(self):
        app = ISchoolToolApplication(None)
        states = IRelationshipStateContainer(app)['section-membership']
        codes = [state.code for state in states
                 if states.overlap(COMPLETED, state.active)]
        return codes

    def collectCourses(self):
        today = self.request.util.today
        student=removeSecurityProxy(self.context)
        codes = self.completed_state_codes
        completed_sections = [
            relationship.target
            for relationship in Membership.relationships(member=student)
            if relationship.state.has(today, codes) and
            ISection.providedBy(relationship.target)
            ]
        schoolyears_data = {}
        for section in completed_sections:
            section = removeSecurityProxy(section)
            sy = ISchoolYear(section)
            if sy not in schoolyears_data:
                schoolyears_data[sy] = {}
            term = ITerm(section)
            if term not in schoolyears_data[sy]:
                schoolyears_data[sy][term] = []
            schoolyears_data[sy][term].extend(section.courses)
        result = []
        sortingKey = lambda course: self.collator.key(course.title)
        for sy in sorted(schoolyears_data, key=lambda x:x.first, reverse=True):
            sy_info = {
                'obj': sy,
                'css_class': 'active' if sy is self.schoolyear else 'inactive',
                'terms': [],
                }
            for term in sorted(schoolyears_data[sy],
                               key=lambda x:x.first,
                               reverse=True):
                term_info = {'obj': term, 'courses': []}
                for course in sorted(schoolyears_data[sy][term],
                                     key=sortingKey):
                    course_info = {
                        'obj': course,
                        'title': course.title,
                        }
                    term_info['courses'].append(course_info)
                sy_info['terms'].append(term_info)
            result.append(sy_info)
        return result


class CoursesTertiaryNavigationManager(TertiaryNavigationManager,
                                       ActiveSchoolYearContentMixin):

    template = InlineViewPageTemplate("""
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
                'courses',
                schoolyear.__name__)
            result.append({
                    'class': schoolyear.first == active.first and 'active' or None,
                    'viewlet': u'<a href="%s">%s</a>' % (url, schoolyear.title),
                    })
        return result


class CoursesActiveTabRefineLinksViewlet(RefineLinksViewlet,
                                         ActiveSchoolYearContentMixin):

    def __init__(self, context, request, view, manager):
        courses = self.getCourseContainer(context, request)
        RefineLinksViewlet.__init__(self, courses, request, view, manager)

    @classmethod
    def getCourseContainer(cls, context, request):
        courses = ICourseContainer(cls.schoolyear, context)
        return courses


class CoursesAddLinks(CoursesActiveTabRefineLinksViewlet):
    """Manager for Add links in CoursesView"""


class CoursesImportLinks(CoursesActiveTabRefineLinksViewlet):
    """Course import links viewlet."""


class CourseAddLinks(CoursesActiveTabRefineLinksViewlet):
    """Manager for Add links in CourseView"""

    def render(self):
        # This check is necessary because the user can be a leader
        # of the context course, which gives him schooltool.edit on it
        if canAccess(self.context.__parent__, '__delitem__'):
            return super(CourseAddLinks, self).render()


class CourseActionsLinks(RefineLinksViewlet):
    """Manager for Action links in CourseView"""

    def render(self):
        # This check is necessary because the user can be a leader
        # of the context course, which gives him schooltool.edit on it
        if canAccess(self.context.__parent__, '__delitem__'):
            return super(CourseActionsLinks, self).render()


class CourseDeleteLink(ModalFormLinkViewlet):

    @property
    def enabled(self):
        if not flourish.canDelete(self.context):
            return False
        return super(CourseDeleteLink, self).enabled

    @property
    def dialog_title(self):
        title = _(u'Delete ${course}',
                  mapping={'course': self.context.title})
        return translate(title, context=self.request)


class CourseAddLinkViewlet(LinkViewlet, ActiveSchoolYearContentMixin):

    @property
    def url(self):
        courses = ICourseContainer(self.schoolyear)
        return '%s/%s' % (absoluteURL(courses, self.request),
                          'addSchoolToolCourse.html')


class CourseAddLinkFromCourseViewlet(CourseAddLinkViewlet):

    @property
    def schoolyear(self):
        return ISchoolYear(self.context)

    @property
    def url(self):
        courses = ICourseContainer(self.schoolyear)
        return '%s/%s?camefrom=%s' % (
            absoluteURL(courses, self.request),
            'addSchoolToolCourse.html',
            absoluteURL(self.context, self.request))


class FlourishCoursesView(table.table.TableContainerView,
                          ActiveSchoolYearContentMixin):

    content_template = InlineViewPageTemplate('''
      <div>
        <tal:block content="structure view/container/schooltool:content/ajax/table" />
      </div>
    ''')

    @property
    def title(self):
        schoolyear = self.schoolyear
        return _('Courses for ${schoolyear}',
                 mapping={'schoolyear': schoolyear.title})

    @property
    def container(self):
        schoolyear = self.schoolyear
        return ICourseContainer(schoolyear)


def getCoursesTable(context, request, view, manager):
    container = view.container
    table = queryMultiAdapter(
        (container, request, view, manager),
        flourish.interfaces.IViewlet,
        'table')
    return table


def get_course_position(course, f):
    if not ICourse.providedBy(course):
        course = table.column.unindex(course)
    return course.__parent__._order.index(course.__name__)


class CoursesTableBase(table.ajax.IndexedTable):

    visible_column_names = ['title', 'course_id']

    def columns(self):
        position = GetterColumn(
            name='position',
            title=u'Position',
            getter=get_course_position,
            subsort=True)
        title = table.column.IndexedLocaleAwareGetterColumn(
            index='title',
            name='title',
            title=_(u'Title'),
            getter=lambda i, f: i.title,
            cell_formatter=table.table.url_cell_formatter,
            subsort=True)
        course_id = table.column.IndexedLocaleAwareGetterColumn(
            index='course_id',
            name='course_id',
            title=_('Course ID'),
            getter=lambda i, f: i.course_id or '',
            subsort=True)
        return [position, title, course_id]

    def sortOn(self):
        return (('position', False),)


class CoursesTable(CoursesTableBase):

    pass


class CourseListTable(CoursesTableBase):

    @property
    def source(self):
        schoolyear = ISchoolYear(self.context)
        return ICourseContainer(schoolyear)


class CourseTableSchoolYear(flourish.viewlet.Viewlet):
    template = InlineViewPageTemplate('''
      <input type="hidden" name="schoolyear_id"
             tal:define="schoolyear_id view/view/schoolyear/__name__|nothing"
             tal:condition="schoolyear_id"
             tal:attributes="value schoolyear_id" />
    ''')


class CourseTableDoneLink(flourish.viewlet.Viewlet):
    template = InlineViewPageTemplate('''
      <h3 tal:define="can_manage context/schooltool:app/schooltool:can_edit"
          class="done-link" i18n:domain="schooltool">
        <tal:block condition="can_manage">
          <a tal:attributes="href string:${context/schooltool:app/@@absolute_url}/manage"
             i18n:translate="">Done</a>
        </tal:block>
        <tal:block condition="not:can_manage">
          <a tal:attributes="href request/principal/schooltool:person/@@absolute_url"
             i18n:translate="">Done</a>
        </tal:block>
      </h3>
      ''')


class CourseContainerTitle(ContentTitle):

    @property
    def title(self):
        schoolyear = ISchoolYear(self.context)
        return _('Courses for ${schoolyear}',
                 mapping={'schoolyear': schoolyear.title})


class FlourishCourseContainerDeleteView(ContainerDeleteView):

    def nextURL(self):
        if 'CONFIRM' in self.request:
            schoolyear = ISchoolYear(self.context)
            params = {'schoolyear_id': schoolyear.__name__.encode('utf-8')}
            url = '%s/courses?%s' % (
                absoluteURL(ISchoolToolApplication(None), self.request),
                urlencode(params))
            return url
        return ContainerDeleteView.nextURL(self)


class ICourseLevel(Interface):

    level = Choice(
        title=_('Grade Level'),
        vocabulary='schooltool.level.level.levelvocabulary',
        required=False)


class CourseLevelFormAdapter(object):

    adapts(ICourse)
    implements(ICourseLevel)

    def __init__(self, context):
        self.__dict__['context'] = removeSecurityProxy(context)

    def __getattr__(self, name):
        if name == 'level':
            if self.context.levels:
                return list(self.context.levels)[0]

    def __setattr__(self, name, value):
        if name == 'level':
            value = removeSecurityProxy(value)
            current = None
            if self.context.levels:
                current = list(self.context.levels)[0]
            if value != current:
                if current is not None:
                    self.context.levels.remove(current)
                if value is not None:
                    self.context.levels.add(value)


class FlourishCourseView(DisplayForm):

    template = InheritTemplate(Page.template)
    content_template = ViewPageTemplateFile('templates/f_course_view.pt')

    @property
    def fields(self):
        fields = field.Fields(ICourse)
        fields += field.Fields(ICourseLevel)
        fields = fields.select('__name__', 'title', 'description', 'course_id', 'government_id', 'credits', 'level')
        return fields

    @property
    def sections(self):
        return list(removeSecurityProxy(self.context).sections)

    @property
    def unproxied_course(self):
        return removeSecurityProxy(self.context)

    @property
    def canModify(self):
        return checkPermission('schooltool.edit', self.context)

    @property
    def title(self):
        schoolyear = ISchoolYear(self.context.__parent__)
        return _('Courses for ${schoolyear}',
                 mapping={'schoolyear': schoolyear.title})

    @property
    def subtitle(self):
        return self.context.title

    def done_link(self):
        schoolyear = ISchoolYear(self.context.__parent__)
        url = '%s/%s?schoolyear_id=%s' % (
            absoluteURL(ISchoolToolApplication(None), self.request),
            'courses',
            schoolyear.__name__)
        return url

    def updateWidgets(self):
        super(FlourishCourseView, self).updateWidgets()
        for widget in self.widgets.values():
            if not widget.value:
                widget.mode = HIDDEN_MODE

    def has_leaders(self):
        return bool(list(self.context.leaders))


class FlourishCourseViewDoneLink(flourish.viewlet.Viewlet):

    template = InlineViewPageTemplate('''
    <h3 class="done-link" i18n:domain="schooltool">
      <a tal:attributes="href view/view/done_link"
         i18n:translate="">Done</a>
    </h3>
    ''')


class FlourishCourseAddView(AddForm, ActiveSchoolYearContentMixin):

    template = InheritTemplate(Page.template)
    label = None
    legend = _('Course Information')

    @property
    def fields(self):
        fields = field.Fields(ICourse)
        fields += field.Fields(ICourseLevel)
        fields = fields.select('title', 'description', 'course_id', 'government_id', 'credits', 'level')
        return fields

    def updateActions(self):
        super(FlourishCourseAddView, self).updateActions()
        self.actions['add'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    @button.buttonAndHandler(_('Submit'), name='add')
    def handleAdd(self, action):
        super(FlourishCourseAddView, self).handleAdd.func(self, action)

    @button.buttonAndHandler(_('Cancel'))
    def handle_cancel_action(self, action):
        if 'camefrom' in self.request:
            url = self.request['camefrom']
            self.request.response.redirect(url)
            return
        app = ISchoolToolApplication(None)
        url = self.url_with_schoolyear_id(app, view_name='courses')
        self.request.response.redirect(url)

    def create(self, data):
        course = Course(data['title'], data.get('description'))
        self._level = removeSecurityProxy(data.pop('level'))
        form.applyChanges(self, course, data)
        return course

    def add(self, course):
        chooser = INameChooser(self.context)
        name = chooser.chooseName(u'', course)
        self.context[name] = course
        self._course = course
        if self._level is not None:
            self._level.courses.add(course)
        return course

    def nextURL(self):
        return absoluteURL(self._course, self.request)

    @property
    def schoolyear(self):
        return ISchoolYear(self.context)

    @property
    def title(self):
        return _('Courses for ${schoolyear}',
                 mapping={'schoolyear': self.schoolyear.title})


class FlourishCourseEditView(Form, form.EditForm):

    template = InheritTemplate(Page.template)
    label = None
    legend = _('Course Information')

    @property
    def fields(self):
        fields = field.Fields(ICourse)
        fields += field.Fields(ICourseLevel)
        fields = fields.select('title', 'description', 'course_id', 'government_id', 'credits', 'level')
        return fields

    @property
    def title(self):
        return self.context.title

    def update(self):
        return form.EditForm.update(self)

    def updateActions(self):
        super(FlourishCourseEditView, self).updateActions()
        self.actions['apply'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    @button.buttonAndHandler(_('Submit'), name='apply')
    def handleApply(self, action):
        super(FlourishCourseEditView, self).handleApply.func(self, action)
        # XXX: hacky sucessful submit check
        if (self.status == self.successMessage or
            self.status == self.noChangesMessage):
            url = absoluteURL(self.context, self.request)
            self.request.response.redirect(url)

    @button.buttonAndHandler(_("Cancel"))
    def handle_cancel_action(self, action):
        url = absoluteURL(self.context, self.request)
        self.request.response.redirect(url)


class FlourishCourseDeleteView(DialogForm, form.EditForm):
    """View used for confirming deletion of a course."""

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
        super(FlourishCourseDeleteView, self).updateActions()
        self.actions['apply'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')


class CoursesTableFilter(table.ajax.IndexedTableFilter):

    template = ViewPageTemplateFile('templates/f_course_table_filter.pt')

    title = _("Title or course ID")

    @property
    def search_id(self):
        return self.manager.html_id+'-search'

    @property
    def search_title_id(self):
        return self.manager.html_id+"-title"

    @property
    def search_level_id(self):
        return self.manager.html_id+"-level"

    def levelContainer(self):
        app = ISchoolToolApplication(None)
        return ILevelContainer(app)

    def levels(self):
        result = []
        container = self.levelContainer()
        for level_id, level in container.items():
            result.append({'id': level_id,
                           'title': level.title})
        return result

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
            level_id = self.request.get(self.search_level_id)
            level = self.levelContainer().get(level_id)
            if level:
                # XXX: create set index for course levels
                items = [item for item in items
                         if level in table.column.unindex(item).levels]
        return self.query(items, params)


class FlourishManageCoursesOverview(ContainerSearchContent):

    add_view_name = 'addSchoolToolCourse.html'
    hint = _('Manage courses')
    title = _('Courses')
    css_class = 'content manage-courses-overview'

    @property
    def container(self):
        return ICourseContainer(self.schoolyear, None)

    def container_url(self):
        return self.url_with_schoolyear_id(self.context, view_name='courses')

    @property
    def json_url(self):
        app = ISchoolToolApplication(None)
        return '%s/courses_json' % absoluteURL(app, self.request)


class CourseListTableFilter(table.ajax.IndexedTableFilter):

    def filter(self, items):
        int_ids = getUtility(IIntIds)
        course_ids = [int_ids.getId(course) for course in self.context.courses]
        return [item for item in items if item['id'] in course_ids]

    def render(self, *args, **kw):
        return ''


class CoursesJSONSearchView(JSONSearchViewBase,
                            ActiveSchoolYearContentMixin):

    @Lazy
    def container(self):
        return ICourseContainer(self.schoolyear)

    @property
    def catalog(self):
        return ICatalog(self.container)

    @property
    def items(self):
        if self.text_query:
            container_id = getUtility(IIntIds).getId(self.container)
            container_query = {'any_of': [container_id]}
            params = {
                'text': self.text_query,
                'container_id': container_query,
            }
            return self.catalog.searchResults(**params)
        return []

    def encode(self, course):
        label = course.title
        return {
            'label': label,
            'value': label,
            'url': absoluteURL(course, self.request),
        }


class CoursesActionsLinks(flourish.page.RefineLinksViewlet):

    pass


class CoursesReorderLinkViewlet(flourish.page.LinkViewlet,
                                ActiveSchoolYearContentMixin):

    @property
    def url(self):
        courses = ICourseContainer(self.schoolyear)
        return '%s/reorder.html' % absoluteURL(courses, self.request)


class CoursesReorderView(flourish.page.Page,
                         ActiveSchoolYearContentMixin):

    @Lazy
    def schoolyear(self):
        return ISchoolYear(self.context)

    @property
    def title(self):
        return _('Courses for ${schoolyear}',
                 mapping={'schoolyear': self.schoolyear.title})

    def done_url(self):
        app = ISchoolToolApplication(None)
        return self.url_with_schoolyear_id(app, view_name='courses')

    @Lazy
    def courses(self):
        result = []
        for i, course in enumerate(self.context.values()):
            result.append({
                'pos': i + 1,
                '__name__': course.__name__,
                'title': course.title,
                'course_id': course.course_id,
            })
        return result

    def positions(self):
        return range(1, len(self.context.values())+1)

    def update(self):
        if 'DONE' in self.request:
            url = absoluteURL(self.context, self.request)
            self.request.response.redirect(url)
        elif 'form-submitted' in self.request:
            for course in self.context.values():
                name = 'delete.%s' % course.__name__
                if name in self.request:
                    del self.context[course.__name__]
                    return
            old_pos, new_pos = 0, 0
            for course in self.context.values():
                old_pos += 1
                name = course.__name__
                if 'pos.'+name not in self.request:
                    continue
                new_pos = int(self.request['pos.'+name])
                if new_pos != old_pos:
                    break
            old_pos, new_pos = old_pos-1, new_pos-1
            keys = list(self.context.keys())
            moving = keys[old_pos]
            keys.remove(moving)
            keys.insert(new_pos,moving)
            self.context.updateOrder(keys)
