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
Fee implementation
"""

from persistent import Persistent
from persistent.list import PersistentList

from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.interface import implementer
from zope.interface import implements

from schooltool.basicperson.interfaces import IBasicPerson
from schooltool.fee.interfaces import IAmount
from schooltool.fee.interfaces import ICredit
from schooltool.fee.interfaces import ICreditBalance
from schooltool.fee.interfaces import IDebit
from schooltool.fee.interfaces import IDebitBalance


PERSON_CREDIT_KEY = 'schooltool.fee.credit'
PERSON_DEBIT_KEY = 'schooltool.fee.debit'


class Amount(Persistent):

    implements(IAmount)

    title = None
    description = None
    date = None
    amount = None


class Credit(Amount):

    implements(ICredit)


class Debit(Amount):

    implements(IDebit)


@implementer(ICreditBalance)
@adapter(IBasicPerson)
def PersonCreditBalance(person):
    ann = IAnnotations(person)
    if PERSON_CREDIT_KEY not in ann:
        ann[PERSON_CREDIT_KEY] = PersistentList()
    return ann[PERSON_CREDIT_KEY]


@implementer(IDebitBalance)
@adapter(IBasicPerson)
def PersonDebitBalance(person):
    ann = IAnnotations(person)
    if PERSON_DEBIT_KEY not in ann:
        ann[PERSON_DEBIT_KEY] = PersistentList()
    return ann[PERSON_DEBIT_KEY]
