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
Unit tests for schoolbell.app.security

$Id: test_security.py 4431 2005-08-02 04:33:27Z tvon $
"""
import unittest
from pprint import pprint

from zope.interface.verify import verifyObject
from zope.testing import doctest
from zope.app.container.contained import ObjectAddedEvent
from zope.app.tests import ztapi, setup

from schoolbell.app.tests.test_security import setUpLocalGrants

def doctest_personPermissionsSubscriber():
    r"""
    Set up:

        >>> from schoolbell.app.app import SchoolBellApplication, Group
        >>> from schoolbell.app.person.person import Person, PersonContainer
        >>> root = setup.placefulSetUp(True)
        >>> setUpLocalGrants()
        >>> root['sb'] = SchoolBellApplication()
        >>> root['sb']['persons'] = PersonContainer()

        >>> group = Group('slackers')
        >>> root['sb']['groups']['slackers'] = group

    Call our subscriber:

        >>> from schoolbell.app.security import groupPermissionsSubscriber
        >>> groupPermissionsSubscriber(ObjectAddedEvent(group))

    Check that the group has a view permission on self:

        >>> from zope.app.securitypolicy.interfaces import \
        ...     IPrincipalPermissionManager
        >>> map = IPrincipalPermissionManager(group)
        >>> perms = map.getPermissionsForPrincipal('sb.group.slackers')
        >>> perms.sort()
        >>> pprint(perms)
        [('schoolbell.view', PermissionSetting: Allow),
         ('schoolbell.viewCalendar', PermissionSetting: Allow)]

    Check that no permissions are set if the object added is not a group:

        >>> person = Person('joe')
        >>> root['sb']['persons']['joe'] = person
        >>> groupPermissionsSubscriber(ObjectAddedEvent(person))
        >>> map = IPrincipalPermissionManager(person)
        >>> map.getPermissionsForPrincipal('sb.person.joe')
        []

    Clean up:

        >>> setup.placefulTearDown()
    """

def doctest_PersonContainer():
    """Tests for PersonContainer

        >>> from schoolbell.app.person.interfaces import IPersonContainer
        >>> from schoolbell.app.person.person import PersonContainer
        >>> c = PersonContainer()
        >>> verifyObject(IPersonContainer, c)
        True

    PersonContainer uses the `username` attribute of persons as the key

        >>> from schoolbell.app.person.person import Person
        >>> person = Person(username="itsme")
        >>> c['doesnotmatter'] = person
        >>> c['itsme'] is person
        True
        >>> c.get('doesnotmatter') is None
        True

    Adaptation (i.e. __conform__) is tested in doctest_SchoolBellApplication.
    """


def doctest_Person():
    r"""Tests for Person

        >>> from schoolbell.app.person.interfaces import IPersonContained
        >>> from schoolbell.app.person.person import Person
        >>> person = Person('person')
        >>> verifyObject(IPersonContained, person)
        True

    Persons initially have no password

        >>> person.hasPassword()
        False

    When a person has no password, he cannot log in

        >>> person.checkPassword('')
        False
        >>> person.checkPassword(None)
        False

    You can set the password

        >>> person.setPassword('secret')
        >>> person.hasPassword()
        True
        >>> person.checkPassword('secret')
        True
        >>> person.checkPassword('justguessing')
        False

    Note that the password is not stored in plain text and cannot be recovered

        >>> import pickle
        >>> 'secret' not in pickle.dumps(person)
        True

    You can lock out the user's accound by setting the password to None

        >>> person.setPassword(None)
        >>> person.hasPassword()
        False
        >>> person.checkPassword('')
        False
        >>> person.checkPassword(None)
        False

    Note that you can set the password to an empty string, although that is
    not a secure password

        >>> person.setPassword('')
        >>> person.hasPassword()
        True
        >>> person.checkPassword('')
        True
        >>> person.checkPassword(None)
        False

    It is probably not a very good idea to use non-ASCII characters in
    passwords, but you can do that

        >>> person.setPassword(u'\u1234')
        >>> person.checkPassword(u'\u1234')
        True

    Persons have a calendar:

        >>> person.calendar.__name__
        'calendar'
        >>> person.calendar.__parent__ is person
        True
        >>> len(person.calendar)
        0
    """

def doctest_PersonPreferences():
    r"""Tests for the Preferences adapter

        >>> from zope.app.tests import setup
        >>> setup.placelessSetUp()
        >>> setup.setUpAnnotations()
        >>> from schoolbell.app.person.person import Person

        >>> person = Person('person')

    Note that the ``IHavePreferences`` interface is added in ZCML.

    Make sure the attribute stores the correct interface

        >>> from schoolbell.app.person.interfaces import IPersonPreferences
        >>> from schoolbell.app.person.preference import getPersonPreferences
        >>> prefs = getPersonPreferences(person)
        >>> verifyObject(IPersonPreferences, prefs)
        True
        >>> prefs.timezone
        'UTC'
        >>> prefs.weekstart
        0

    Need to have prefs.__parent__ refer to the person it's attached to:

        >>> prefs.__parent__ == person
        True

        >>> setup.placelessTearDown()

    """


def doctest_PersonDetails():
    r"""Tests for the contact information Details adapter

        >>> from zope.app.tests import setup
        >>> setup.placelessSetUp()
        >>> setup.setUpAnnotations()
        >>> from schoolbell.app.person.person import Person

        >>> person = Person('person')

    Make sure the attribute stores the correct interface

        >>> from schoolbell.app.person.interfaces import IPersonDetails
        >>> from schoolbell.app.person.details import getPersonDetails
        >>> details = getPersonDetails(person)
        >>> verifyObject(IPersonDetails, details)
        True

        >>> from zope.app.location.interfaces import ILocation
        >>> verifyObject(ILocation, details)
        True

    Need to have prefs.__parent__ refer to the person its attached to

        >>> details.__parent__ == person
        True

    """


def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite(),
        doctest.DocTestSuite('schoolbell.app.person.person'),
        ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
