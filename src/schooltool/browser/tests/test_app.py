#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2003 Shuttleworth Foundation
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
Unit tests for schooltool.browser.app

$Id$
"""

import unittest
from logging import INFO

from schooltool.interfaces import AuthenticationError
from schooltool.browser.tests import TraversalTestMixin, RequestStub, setPath


__metaclass__ = type


class PersonStub:
    __name__ = 'manager'
    title = 'The Mgmt'


class TestAppView(unittest.TestCase, TraversalTestMixin):

    def createView(self):
        from schooltool.app import Application
        from schooltool.app import ApplicationObjectContainer
        from schooltool.model import Person, Group
        from schooltool.browser.app import RootView
        app = Application()
        app['persons'] = ApplicationObjectContainer(Person)
        app['groups'] = ApplicationObjectContainer(Group)
        view = RootView(app)
        return view

    def createRequestWithAuthentication(self, *args, **kw):
        person = PersonStub()
        setPath(person, '/persons/manager')
        request = RequestStub(*args, **kw)
        def authenticate(username, password):
            if username == 'manager' and password == 'schooltool':
                request.authenticated_user = person
                request.user = username
            else:
                request.authenticated_user = None
                request.user = ''
                raise AuthenticationError
        request.authenticate = authenticate
        return request

    def test_render(self):
        view = self.createView()
        request = RequestStub()
        result = view.render(request)
        self.assert_('Username' in result)
        self.assert_('error' not in result)
        self.assert_('expired' not in result)
        self.assertEquals(request.headers['content-type'],
                          "text/html; charset=UTF-8")

    def test_render_expired(self):
        view = self.createView()
        request = RequestStub('/?expired=1', args={'expired': '1'})
        result = view.render(request)
        self.assert_('Username' in result)
        self.assert_('error' not in result)
        self.assert_('expired' in result)
        self.assert_('action="/"' in result)
        self.assertEquals(request.headers['content-type'],
                          "text/html; charset=UTF-8")

    def test_render_forbidden(self):
        view = self.createView()
        request = RequestStub('/?forbidden=1', args={'forbidden': '1'})
        result = view.render(request)
        self.assert_('Username' in result)
        self.assert_('expired' not in result)
        self.assert_('not allowed' in result)
        self.assert_('action="/"' in result)
        self.assertEquals(request.headers['content-type'],
                          "text/html; charset=UTF-8")

    def test_render_with_url(self):
        view = self.createView()
        request = RequestStub(args={'url': '/some/url'})
        result = view.render(request)
        self.assert_('Username' in result)
        self.assert_('error' not in result)
        self.assert_('expired' not in result)
        self.assert_('<input type="hidden" name="url" value="/some/url" />'
                     in result)
        self.assertEquals(request.headers['content-type'],
                          "text/html; charset=UTF-8")

    def test_post(self):
        from schooltool.browser.auth import globalTicketService
        view = self.createView()
        request = self.createRequestWithAuthentication(method='POST',
                              args={'username': 'manager',
                                    'password': 'schooltool'})
        result = view.render(request)
        self.assertEquals(request.code, 302)
        self.assertEquals(request.headers['location'],
                          'http://localhost:7001/start')
        ticket = request._outgoing_cookies['auth']
        username, password = globalTicketService.verifyTicket(ticket)
        self.assertEquals(username, 'manager')
        self.assertEquals(password, 'schooltool')

    def test_post_with_url(self):
        from schooltool.browser.auth import globalTicketService
        view = self.createView()
        request = self.createRequestWithAuthentication(method='POST',
                              args={'username': 'manager',
                                    'password': 'schooltool',
                                    'url': '/some/path'})
        result = view.render(request)
        self.assertEquals(request.code, 302)
        self.assertEquals(request.headers['location'],
                          'http://localhost:7001/some/path')
        ticket = request._outgoing_cookies['auth']
        username, password = globalTicketService.verifyTicket(ticket)
        self.assertEquals(username, 'manager')
        self.assertEquals(password, 'schooltool')

    def test_post_failed(self):
        view = self.createView()
        request = self.createRequestWithAuthentication(method='POST',
                              args={'username': 'manager',
                                    'password': '5ch001t001'})
        result = view.render(request)
        self.assert_('error' in result)
        self.assert_('Username' in result)
        self.assert_('manager' in result)
        self.assertEquals(request.headers['content-type'],
                          "text/html; charset=UTF-8")

    def test_traversal(self):
        from schooltool.browser import StaticFile
        from schooltool.browser.app import LogoutView
        from schooltool.browser.app import StartView
        from schooltool.browser.app import PersonContainerView
        from schooltool.browser.app import GroupContainerView
        view = self.createView()
        app = view.context
        self.assertTraverses(view, 'logout', LogoutView, app)
        self.assertTraverses(view, 'persons', PersonContainerView,
                             app['persons'])
        self.assertTraverses(view, 'groups', GroupContainerView, app['groups'])
        css = self.assertTraverses(view, 'schooltool.css', StaticFile)
        self.assertEquals(css.content_type, 'text/css')
        css = self.assertTraverses(view, 'logo.png', StaticFile)
        self.assertEquals(css.content_type, 'image/png')
        user = object()
        request = RequestStub(authenticated_user=user)
        self.assertTraverses(view, 'start', StartView, user, request=request)
        self.assertRaises(KeyError, view._traverse, 'missing', RequestStub())


class TestLogoutView(unittest.TestCase):

    def createView(self):
        from schooltool.browser.app import LogoutView
        view = LogoutView(None)
        return view

    def test_render(self):
        view = self.createView()
        request = RequestStub()
        result = view.render(request)
        self.assertEquals(request.code, 302)
        self.assertEquals(request.headers['location'],
                          'http://localhost:7001/')

    def test_render_with_auth(self):
        from schooltool.interfaces import AuthenticationError
        from schooltool.browser.auth import globalTicketService
        view = self.createView()
        ticket = globalTicketService.newTicket(('usr', 'pwd'))
        request = RequestStub(cookies={'auth': ticket})
        request.authenticate = lambda username, password: None
        result = view.render(request)
        self.assertEquals(request.code, 302)
        self.assertEquals(request.headers['location'],
                          'http://localhost:7001/')
        self.assertRaises(AuthenticationError,
                          globalTicketService.verifyTicket, ticket)


class TestStartView(unittest.TestCase):

    def createView(self):
        from schooltool.browser.app import StartView
        from schooltool.model import Person
        user = Person()
        setPath(user, '/persons/user')
        return StartView(user)

    def test(self):
        view = self.createView()
        request = RequestStub(authenticated_user=view.context)
        result = view.render(request)
        self.assertEquals(request.headers['content-type'],
                          "text/html; charset=UTF-8")
        self.assertEquals(request.code, 200)


class TestPersonContainerView(unittest.TestCase, TraversalTestMixin):

    def createView(self):
        from schooltool.model import Person
        from schooltool.browser.app import PersonContainerView
        return PersonContainerView({'person': Person()})

    def test_render(self):
        view = self.createView()
        request = RequestStub()
        result = view.render(request)
        self.assertEquals(request.code, 404)

    def test_traverse(self):
        from schooltool.browser.model import PersonView
        from schooltool.browser.app import PersonAddView
        view = self.createView()
        person = view.context['person']
        self.assertTraverses(view, 'person', PersonView, person)
        self.assertTraverses(view, 'add.html', PersonAddView, view.context)
        self.assertRaises(KeyError, view._traverse, 'missing', RequestStub())


class TestPersonAddView(unittest.TestCase):

    def createView(self):
        from schooltool.model import Person
        from schooltool.browser.app import PersonAddView

        class PersonContainerStub:

            def __init__(self):
                self.persons = []

            def new(self, username, title):
                person = Person(title=title)
                person.__name__ = username
                person.__parent__ = self
                self.persons.append(person)
                return person

        self.person_container = PersonContainerStub()
        setPath(self.person_container, '/persons')

        return PersonAddView(self.person_container)

    def test(self):
        view = self.createView()

        request = RequestStub()
        result = view.do_GET(request)
        self.assert_('Add person' in result)

        request = RequestStub(args={'username': 'newbie',
                                    'password': 'foo',
                                    'verify_password': 'foo'})
        result = view.do_POST(request)
        self.assertEquals(request.applog,
                          [(None, u'Object created: /persons/newbie', INFO)])
        self.assertEquals(request.code, 302)
        self.assertEquals(request.headers['location'],
                          'http://localhost:7001/persons/newbie/edit.html')

        persons = self.person_container.persons
        self.assertEquals(len(persons), 1)
        self.assertEquals(persons[0].__name__, 'newbie')
        self.assertEquals(persons[0].title, 'newbie')

    def test_errors(self):
        # We're not very i18n friendly by not allowing international
        # symbols in user names.
        for username in ('newbie \xc4\x85', 'new/bie', 'foo\000bar'):
            view = self.createView()
            request = RequestStub(args={'username': username,
                                        'password': 'bar',
                                        'verify_password': 'bar'})
            view.do_POST(request)
            self.assertEquals(view.error, u'Invalid username')

        view = self.createView()
        request = RequestStub(args={'username': 'badpass',
                                    'password': 'foo',
                                    'verify_password': 'bar'})
        view.do_POST(request)
        self.assertEquals(view.error, u'Passwords do not match')
        self.assertEquals(view.prev_username, 'badpass')


class TestGroupContainerView(unittest.TestCase, TraversalTestMixin):

    def createView(self):
        from schooltool.model import Group
        from schooltool.browser.app import GroupContainerView
        return GroupContainerView({'group': Group()})

    def test_render(self):
        view = self.createView()
        request = RequestStub()
        result = view.render(request)
        self.assertEquals(request.code, 404)

    def test_traverse(self):
        from schooltool.browser.model import GroupView
        from schooltool.browser.app import GroupAddView
        view = self.createView()
        group = view.context['group']
        self.assertTraverses(view, 'group', GroupView, group)
        self.assertTraverses(view, 'add.html', GroupAddView, view.context)
        self.assertRaises(KeyError, view._traverse, 'missing', RequestStub())


class TestGroupAddView(unittest.TestCase):

    def createView(self):
        from schooltool.browser.app import GroupAddView
        from schooltool.model import Group

        class GroupContainerStub:

            def __init__(self):
                self.groups = []

            def new(self, groupname, title):
                group = Group(title=title)
                group.__name__ = groupname
                group.__parent__ = self
                self.groups.append(group)
                return group

        self.group_container = GroupContainerStub()
        setPath(self.group_container, '/groups')
        return GroupAddView(self.group_container)

    def test_GET(self):
        view = self.createView()
        request = RequestStub()
        content = view.do_GET(request)
        self.assert_('Add group' in content)

    def test_POST(self):
        view = self.createView()
        request = RequestStub(args={'groupname': 'newgroup'})
        content = view.do_POST(request)
        self.assertEquals(request.code, 302)
        self.assertEquals(request.headers['location'],
                          'http://localhost:7001/groups/newgroup/edit.html')
        self.assertEquals(request.applog,
                          [(None, 'Object created: /groups/newgroup', INFO)])

        self.assertEquals(len(self.group_container.groups), 1)
        group = self.group_container.groups[0]
        self.assertEquals(group.__name__, 'newgroup')
        self.assertEquals(group.title, 'newgroup')

    def test_POST_errors(self):
        view = self.createView()
        request = RequestStub(args={'groupname': 'new/group'})
        content = view.do_POST(request)
        self.assertEquals(request.code, 200)
        self.assertEquals(request.applog, [])
        self.assert_('Add group' in content)
        self.assert_('Invalid group name' in content)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAppView))
    suite.addTest(unittest.makeSuite(TestLogoutView))
    suite.addTest(unittest.makeSuite(TestStartView))
    suite.addTest(unittest.makeSuite(TestPersonContainerView))
    suite.addTest(unittest.makeSuite(TestPersonAddView))
    suite.addTest(unittest.makeSuite(TestGroupContainerView))
    suite.addTest(unittest.makeSuite(TestGroupAddView))
    return suite


if __name__ == '__main__':
    unittest.main()
