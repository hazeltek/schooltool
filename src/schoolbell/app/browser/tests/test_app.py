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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
Tests for schoolbell views.

$Id$
"""

import unittest
from pprint import pprint
from zope.testing import doctest
from zope.app import zapi
from zope.app.testing import setup, ztapi
from zope.interface import directlyProvides
from zope.app.traversing.interfaces import IContainmentRoot
from zope.publisher.browser import TestRequest
from zope.app.pagetemplate.simpleviewclass import SimpleViewClass


def doctest_PersonView():
    r"""Test for PersonView

    Let's create a view for a person:

        >>> from schoolbell.app.browser.app import PersonView
        >>> from schoolbell.app.app import Person
        >>> person = Person()
        >>> request = TestRequest()
        >>> view = PersonView(person, request)

    TODO: implement proper permission checking.
    For now, all these methods just return True

        >>> view.canEdit()
        True
        >>> view.canChangePassword()
        True
        >>> view.canViewCalendar()
        True
        >>> view.canChooseCalendars()
        True

    """


def doctest_PersonPhotoView():
    r"""Test for PersonPhotoView

    We will need a person that has a photo:

        >>> from schoolbell.app.app import Person
        >>> person = Person()
        >>> person.photo = "I am a photo!"

    We can now create a view:

        >>> from schoolbell.app.browser.app import PersonPhotoView
        >>> request = TestRequest()
        >>> view = PersonPhotoView(person, request)

    The view returns the photo and sets the appropriate Content-Type header:

        >>> view()
        'I am a photo!'
        >>> request.response.getHeader("Content-Type")
        'image/jpeg'

    However, if a person has no photo, the view raises a NotFound error.

        >>> person.photo = None
        >>> view()                                  # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        NotFound: Object: <...Person object at ...>, name: u'photo'

    """


def doctest_GroupListView():
    r"""Test for GroupListView

    We will need a volunteer for this test:

        >>> from schoolbell.app.app import Person
        >>> person = Person(u'ignas')

    One requirement: the person has to know where he is.

        >>> from schoolbell.app.app import SchoolBellApplication
        >>> app = SchoolBellApplication()
        >>> directlyProvides(app, IContainmentRoot)
        >>> app['persons']['ignas'] = person

    We will be testing the person's awareness of the world, so we will
    create some (empty) groups.

        >>> from schoolbell.app.app import Group
        >>> world = app['groups']['the_world'] = Group("Others")
        >>> etria = app['groups']['etria'] = Group("Etria")
        >>> pov = app['groups']['pov'] = Group("PoV")

    Let's create a view for a person:

        >>> from schoolbell.app.browser.app import GroupListView
        >>> request = TestRequest()
        >>> view = GroupListView(person, request)

    Rendering the view does no harm:

        >>> view.update()

    First, all groups should be listed:

        >>> group_titles = [g.title for g in view.getAllGroups()]
        >>> group_titles.sort()
        >>> group_titles
        ['Etria', 'Others', 'PoV']

    Let's tell the person to join PoV:

        >>> request = TestRequest()
        >>> request.form = {'group.pov': 'on', 'UPDATE_SUBMIT': 'Apply'}
        >>> view = GroupListView(person, request)
        >>> view.update()

    He should have joined:

        >>> [group.title for group in person.groups]
        ['PoV']

    And we should be directed to the person info page:

        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1/persons/ignas'

    Had we decided to make the guy join Etria but then changed our mind:

        >>> request = TestRequest()
        >>> request.form = {'group.pov': 'on', 'group.etria': 'on',
        ...                 'CANCEL': 'Cancel'}
        >>> view = GroupListView(person, request)
        >>> view.update()

    Nothing would have happened!

        >>> [group.title for group in person.groups]
        ['PoV']

    Yet we would find ourselves in the person info page:

        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1/persons/ignas'

    Finally, let's remove him out of PoV for a weekend and add him
    to The World.

        >>> request = TestRequest()
        >>> request.form = {'group.the_world': 'on', 'UPDATE_SUBMIT': 'Apply'}
        >>> view = GroupListView(person, request)
        >>> view.update()

    Mission successful:

        >>> [group.title for group in person.groups]
        ['Others']

    Yadda yadda, redirection works:

        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1/persons/ignas'

    """


def doctest_MemberListView():
    r"""Test for MemberListView

    We will be (ab)using a group and three test subjects:

        >>> from schoolbell.app.app import Group
        >>> pov = Group('PoV')

        >>> from schoolbell.app.app import Person
        >>> gintas = Person('gintas', 'Gintas')
        >>> ignas = Person('ignas', 'Ignas')
        >>> alga = Person('alga', 'Albertas')

    We need these objects to live in an application:

        >>> from schoolbell.app.app import SchoolBellApplication
        >>> app = SchoolBellApplication()
        >>> directlyProvides(app, IContainmentRoot)
        >>> app['groups']['pov'] = pov
        >>> app['persons']['gintas'] = gintas
        >>> app['persons']['ignas'] = ignas
        >>> app['persons']['alga'] = alga

    Let's create a view for our group:

        >>> from schoolbell.app.browser.app import MemberViewPersons
        >>> request = TestRequest()
        >>> view = MemberViewPersons(pov, request)

    Rendering the view does no harm:

        >>> view.update()

    First, all persons should be listed in alphabetical order:

        >>> [g.title for g in view.getPotentialMembers()]
        ['Albertas', 'Gintas', 'Ignas']

    Let's make Ignas a member of PoV:

        >>> request = TestRequest()
        >>> request.form = {'member.ignas': 'on', 'UPDATE_SUBMIT': 'Apply'}
        >>> view = MemberViewPersons(pov, request)
        >>> view.update()

    He should have joined:

        >>> [person.title for person in pov.members]
        ['Ignas']

    And we should be directed to the group info page:

        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1/groups/pov'

    We can cancel an action if we want to:

        >>> request = TestRequest()
        >>> request.form = {'member.gintas': 'on', 'CANCEL': 'Cancel'}
        >>> view = MemberViewPersons(pov, request)
        >>> view.update()
        >>> [person.title for person in pov.members]
        ['Ignas']
        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1/groups/pov'

    Finally, let's remove Ignas from PoV (he went home early today)
    and add Albert, who came in late and has to work after-hours:

        >>> request = TestRequest()
        >>> request.form = {'member.alga': 'on', 'UPDATE_SUBMIT': 'Apply'}
        >>> view = MemberViewPersons(pov, request)
        >>> view.update()

    Mission accomplished:

        >>> [person.title for person in pov.members]
        ['Albertas']

    Yadda yadda, redirection works:

        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1/groups/pov'

    TODO: check resource view

    """


def doctest_GroupView():
    r"""Test for GroupView

    Let's create a view for a group:

        >>> from schoolbell.app.browser.app import GroupView
        >>> from schoolbell.app.app import Group
        >>> group = Group()
        >>> request = TestRequest()
        >>> view = GroupView(group, request)

    Let's relate some objects to our group:

        >>> from schoolbell.app.app import Person, Resource
        >>> group.members.add(Person(title='First'))
        >>> group.members.add(Person(title='Last'))
        >>> group.members.add(Person(title='Intermediate'))
        >>> group.members.add(Resource(title='Average'))
        >>> group.members.add(Resource(title='Another'))
        >>> group.members.add(Resource(title='The last'))

    A person list from that view should be sorted by title.

        >>> titles = [person.title for person in view.getPersons()]
        >>> titles.sort()
        >>> titles
        ['First', 'Intermediate', 'Last']

    Same for the resource list.

        >>> titles = [resource.title for resource in view.getResources()]
        >>> titles.sort()
        >>> titles
        ['Another', 'Average', 'The last']


    TODO: implement proper permission checking.
    For now, all these methods just return True

        >>> view.canEdit()
        True

    """


def doctest_GroupAddView():
    r"""Test for GroupAddView

    Adding views in Zope 3 are somewhat unobvious.  The context of an adding
    view is a view named '+' and providing IAdding.

        >>> class AddingStub:
        ...     pass
        >>> context = AddingStub()

    The container to which items will actually be added is accessible as the
    `context` attribute

        >>> from schoolbell.app.app import GroupContainer
        >>> container = GroupContainer()
        >>> context.context = container

    ZCML configuration adds some attributes to GroupAddView, namely `schema`
    and `_factory`.

        >>> from schoolbell.app.browser.app import GroupAddView
        >>> from schoolbell.app.interfaces import IGroup
        >>> from schoolbell.app.app import Group
        >>> class GroupAddViewForTesting(GroupAddView):
        ...     schema = IGroup
        ...     _factory = Group

    We can now finally create the view:

        >>> request = TestRequest()
        >>> view = GroupAddViewForTesting(context, request)

    The `nextURL` method tells Zope 3 where you should be redirected after
    successfully adding a group.  We will pretend that `container` is located
    at the root so that zapi.absoluteURL(container) returns 'http://127.0.0.1'.

        >>> directlyProvides(container, IContainmentRoot)
        >>> view.nextURL()
        'http://127.0.0.1'

    We can cancel an action if we want to:

        >>> request = TestRequest()
        >>> request.form = {'CANCEL': 'Cancel'}
        >>> view = GroupAddViewForTesting(context, request)
        >>> view.update()
        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1'

    If 'CANCEL' is not present in the request, the view calls inherited
    'update'.  We will use a trick and set update_status to some value to
    short-circuit AddView.update().

        >>> request = TestRequest()
        >>> request.form = {'field.title': 'a_group',
        ...                 'UPDATE_SUBMIT': 'Add'}
        >>> view = GroupAddViewForTesting(context, request)
        >>> view.update_status = 'Just checking'
        >>> view.update()
        'Just checking'

    """


def doctest_GroupEditView():
    r"""Test for GroupEditView

    Let's create a view for editing a group:

        >>> from schoolbell.app.browser.app import GroupEditView
        >>> from schoolbell.app.app import Group
        >>> from schoolbell.app.interfaces import IGroup
        >>> group = Group()
        >>> directlyProvides(group, IContainmentRoot)
        >>> request = TestRequest()

        >>> class TestGroupEditView(GroupEditView):
        ...     schema = IGroup
        ...     _factory = Group

        >>> view = TestGroupEditView(group, request)

    We should not get redirected if we did not click on apply button:

        >>> request = TestRequest()
        >>> view = TestGroupEditView(group, request)
        >>> view.update()
        ''
        >>> request.response.getStatus()
        599

    After changing name of the group you should get redirected to the group
    list:

        >>> request = TestRequest()
        >>> request.form = {'UPDATE_SUBMIT': 'Apply',
        ...                 'field.title': u'new_title'}
        >>> view = TestGroupEditView(group, request)
        >>> view.update()
        u'Updated on ${date_time}'
        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1'

        >>> group.title
        u'new_title'

    Even if the title has not changed you should get redirected to the group
    list:

        >>> request = TestRequest()
        >>> request.form = {'UPDATE_SUBMIT': 'Apply',
        ...                 'field.title': u'new_title'}
        >>> view = TestGroupEditView(group, request)
        >>> view.update()
        ''
        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1'

        >>> group.title
        u'new_title'

    We should not get redirected if there were errors:

        >>> request = TestRequest()
        >>> request.form = {'UPDATE_SUBMIT': 'Apply',
        ...                 'field.title': u''}
        >>> view = TestGroupEditView(group, request)
        >>> view.update()
        u'An error occured.'
        >>> request.response.getStatus()
        599

        >>> group.title
        u'new_title'

    We can cancel an action if we want to:

        >>> request = TestRequest()
        >>> request.form = {'CANCEL': 'Cancel'}
        >>> view = TestGroupEditView(group, request)
        >>> view.update()
        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1'

    """


def doctest_ResourceView():
    r"""Test for ResourceView

    Let's create a view for a resource:

        >>> from schoolbell.app.browser.app import ResourceView
        >>> from schoolbell.app.app import Resource
        >>> resource = Resource()
        >>> request = TestRequest()
        >>> view = ResourceView(resource, request)

    TODO: implement proper permission checking.
    For now, all these methods just return True

        >>> view.canEdit()
        True

    """


def doctest_PersonEditView():
    r"""Test for PersonEditView

    PersonEditView is a view on IPerson.

        >>> from schoolbell.app.browser.app import PersonEditView
        >>> from schoolbell.app.app import Person
        >>> person = Person()

    Let's try creating one

        >>> request = TestRequest()
        >>> view = PersonEditView(person, request)

    You can change person's title and photo

        >>> request = TestRequest(form={'UPDATE_SUBMIT': True,
        ...                             'field.title': u'newTitle',
        ...                             'field.photo': 'PHOTO'})
        >>> view = PersonEditView(person, request)

        >>> view.update()
        >>> view.message
        >>> person.title
        u'newTitle'
        >>> person.photo
        'PHOTO'

    You can clear the person's photo:
        >>> request = TestRequest(form={'UPDATE_SUBMIT': True,
        ...                             'field.title':u'newTitle',
        ...                             'field.clear_photo':'on'})
        >>> view = PersonEditView(person, request)

        >>> view.update()
        >>> view.message
        >>> person.title
        u'newTitle'
        >>> print person.photo
        None

    You can set a person's password

        >>> person.setPassword('lala')
        >>> request = TestRequest(form={'UPDATE_SUBMIT': True,
        ...                             'field.title': person.title,
        ...                             'field.new_password': 'bar',
        ...                             'field.verify_password': 'bar'})
        >>> view = PersonEditView(person, request)

        >>> view.update()
        >>> view.message
        u'Password was successfully changed!'
        >>> person.checkPassword('bar')
        True

    Unless new password and confirm password do not match

        >>> person.setPassword('lala')
        >>> request = TestRequest(form={'UPDATE_SUBMIT': True,
        ...                             'field.title': person.title,
        ...                             'field.new_password': 'bara',
        ...                             'field.verify_password': 'bar'})
        >>> view = PersonEditView(person, request)

        >>> view.update()
        >>> view.error
        u'Passwords do not match.'

    If the form contains errors, it is redisplayed

        >>> request = TestRequest(form={'UPDATE_SUBMIT': True,
        ...                             'field.title': '',
        ...                             'field.new_password': 'xyzzy',
        ...                             'field.verify_password': 'xyzzy'})
        >>> view = PersonEditView(person, request)

        >>> view.update()
        >>> person.title
        u'newTitle'

        >>> bool(view.title_widget.error())
        True

    We can cancel an action if we want to:

        >>> directlyProvides(person, IContainmentRoot)
        >>> request = TestRequest()
        >>> request.form = {'CANCEL': 'Cancel'}
        >>> view = PersonEditView(person, request)
        >>> view.update()
        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1'

    """


def doctest_PersonAddView():
    r"""Test for PersonAddView

    We need some setup to make traversal work in a unit test.

        >>> class FakeURL:
        ...     def __init__(self, context, request): pass
        ...     def __call__(self): return "http://localhost/frogpond/persons"
        ...
        >>> from schoolbell.app.interfaces import IPersonContainer
        >>> from zope.app.traversing.browser.interfaces import IAbsoluteURL
        >>> ztapi.browserViewProviding(IPersonContainer, FakeURL, \
        ...                            providing=IAbsoluteURL)

    Let's create a PersonContainer

        >>> from schoolbell.app.app import SchoolBellApplication
        >>> app = SchoolBellApplication()
        >>> pc = app['persons']

    Now let's create a PersonAddView for the container

        >>> from schoolbell.app.browser.app import PersonAddView
        >>> view = PersonAddView(pc, TestRequest())
        >>> view.update()

    Let's try to add a user:

        >>> request = TestRequest(form={'field.title': u'John Doe',
        ...                             'field.username': u'jdoe',
        ...                             'field.password': u'secret',
        ...                             'field.verify_password': u'secret',
        ...                             'field.photo': u'',
        ...                             'UPDATE_SUBMIT': 'Add'})
        >>> view = PersonAddView(pc, request)
        >>> view.update()
        ''
        >>> print view.errors
        ()
        >>> print view.error
        None
        >>> 'jdoe' in pc
        True
        >>> person = pc['jdoe']
        >>> person.title
        u'John Doe'
        >>> person.username
        u'jdoe'
        >>> person.checkPassword('secret')
        True
        >>> person.photo is None
        True

    If we try to add a user with the same login, we get a nice error message:

        >>> request = TestRequest(form={'field.title': u'Another John Doe',
        ...                             'field.username': u'jdoe',
        ...                             'field.password': u'pass',
        ...                             'field.verify_password': u'pass',
        ...                             'field.photo': None,
        ...                             'UPDATE_SUBMIT': 'Add'})
        >>> view = PersonAddView(pc, request)
        >>> view.update()
        u'An error occured.'
        >>> view.error
        u'This username is already used!'

    Let's try to add user with different password and verify_password fields:

        >>> request = TestRequest(form={'field.title': u'Coo Guy',
        ...                             'field.username': u'coo',
        ...                             'field.password': u'secret',
        ...                             'field.verify_password': u'plain',
        ...                             'field.photo': None,
        ...                             'UPDATE_SUBMIT': 'Add'})
        >>> view = PersonAddView(pc, request)
        >>> view.update()
        u'An error occured.'
        >>> view.error
        u'Passwords do not match!'
        >>> 'coo' in pc
        False

    We can select groups that the user should be in.  First, let's create a
    group:

        >>> from schoolbell.app.app import Group
        >>> pov = app['groups']['pov'] = Group('PoV')

    Now, let's create and render a view:

        >>> request = TestRequest(form={'field.title': u'Gintas',
        ...                             'field.username': u'gintas',
        ...                             'field.password': u'denied',
        ...                             'field.verify_password': u'denied',
        ...                             'field.photo': ':)',
        ...                             'group.pov': 'on',
        ...                             'UPDATE_SUBMIT': 'Add'})
        >>> view = PersonAddView(pc, request)
        >>> view.update()
        ''
        >>> print view.errors
        ()
        >>> print view.error
        None

        >>> pc['gintas'].photo
        ':)'

    Now the person belongs to the group that we have selected:

        >>> list(pc['gintas'].groups) == [pov]
        True

    We can cancel an action if we want to:

        >>> directlyProvides(pc, IContainmentRoot)
        >>> request = TestRequest()
        >>> request.form = {'CANCEL': 'Cancel'}
        >>> view = PersonAddView(pc, request)
        >>> view.update()
        >>> request.response.getStatus()
        302
        >>> request.response.getHeaders()['Location']
        'http://127.0.0.1/persons'

    """


def doctest_LoginView():
    """
    Suppose we have a SchoolBell app and a person:

        >>> from schoolbell.app.app import SchoolBellApplication
        >>> app = SchoolBellApplication()
        >>> directlyProvides(app, IContainmentRoot)
        >>> persons = app['persons']

        >>> from schoolbell.app.app import Person
        >>> frog = Person('frog')
        >>> persons[None] = frog
        >>> frog.setPassword('pond')

    We create our view:

        >>> from schoolbell.app.browser.app import LoginView
        >>> request = TestRequest()
        >>> class StubPrincipal:
        ...     title = "Some user"
        ...
        >>> request.setPrincipal(StubPrincipal())
        >>> View = SimpleViewClass('../templates/login.pt', bases=(LoginView,))
        >>> view = View(app, request)

    Render it with an empty request:

        >>> content = view()
        >>> '<h3>Please log in</h3>' in content
        True

    If we have authentication utility:

        >>> from schoolbell.app.security import SchoolBellAuthenticationUtility
        >>> from zope.app.security.interfaces import IAuthentication
        >>> auth = SchoolBellAuthenticationUtility()
        >>> ztapi.provideUtility(IAuthentication, auth)
        >>> auth.__parent__ = app
        >>> setUpSession()

    It does not authenticate our session:

        >>> auth.authenticate(request)

    However, if we pass valid credentials, we get authenticated:

        >>> request = TestRequest(form={'username': 'frog',
        ...                             'password': 'pond',
        ...                             'LOGIN': 'Log in'})
        >>> request.setPrincipal(StubPrincipal())
        >>> view = View(app, request)
        >>> content = view()
        >>> view.error
        >>> request.response.getStatus()
        302
        >>> url = zapi.absoluteURL(app, request)
        >>> request.response.getHeader('Location') == url
        True
        >>> auth.authenticate(request)
        <schoolbell.app.security.Principal object at 0x...>

    If we pass bad credentials, we get a nice error and a form.

        >>> request = TestRequest(form={'username': 'snake',
        ...                             'password': 'pw',
        ...                             'LOGIN': 'Log in'})
        >>> auth.setCredentials(request, 'frog', 'pond')
        >>> request.setPrincipal(auth.authenticate(request))
        >>> view = View(app, request)
        >>> content = view()
        >>> view.error
        u'Username or password is incorrect'
        >>> view.error in content
        True
        >>> 'Please log in' in content
        True

    The previous credentials are not lost if a new login fails:

        >>> principal = auth.authenticate(request)
        >>> principal
        <schoolbell.app.security.Principal object at 0x...>
        >>> principal.id
        'sb.person.frog'

    We can specify the URL we want to go to after being authenticated:

        >>> request = TestRequest(form={'username': 'frog',
        ...                             'password': 'pond',
        ...                             'nexturl': 'http://host/path',
        ...                             'LOGIN': 'Log in'})
        >>> request.setPrincipal(StubPrincipal())
        >>> view = View(app, request)
        >>> content = view()
        >>> view.error
        >>> request.response.getStatus()
        302
        >>> url = zapi.absoluteURL(app, request)
        >>> request.response.getHeader('Location')
        'http://host/path'

    """


def doctest_LogoutView():
    """
    Suppose we have a SchoolBell app and a person:

        >>> from schoolbell.app.app import SchoolBellApplication
        >>> app = SchoolBellApplication()
        >>> directlyProvides(app, IContainmentRoot)
        >>> persons = app['persons']

        >>> from schoolbell.app.app import Person
        >>> frog = Person('frog')
        >>> persons[None] = frog
        >>> frog.setPassword('pond')

    Also, we have an authentication utility:

        >>> from schoolbell.app.security import SchoolBellAuthenticationUtility
        >>> from zope.app.security.interfaces import IAuthentication
        >>> auth = SchoolBellAuthenticationUtility()
        >>> ztapi.provideUtility(IAuthentication, auth)
        >>> auth.__parent__ = app
        >>> setUpSession()

    We have a request in an authenticated session:

        >>> request = TestRequest()
        >>> auth.setCredentials(request, 'frog', 'pond')
        >>> request.setPrincipal(auth.authenticate(request))

    And we call the logout view:

        >>> from schoolbell.app.browser.app import LogoutView
        >>> view = LogoutView(app, request)
        >>> view()

    Now, the session no longer has an authenticated user:

        >>> auth.authenticate(request)

    The user gets redirected to the front page:

        >>> request.response.getStatus()
        302
        >>> url = zapi.absoluteURL(app, request)
        >>> request.response.getHeader('Location') == url
        True


    The view also doesn't fail if the user was not logged in in the
    first place:

        >>> request = TestRequest()
        >>> view = LogoutView(app, request)
        >>> view()
        >>> auth.authenticate(request)

    """

def doctest_ACLView():
    r"""
    Set up for local grants:

        >>> from zope.app.annotation.interfaces import IAnnotatable
        >>> from zope.app.securitypolicy.interfaces import \
        ...                         IPrincipalPermissionManager
        >>> from zope.app.securitypolicy.principalpermission import \
        ...                         AnnotationPrincipalPermissionManager
        >>> setup.setUpAnnotations()
        >>> setup.setUpTraversal()
        >>> ztapi.provideAdapter(IAnnotatable, IPrincipalPermissionManager,
        ...                      AnnotationPrincipalPermissionManager)

    Suppose we have a SchoolBell app:

        >>> from schoolbell.app.app import SchoolBellApplication
        >>> app = SchoolBellApplication()
        >>> directlyProvides(app, IContainmentRoot)
        >>> persons = app['persons']
        >>> from schoolbell.app.security import setUpLocalAuth
        >>> setUpLocalAuth(app)
        >>> from zope.app.component.hooks import setSite
        >>> setSite(app)

    We have a couple of persons and groups:

        >>> from schoolbell.app.app import Person, Group
        >>> app['persons']['1'] = Person('albert', title='Albert')
        >>> app['persons']['2'] = Person('marius', title='Marius')
        >>> app['groups']['3'] = Group('office')
        >>> app['groups']['4'] = Group('mgmt')

    We create an ACLView:

        >>> from schoolbell.app.browser.app import ACLView
        >>> View = SimpleViewClass("../templates/acl.pt", bases=(ACLView, ))
        >>> request = TestRequest()
        >>> class StubPrincipal:
        ...     title = "Some user"
        ...
        >>> request.setPrincipal(StubPrincipal())
        >>> view = View(app, request)

    The view has methods to list persons and groups:

        >>> pprint(view.getPersons())
        [{'perms': [], 'id': u'sb.person.albert', 'title': 'Albert'},
         {'perms': [], 'id': u'sb.person.marius', 'title': 'Marius'}]
        >>> pprint(view.getGroups())
        [{'perms': [], 'id': u'sb.group.3', 'title': 'office'},
         {'perms': [], 'id': u'sb.group.4', 'title': 'mgmt'}]

    Also it knows a list of permissions to display:

        >>> pprint(view.permissions)
        [('zope.View', u'View'),
         ('zope.ManageContent', u'Manage'),
         ('zope.ManageSite', u'Manage Site')]

    The view displays a matrix with groups and persons as rows and
    permisssions as columns:

        >>> print view()
        <BLANKLINE>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        ...
        <form method="POST" class="standalone"
              action="http://127.0.0.1">
          <fieldset>
            <legend>Permissions</legend>
            <table class="acl">
              <tr>
                 <th>User/Group</th>
                 <th>View</th>
                 <th>Manage</th>
                 <th>Manage Site</th>
              </tr>
              <tr>
                 <th>office</th>
                 <td>
                    <input type="checkbox" name="sb.group.3"
                           value="zope.View" />
                 </td>
                 <td>
                    <input type="checkbox" name="sb.group.3"
                           value="zope.ManageContent" />
                 </td>
                 <td>
                    <input type="checkbox" name="sb.group.3"
                           value="zope.ManageSite" />
                 </td>
              </tr>
              ...
              <tr>
                 <th>Albert</th>
                 <td>
                    <input type="checkbox" name="sb.person.albert"
                           value="zope.View" />
                 </td>
                 <td>
                    <input type="checkbox" name="sb.person.albert"
                           value="zope.ManageContent" />
                 </td>
                 <td>
                    <input type="checkbox" name="sb.person.albert"
                           value="zope.ManageSite" />
                 </td>
              </tr>
        ...

    If we submit a form with a checkbox marked, a user gets a grant:

        >>> request = TestRequest(form={
        ...     'sb.person.albert': ['zope.ManageSite',
        ...                          'zope.ManageContent'],
        ...     'sb.person.marius': 'zope.ManageContent',
        ...     'sb.group.3': 'zope.ManageSite',
        ...     'UPDATE_SUBMIT': 'Set'})
        >>> view = View(app, request)
        >>> result = view.update()

    Now the users should have permissions on app:

        >>> grants = IPrincipalPermissionManager(app)
        >>> grants.getPermissionsForPrincipal('sb.person.marius')
        [('zope.ManageContent', PermissionSetting: Allow)]
        >>> pprint(grants.getPermissionsForPrincipal('sb.person.albert'))
        [('zope.ManageContent', PermissionSetting: Allow),
         ('zope.ManageSite', PermissionSetting: Allow)]
        >>> grants.getPermissionsForPrincipal('sb.group.3')
        [('zope.ManageSite', PermissionSetting: Allow)]

        >>> pprint(view.getPersons())
        [{'id': u'sb.person.albert',
          'perms': ['zope.ManageContent', 'zope.ManageSite'],
          'title': 'Albert'},
         {'id': u'sb.person.marius',
          'perms': ['zope.ManageContent'],
          'title': 'Marius'}]
        >>> pprint(view.getGroups())
        [{'perms': ['zope.ManageSite'], 'id': u'sb.group.3', 'title': 'office'},
         {'perms': [], 'id': u'sb.group.4', 'title': 'mgmt'}]

    The view redirects to the context's default view:

        >>> request.response.getStatus()
        302
        >>> url = zapi.absoluteURL(app, request)
        >>> request.response.getHeader('Location') == url
        True

    If we render the form, we see the appropriate checkboxes checked:

        >>> request.setPrincipal(StubPrincipal())
        >>> print view()
        <BLANKLINE>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        ...
              <tr>
                 <th>office</th>
                 <td>
                    <input type="checkbox" name="sb.group.3"
                           value="zope.View" />
                 </td>
                 <td>
                    <input type="checkbox" name="sb.group.3"
                           value="zope.ManageContent" />
                 </td>
                 <td>
                    <input type="checkbox" checked="checked"
                           name="sb.group.3" value="zope.ManageSite" />
                 </td>
              </tr>
        ...
              <tr>
                 <th>Albert</th>
                 <td>
                    <input type="checkbox" name="sb.person.albert"
                           value="zope.View" />
                 </td>
                 <td>
                    <input type="checkbox" checked="checked"
                           name="sb.person.albert"
                           value="zope.ManageContent" />
                 </td>
                 <td>
                    <input type="checkbox" checked="checked"
                           name="sb.person.albert"
                           value="zope.ManageSite" />
                 </td>
              </tr>
        ...


    If we submit a form without a submit button, nothing is changed:

        >>> request = TestRequest(form={
        ...     'sb.group.4': 'zope.ManageSite',})
        >>> request.setPrincipal(StubPrincipal())
        >>> view = View(app, request)
        >>> result = view.update()

        >>> grants.getPermissionsForPrincipal('sb.person.marius')
        [('zope.ManageContent', PermissionSetting: Allow)]

    The user does not get redirected:

        >>> request.response.getStatus()
        599
        >>> url = zapi.absoluteURL(app, request)
        >>> request.response.getHeader('Location')


    However, if submit was clicked, unchecked permissions are revoked,
    and new ones granted:

        >>> request = TestRequest(form={
        ...     'sb.group.4': 'zope.ManageSite',
        ...     'UPDATE_SUBMIT': 'Set'})
        >>> view = View(app, request)
        >>> result = view.update()

        >>> grants.getPermissionsForPrincipal('sb.person.marius')
        []
        >>> grants.getPermissionsForPrincipal('sb.group.4')
        [('zope.ManageSite', PermissionSetting: Allow)]

    If the cancel button is hit, the changes are not applied, but the
    browser is redirected to the default view for context:

        >>> request = TestRequest(form={
        ...     'sb.group.4': 'zope.ManageContent',
        ...     'CANCEL': 'Cancel'})
        >>> view = View(app, request)
        >>> result = view.update()

        >>> grants.getPermissionsForPrincipal('sb.person.marius')
        []
        >>> grants.getPermissionsForPrincipal('sb.group.4')
        [('zope.ManageSite', PermissionSetting: Allow)]

        >>> request.response.getStatus()
        302
        >>> url = zapi.absoluteURL(app, request)
        >>> request.response.getHeader('Location') == url
        True

    """

def setUpSession():
    """Set up the session machinery."""
    from zope.app.session.session import ClientId, Session
    from zope.app.session.session import PersistentSessionDataContainer
    from zope.publisher.interfaces import IRequest
    from zope.app.session.http import CookieClientIdManager
    from zope.app.session.interfaces import ISessionDataContainer
    from zope.app.session.interfaces import IClientId
    from zope.app.session.interfaces import IClientIdManager, ISession
    ztapi.provideAdapter(IRequest, IClientId, ClientId)
    ztapi.provideAdapter(IRequest, ISession, Session)
    ztapi.provideUtility(IClientIdManager, CookieClientIdManager())
    sdc = PersistentSessionDataContainer()
    ztapi.provideUtility(ISessionDataContainer, sdc, 'schoolbell.auth')


def setUp(test):
    """Set up the test fixture for doctests in this module.

    Performs what is called a "placeless setup" in the Zope 3 world, then
    sets up annotations, relationships, and registers widgets as views for some
    schema fields.
    """
    from zope.app.form.browser import PasswordWidget, TextWidget, BytesWidget
    from zope.app.form.browser import CheckBoxWidget, DateWidget, IntWidget
    from zope.app.form.browser import ChoiceInputWidget, DropdownWidget, TextAreaWidget
    from zope.app.form.browser import ChoiceCollectionInputWidget, CollectionInputWidget
    from zope.app.form.browser import MultiSelectWidget
    from zope.app.form.interfaces import IInputWidget
    from zope.publisher.interfaces.browser import IBrowserRequest
    from zope.schema.interfaces import IPassword, ITextLine, IText, IBytes, IBool, ISet
    from zope.schema.interfaces import IDate, IInt, IChoice, IIterableVocabulary
    setup.placefulSetUp()
    setup.setUpAnnotations()
    setup.setUpTraversal()
    # relationships
    from schoolbell.relationship.tests import setUpRelationships
    setUpRelationships()
    # widgets
    ztapi.browserViewProviding(IPassword, PasswordWidget, IInputWidget)
    ztapi.browserViewProviding(ITextLine, TextWidget, IInputWidget)
    ztapi.browserViewProviding(IText, TextAreaWidget, IInputWidget)
    ztapi.browserViewProviding(IBytes, BytesWidget, IInputWidget)
    ztapi.browserViewProviding(IBool, CheckBoxWidget, IInputWidget)
    ztapi.browserViewProviding(IDate, DateWidget, IInputWidget)
    ztapi.browserViewProviding(IInt, IntWidget, IInputWidget)
    ztapi.browserViewProviding(IChoice, ChoiceInputWidget, IInputWidget)
    ztapi.browserViewProviding(ISet, CollectionInputWidget, IInputWidget)

    ztapi.provideMultiView((IChoice, IIterableVocabulary), IBrowserRequest,
                           IInputWidget, '', DropdownWidget)

    ztapi.provideMultiView((ISet, IChoice), IBrowserRequest,
                           IInputWidget, '', ChoiceCollectionInputWidget)
    ztapi.provideMultiView((ISet, IIterableVocabulary), IBrowserRequest,
                           IInputWidget, '', MultiSelectWidget)

    # errors in forms
    from zope.app.form.interfaces import IWidgetInputError
    from zope.app.form.browser.interfaces import IWidgetInputErrorView
    from zope.app.form.browser.exception import WidgetInputErrorView
    ztapi.browserViewProviding(IWidgetInputError, WidgetInputErrorView,
                               IWidgetInputErrorView)


    # Now, the question is: does the speed of the tests run with the
    # setup below justify this complex setup that duplicates the ZCML?
    # For now, I say yes.

    # ++view++
    from zope.app.traversing.interfaces import ITraversable
    from zope.app.traversing.namespace import view, resource
    ztapi.provideView(None, None, ITraversable, 'view', view)
    ztapi.provideView(None, None, ITraversable, 'resource', resource)

    # schoolbell: namespace in tal
    from zope.app.traversing.interfaces import IPathAdapter
    from schoolbell.app.browser import SchoolBellAPI
    ztapi.provideAdapter(None, IPathAdapter, SchoolBellAPI, 'schoolbell')

    # standard_macros and schoolbell_navigation
    from zope.app.pagetemplate.simpleviewclass import SimpleViewClass
    from schoolbell.app.browser import NavigationView
    from zope.app.basicskin.standardmacros import StandardMacros
    ztapi.browserView(None, 'standard_macros', StandardMacros)
    ztapi.browserView(None, 'view_macros',
                      SimpleViewClass("../templates/view_macros.pt"))
    ztapi.browserView(None, 'schoolbell_navigation',
                      SimpleViewClass("../templates/navigation.pt",
                                      bases=(NavigationView,)))
    class ResourceStub:
        def __init__(self, request):
            pass
        def __call__(self):
            return "a resource"

    ztapi.browserResource('layout.css', ResourceStub)
    ztapi.browserResource('style.css', ResourceStub)
    ztapi.browserResource('schoolbell.js', ResourceStub)
    ztapi.browserResource('logo.png', ResourceStub)

    from zope.app.publisher.browser.menu import MenuAccessView
    ztapi.browserView(None, 'view_get_menu', MenuAccessView)
    from zope.app.publisher.interfaces.browser import IMenuItemType
    class ZMIMenu(IMenuItemType): pass
    directlyProvides(ZMIMenu, IMenuItemType)
    ztapi.provideUtility(IMenuItemType, ZMIMenu, 'zmi_views')
    ztapi.provideUtility(IMenuItemType, ZMIMenu, 'schoolbell_actions')


def tearDown(test):
    """Tear down the test fixture for doctests in this module."""
    setup.placefulTearDown()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(setUp=setUp, tearDown=tearDown,
                                       optionflags=doctest.ELLIPSIS))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
