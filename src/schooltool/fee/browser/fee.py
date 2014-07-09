#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2014 Shuttleworth Foundation
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
Fee views
"""

from decimal import Decimal

from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser.absoluteurl import absoluteURL

from z3c.form import button
from z3c.form import field
from z3c.form import form

from schooltool.common.inlinept import InheritTemplate
from schooltool.course.section import is_student
from schooltool.fee.interfaces import ICredit
from schooltool.fee.interfaces import ICreditBalance
from schooltool.fee.interfaces import IDebit
from schooltool.fee.interfaces import IDebitBalance
from schooltool.fee.fee import Credit
from schooltool.fee.fee import Debit
from schooltool.skin import flourish

from schooltool.common import SchoolToolMessage as _


class PersonFeesViewlet(flourish.viewlet.Viewlet):

    template = ViewPageTemplateFile('templates/personfees.pt')

    def entry_info(self, entry):
        result = {
            'title': entry.title,
            'date': entry.date,
            'credit': None,
            'debit': None,
        }
        if ICredit.providedBy(entry):
            result['credit'] = entry.amount
        elif IDebit.providedBy(entry):
            result['debit'] = entry.amount
        return result

    def update(self):
        debit_balance = removeSecurityProxy(IDebitBalance(self.context))
        credit_balance = removeSecurityProxy(ICreditBalance(self.context))
        entries = []
        balance = Decimal(0)
        for entry in (debit_balance + credit_balance):
            info = self.entry_info(entry)
            if info['credit']:
                balance += info['credit']
            if info['debit']:
                balance -= info['debit']
            entries.append(info)
        self.entries = sorted(entries, key=lambda e: e['date'])
        self.balance = balance

    @property
    def amount_due(self):
        if self.balance < 0:
            return abs(self.balance)

    def render(self, *args, **kw):
        if is_student(self.context):
            return self.template(*args, **kw)
        return ''


class AddDebitPersonView(flourish.form.Form):

    template = InheritTemplate(flourish.page.Page.template)
    label = None
    legend = _('Debit Information')
    fields = field.Fields(IDebit)

    @property
    def title(self):
        return self.context.title

    def getContent(self):
        return {
            'date': self.request.util.today,
            'title': '',
            'description': '',
            'amount': 0,
        }

    def updateActions(self):
        super(AddDebitPersonView, self).updateActions()
        self.actions['submit'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    @button.buttonAndHandler(_('Submit'))
    def handleSubmit(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        debit = Debit()
        form.applyChanges(self, debit, data)
        debit_balance = removeSecurityProxy(IDebitBalance(self.context))
        debit_balance.append(debit)
        self.request.response.redirect(self.nextURL())

    @button.buttonAndHandler(_("Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.nextURL())

    def nextURL(self):
        return absoluteURL(self.context, self.request)


class AddCreditPersonView(flourish.form.Form):

    template = InheritTemplate(flourish.page.Page.template)
    label = None
    legend = _('Credit Information')
    fields = field.Fields(ICredit)

    @property
    def title(self):
        return self.context.title

    def getContent(self):
        return {
            'date': self.request.util.today,
            'title': '',
            'description': '',
            'amount': 0,
        }

    def updateActions(self):
        super(AddCreditPersonView, self).updateActions()
        self.actions['submit'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    @button.buttonAndHandler(_('Submit'))
    def handleSubmit(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        credit = Credit()
        form.applyChanges(self, credit, data)
        credit_balance = removeSecurityProxy(ICreditBalance(self.context))
        credit_balance.append(credit)
        self.request.response.redirect(self.nextURL())

    @button.buttonAndHandler(_("Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.nextURL())

    def nextURL(self):
        return absoluteURL(self.context, self.request)
