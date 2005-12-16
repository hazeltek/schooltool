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
Storage of attendance records.

$Id$
"""
__docformat__ = 'reStructuredText'

import datetime

from persistent import Persistent
from persistent.list import PersistentList
from persistent.dict import PersistentDict
from zope.interface import implements
from zope.app.annotation.interfaces import IAnnotations
from zope.i18n import translate

from schooltool import SchoolToolMessage as _
from schooltool.calendar.simple import ImmutableCalendar
from schooltool.calendar.simple import SimpleCalendarEvent
from schooltool.attendance.interfaces import IDayAttendance
from schooltool.attendance.interfaces import IDayAttendanceRecord
from schooltool.attendance.interfaces import ISectionAttendance
from schooltool.attendance.interfaces import ISectionAttendanceRecord
from schooltool.attendance.interfaces import IAbsenceExplanation
from schooltool.attendance.interfaces import UNKNOWN, PRESENT, ABSENT, TARDY
from schooltool.attendance.interfaces import NEW, ACCEPTED, REJECTED
from schooltool.attendance.interfaces import AttendanceError


#
# Attendance record classes
#

class AttendanceRecord(Persistent):
    """Base class for attendance records."""

    def __init__(self, status):
        self.status = status
        self.late_arrival = None
        self.explanations = PersistentList()

    def isUnknown(self): return self.status == UNKNOWN
    def isPresent(self): return self.status == PRESENT
    def isAbsent(self):  return self.status == ABSENT
    def isTardy(self):   return self.status == TARDY

    def isExplained(self):
        if self.status not in (ABSENT, TARDY):
            raise AttendanceError(
                "only absences and tardies can be explained.")
        for e in self.explanations:
            if e.isAccepted():
                return True
        return False

    def addExplanation(self, text):
        if self.status not in (ABSENT, TARDY):
            raise AttendanceError(
                "only absences and tardies can be explained.")
        explanation = AbsenceExplanation(text)
        self.explanations.append(explanation)
        return explanation

    def makeTardy(self, arrival_time):
        if not self.isAbsent():
            raise AttendanceError("makeTardy when status is %s, not ABSENT"
                                  % self.status)
        self.status = TARDY
        self.late_arrival = arrival_time


class AbsenceExplanation(Persistent):
    """An explanation of an absence/tardy."""

    implements(IAbsenceExplanation)

    def __init__(self, text):
        self.text = text
        self.status = NEW

    def accept(self):
        self.status = ACCEPTED

    def reject(self):
        self.status = REJECTED

    def isAccepted(self):
        return self.status == ACCEPTED


class DayAttendanceRecord(AttendanceRecord):
    """Record of a student's presence or absence on a given day."""

    implements(IDayAttendanceRecord)

    def __init__(self, date, status):
        AttendanceRecord.__init__(self, status)
        self.date = date

    def __repr__(self):
        return 'DayAttendanceRecord(%r, %s)' % (self.date, self.status)


class SectionAttendanceRecord(AttendanceRecord):
    """Record of a student's presence or absence at a given section meeting."""

    implements(ISectionAttendanceRecord)

    def __init__(self, section, datetime, status,
                 duration=datetime.timedelta(0), period_id=None):
        AttendanceRecord.__init__(self, status)
        self.section = section
        self.datetime = datetime
        self.duration = duration
        self.period_id = period_id

    @property
    def date(self):
        return self.datetime.date()

    def __repr__(self):
        return 'SectionAttendanceRecord(%r, %r, %s)' % (self.section,
                                                        self.datetime,
                                                        self.status)


#
# Attendance storage classes
#


class AttendanceFilteringMixin(object):
    """Mixin that implements IAttendance.filter on top of __iter__."""

    def filter(self, first, last):
        for ar in self:
            if first <= ar.date <= last:
                yield ar


class DayAttendance(Persistent, AttendanceFilteringMixin):
    """Persistent object that stores day attendance records for a student."""

    implements(IDayAttendance)

    def __init__(self):
        self._records = PersistentDict()
        # When it is time to optimize, convert it to OOBTree

    def __iter__(self):
        return iter(self._records.values())

    def makeCalendar(self, first, last):
        raise NotImplementedError # XXX TODO

    def get(self, date):
        try:
            return self._records[date]
        except KeyError:
            return DayAttendanceRecord(date, UNKNOWN)

    def record(self, date, present):
        if date in self._records:
            raise AttendanceError('record for %s already exists' % date)
        if present: status = PRESENT
        else: status = ABSENT
        self._records[date] = DayAttendanceRecord(date, status)


class SectionAttendance(Persistent, AttendanceFilteringMixin):
    """Persistent object that stores section attendance records for a student.
    """

    implements(ISectionAttendance)

    def __init__(self):
        self._records = PersistentList()
        # When it is time to optimize, I think self._records should be replaced
        # with a OOBTree, indexed by date.

    def __iter__(self):
        return iter(self._records)

    def makeCalendar(self, first, last):
        events = []
        for record in self.filter(first, last):
            title = None
            if record.isTardy():
                minutes = (record.late_arrival - record.datetime).seconds / 60
                title = self.tardyEventTitle(record, minutes)
            elif record.isAbsent():
                title = self.absenceEventTitle(record)
            if title:
                events.append(self.makeCalendarEvent(record, title))
        return ImmutableCalendar(events)

    def tardyEventTitle(self, record, minutes_late):
        """Produce a title for a calendar event representing a tardy."""
        return translate(_('Was late for ${section} (${mins} minutes).',
                           mapping={'section': record.section.title,
                                    'mins': minutes_late}))

    def absenceEventTitle(self, record):
        """Produce a title for a calendar event representing an absence."""
        return translate(_('Was absent from ${section}.',
                           mapping={'section': record.section.title}))

    def makeCalendarEvent(self, record, title):
        """Produce a calendar event for an absence or a tardy."""
        return SimpleCalendarEvent(title=title,
                                   dtstart=record.datetime,
                                   duration=record.duration)

    def getAllForDay(self, date):
        return self.filter(date, date)

    def get(self, section, datetime):
        for ar in self._records:
            if (ar.section, ar.datetime) == (section, datetime):
                return ar
        return SectionAttendanceRecord(section, datetime, status=UNKNOWN)

    def record(self, section, datetime, duration, period_id, present):
        if self.get(section, datetime).status != UNKNOWN:
            raise AttendanceError('record for %s at %s already exists'
                                  % (section, datetime))
        if present: status = PRESENT
        else: status = ABSENT
        ar = SectionAttendanceRecord(section, datetime, status=status,
                                     duration=duration, period_id=period_id)
        self._records.append(ar)


#
# Adapters
#

DAY_ATTENDANCE_KEY = 'schooltool.attendance.DayAttendance'
SECTION_ATTENDANCE_KEY = 'schooltool.attendance.SectionAttendance'


def getSectionAttendance(person):
    """Return the section attendance record for a person."""
    annotations = IAnnotations(person)
    try:
        attendance = annotations[SECTION_ATTENDANCE_KEY]
    except KeyError:
        attendance = SectionAttendance()
        annotations[SECTION_ATTENDANCE_KEY] = attendance
    return attendance


def getDayAttendance(person):
    """Return the section attendance record for a person."""
    annotations = IAnnotations(person)
    try:
        attendance = annotations[DAY_ATTENDANCE_KEY]
    except KeyError:
        attendance = DayAttendance()
        annotations[DAY_ATTENDANCE_KEY] = attendance
    return attendance

