#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2011 Shuttleworth Foundation
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
Flourish error views.
"""
from zope.app.exception.browser.unauthorized import Unauthorized

from schooltool.skin.error import ErrorView
from schooltool.skin.flourish.page import ExpandedPage

class NotFound(object):

    def __call__(self, *args, **kw):
        self.request.response.setStatus(404)
        return super(NotFound, self).__call__(*args, **kw)


class ErrorPage(ExpandedPage, ErrorView):

    def __call__(self, *args, **kw):
        self.request.response.setStatus(500)
        return ExpandedPage.__call__(self, *args, **kw)


class UnauthorizedPage(ExpandedPage, Unauthorized):

    def render(self, *args, **kw):
        return Unauthorized.__call__(self)
