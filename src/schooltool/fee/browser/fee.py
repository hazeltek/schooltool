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
from zope.cachedescriptors.property import Lazy
from zope.container.interfaces import INameChooser
from zope.security.checker import canAccess
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser.absoluteurl import absoluteURL

from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form import widget

from schooltool.common.inlinept import InheritTemplate
from schooltool.course.section import is_student
from schooltool.fee.fee import Credit
from schooltool.fee.fee import Debit
from schooltool.fee.interfaces import IAmount
from schooltool.fee.interfaces import ICredit
from schooltool.fee.interfaces import IDebit
from schooltool.fee.interfaces import IFeeContainer
from schooltool.skin import flourish

from schooltool.common import SchoolToolMessage as _


class PersonFeesViewlet(flourish.viewlet.Viewlet):

    template = ViewPageTemplateFile('templates/personfees.pt')

    @property
    def canModify(self):
        return canAccess(self.context.__parent__, '__delitem__')

    def entry_info(self, entry):
        result = {
            'title': entry.title,
            'date': entry.date,
            'edit_url': '%s/edit.html' % absoluteURL(entry, self.request)
        }
        if ICredit.providedBy(entry):
            result['amount'] = entry.amount
        elif IDebit.providedBy(entry):
            result['amount'] = -entry.amount
        return result

    def update(self):
        fees = IFeeContainer(self.context)
        entries = []
        balance = Decimal(0)
        for entry in fees.values():
            info = self.entry_info(entry)
            balance += info['amount']
            entries.append(info)
        self.entries = sorted(entries, key=lambda e: e['date'])
        self.balance = balance

    def render(self, *args, **kw):
        if is_student(self.context):
            return self.template(*args, **kw)
        return ''


class AmountAddView(flourish.form.AddForm):

    template = InheritTemplate(flourish.page.Page.template)
    label = None

    @Lazy
    def person(self):
        return self.context.__parent__

    @property
    def title(self):
        return self.person.title

    def updateActions(self):
        super(AmountAddView, self).updateActions()
        self.actions['add'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    @button.buttonAndHandler(_('Submit'), name='add')
    def handleAdd(self, action):
        super(AmountAddView, self).handleAdd.func(self, action)

    @button.buttonAndHandler(_("Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.nextURL())

    def nextURL(self):
        return absoluteURL(self.person, self.request)

    def create(self, data):
        obj = self.factory()
        form.applyChanges(self, obj, data)
        return obj

    def add(self, obj):
        chooser = INameChooser(self.context)
        name = chooser.chooseName(u'', obj)
        self.context[name] = obj


AddAmountDefaultDate = widget.ComputedWidgetAttribute(
    lambda adapter: adapter.request.util.today,
    view=AmountAddView,
    field=IAmount['date']
    )


AddAmountDefaultAmount = widget.StaticWidgetAttribute(
    0,
    view=AmountAddView,
    field=IAmount['amount']
    )


field_order = ['date', 'title', 'description', 'amount']


class DebitAddView(AmountAddView):

    legend = _('Debit Information')
    fields = field.Fields(IDebit).select(*field_order)
    factory = Debit


class CreditAddView(AmountAddView):

    legend = _('Credit Information')
    fields = field.Fields(ICredit).select(*field_order)
    factory = Credit


class AmountEditView(flourish.form.Form,
                     form.EditForm):

    template = InheritTemplate(flourish.page.Page.template)

    @Lazy
    def person(self):
        fees = self.context.__parent__
        return fees.__parent__

    @property
    def title(self):
        return self.person.title

    def update(self):
        form.EditForm.update(self)

    def updateActions(self):
        super(AmountEditView, self).updateActions()
        self.actions['submit'].addClass('button-ok')
        self.actions['cancel'].addClass('button-cancel')

    def nextURL(self):
        return absoluteURL(self.person, self.request)

    @button.buttonAndHandler(_('Submit'), name='submit')
    def handle_submit(self, action):
        super(AmountEditView, self).handleApply.func(self, action)
        if (self.status == self.successMessage or
            self.status == self.noChangesMessage):
            self.request.response.redirect(self.nextURL())

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handle_cancel(self, action):
        self.request.response.redirect(self.nextURL())


class DebitEditView(AmountEditView):

    legend = _('Debit Information')
    fields = field.Fields(IDebit).select(*field_order)


class CreditEditView(AmountEditView):

    legend = _('Credit Information')
    fields = field.Fields(ICredit).select(*field_order)


class AmountActionsLinks(flourish.page.RefineLinksViewlet):

    pass


class AmountDeleteLink(flourish.page.LinkViewlet):

    @property
    def url(self):
        return '%s/delete.html?delete.%s&CONFIRM' % (
            absoluteURL(self.context.__parent__, self.request),
            self.context.__name__.encode('utf-8'))


class FeeContainerDeleteView(flourish.containers.ContainerDeleteView):

    @Lazy
    def person(self):
        return self.context.__parent__

    def nextURL(self):
        if 'CONFIRM' in self.request:
            return absoluteURL(self.person, self.request)
        return flourish.containers.ContainerDeleteView.nextURL(self)
