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
SchoolBell skin.

$Id: skin.py 3335 2005-03-25 18:53:11Z ignas $
"""
import os
import sys

from zope.interface import Interface
from zope.publisher.interfaces.browser import ILayer, IDefaultBrowserLayer
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.viewlet.interfaces import IViewletManager
from zope.app import zapi
from zope.app.publisher.browser import applySkin
from zope.app.traversing import api

from schooltool.app.app import getSchoolToolApplication
from schooltool.app.interfaces import ISchoolToolApplication


class IJavaScriptManager(IViewletManager):
    """Provides a viewlet hook for the javascript link entries."""


class ICSSManager(IViewletManager):
    """Provides a viewlet hook for the CSS link entries."""


class IHeaderManager(IViewletManager):
    """Provides a viewlet hook for the header of a page."""


class INavigationManager(IViewletManager):
    """Provides a viewlet hook for the navigation section of a page."""


class NavigationViewlet(object):
    """A navigation viewlet base class."""

    def appURL(self):
        return zapi.absoluteURL(getSchoolToolApplication(), self.request)

    def __cmp__(self, other):
        if hasattr(self, 'order'):
            if hasattr(other, 'order'):
                return cmp(int(self.order), int(other.order))
            else:
                return -1
        else:
            if hasattr(other, 'order'):
                return +1
            else:
                return cmp(self.title, other.title)


class ISchoolToolLayer(ILayer, IBrowserRequest):
    """SchoolTool layer."""


class ISchoolToolSkin(ISchoolToolLayer, IDefaultBrowserLayer):
    """The SchoolTool skin"""


def schoolToolTraverseSubscriber(event):
    """A subscriber to BeforeTraverseEvent.

    Sets the SchoolBell skin if the object traversed is a SchoolBell
    application instance.
    """
    if (ISchoolToolApplication.providedBy(event.object) and
        IBrowserRequest.providedBy(event.request)):
        applySkin(event.request, ISchoolToolSkin)
