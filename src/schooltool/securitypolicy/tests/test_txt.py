#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2010 Shuttleworth Foundation
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
Test suites for *.txt doctests.
"""

import unittest
from zope.testing import doctest
from zope.app.testing import setup

from schooltool.testing.setup import ZCMLWrapper


def setUpSecurityDirectives(test=None):
    setup.placelessSetUp()
    zcml = ZCMLWrapper()
    zcml.include('zope.app.zcmlfiles')
    zcml.include('schooltool.securitypolicy', file='meta.zcml')
    zcml.include('schooltool.securitypolicy')
    test.globs['zcml'] = zcml


def tearDownSecurityDirectives(test=None):
    setup.placelessTearDown()


def test_suite():
    optionflags = (doctest.NORMALIZE_WHITESPACE |
                   doctest.ELLIPSIS |
                   doctest.REPORT_NDIFF)

    return unittest.TestSuite([
        doctest.DocFileSuite('../README.txt', optionflags=optionflags),
        doctest.DocFileSuite(
            '../security_descriptions.txt',
            setUp=setUpSecurityDirectives, tearDown=tearDownSecurityDirectives,
            optionflags=optionflags),
        ])
