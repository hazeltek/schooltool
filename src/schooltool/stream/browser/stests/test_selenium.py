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
Functional selenium tests for schooltool.proximity
"""
import unittest

from schooltool.stream.stesting import stream_selenium_layer
from schooltool.testing.selenium import collect_ftests


def add_stream(browser, year, title, description=None):
    browser.open('http://localhost/streams')
    browser.query.link(year).click()
    browser.query.link('Stream').click()
    browser.query.id('form-widgets-title').ui.set_value(title)
    if description is not None:
        browser.query.id('form-widgets-description').ui.set_value(title)
    browser.query.id('form-buttons-add').click()


def test_suite():
    extra_globs = {
        'add_stream': add_stream,
    }
    return collect_ftests(layer=stream_selenium_layer, extra_globs=extra_globs)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
