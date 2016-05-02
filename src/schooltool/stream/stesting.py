#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2012 Shuttleworth Foundation
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
Selenium functional testing Utilities for streams.
"""

import os

from schooltool.testing.selenium import SeleniumLayer

dir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(dir, 'stesting.zcml')

stream_selenium_layer = SeleniumLayer(filename,
                                      __name__,
                                      'stream_selenium_layer')


def registerSeleniumSetup():
    try:
        import selenium
    except ImportError:
        return
    from schooltool.testing import registry
    import schooltool.testing.selenium

    def addStream(browser, schoolyear, title, **kw):
        optional = (
            'description',
            )
        browser.query.link('School').click()
        sel = '//ul[contains(@class, "third-nav")]//a[text()="%s"]' % schoolyear
        browser.query.xpath(sel).click()
        sel = '//a[contains(@href, "addStream.html")]'
        browser.query.xpath(sel).click()
        browser.query.name('form.widgets.title').type(title)
        for name in optional:
            if name in kw:
                value = kw[name]
                widget_id = ''.join(['form-widgets-', name])
                browser.query.id(widget_id).ui.set_value(value)
        page = browser.query.tag('html')
        browser.query.button('Submit').click()
        browser.wait(lambda: page.expired)

    registry.register('SeleniumHelpers',
        lambda: schooltool.testing.selenium.registerBrowserUI(
            'stream.add', addStream))


registerSeleniumSetup()
del registerSeleniumSetup
