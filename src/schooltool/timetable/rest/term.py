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
RESTive views for Terms

$Id: app.py 3419 2005-04-14 18:34:36Z alga $
"""
import datetime
from StringIO import StringIO
import operator

from zope.component import adapts
from zope.interface import implements
from zope.app.filerepresentation.interfaces import IFileFactory, IWriteFile
from zope.app.traversing.api import getPath

from schooltool.calendar.icalendar import ICalReader
from schooltool.common import parse_date
from schooltool.app.rest import View
from schooltool.app.rest.app import GenericContainerView
from schooltool.app.rest.xmlparsing import XMLDocument
from schooltool.app.rest.errors import RestError

from schooltool.timetable.term import Term
from schooltool.timetable.interfaces import ITermContainer, ITerm


class TermContainerView(GenericContainerView):
    """RESTive view of a TermContainer."""


class TermFileFactory(object):
    """Adapter adapting ITermContainer to FileFactory."""

    implements(IFileFactory)
    adapts(ITermContainer)

    complex_prop_names = ('RRULE', 'RDATE', 'EXRULE', 'EXDATE')

    _dow_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                "Friday": 4, "Saturday": 5, "Sunday": 6}

    schema = """<?xml version="1.0" encoding="UTF-8"?>
    <!--
    RelaxNG grammar for a representation of Term
    -->
    <grammar xmlns="http://relaxng.org/ns/structure/1.0"
             ns="http://schooltool.org/ns/schooldays/0.1"
             datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes">

      <define name="idattr">
         <attribute name="id">
            <text/>
         </attribute>
      </define>

      <define name="datetext">
        <!-- date in YYYY-MM-DD format -->
        <text/>
      </define>

      <define name="daysofweek">
        <!-- space separated list of weekdays -->
        <text/>
      </define>

      <define name="title">
        <!-- A title of the term -->
        <text/>
      </define>

      <start>
        <ref name="schooldays"/>
      </start>

      <define name="schooldays">
        <element name="schooldays">
          <attribute name="first">
            <text/>
          </attribute>
          <attribute name="last">
            <ref name="datetext"/>
          </attribute>
          <element name="title">
            <ref name="title"/>
          </element>
          <element name="daysofweek">
            <ref name="daysofweek"/>
          </element>
          <zeroOrMore>
            <element name="holiday">
              <attribute name="date">
                <ref name="datetext"/>
              </attribute>
              <text/>
            </element>
          </zeroOrMore>
        </element>
      </define>

    </grammar>
    """

    factory = Term

    def __init__(self, container):
        self.context = container

    def __call__(self, name, content_type, data):
        if '.' in name:
            raise RestError("Terms can not contain dots in their names.")

        if self.isDataICal(data):
            return self.parseText(data, name=name)
        else:
            return self.parseXML(data, name=name)

    def isDataICal(self, data):
        return data.strip().startswith("BEGIN:VCALENDAR")

    def parseText(self, data, name=None):
        first = last = None
        days = []
        reader = ICalReader(StringIO(data))
        for event in reader.iterEvents():
            summary = event.getOne('SUMMARY', '').lower()
            if summary not in ('school period', 'schoolday'):
                continue # ignore boring events

            if not event.all_day_event:
                raise RestError("All-day event should be used")

            has_complex_props = reduce(operator.or_,
                                  map(event.hasProp, self.complex_prop_names))

            if has_complex_props:
                raise RestError("Repeating events/exceptions not yet supported")

            if summary == 'school period':
                if (first is not None and
                    (first, last) != (event.dtstart, event.dtend)):
                    raise RestError("Multiple definitions of school period")
                else:
                    first, last = event.dtstart, event.dtend
            elif summary == 'schoolday':
                if event.duration != datetime.date.resolution:
                    raise RestError("Schoolday longer than one day")
                days.append(event.dtstart)
        else:
            if first is None:
                raise RestError("School period not defined")
            for day in days:
                if not first <= day < last:
                    raise RestError("Schoolday outside school period")
            term = Term(name, first, last - datetime.date.resolution)
            for day in days:
                term.add(day)
        return term

    def parseXML(self, data, name=None):

        doc = XMLDocument(data, self.schema)
        try:
            doc.registerNs('m', 'http://schooltool.org/ns/schooldays/0.1')

            schooldays = doc.query('/m:schooldays')[0]
            first_attr = schooldays['first']
            last_attr = schooldays['last']

            first = parse_date(first_attr)
            last = parse_date(last_attr)
            holidays = [parse_date(node.content)
                        for node in doc.query('/m:schooldays/m:holiday/@date')]

            node = doc.query('/m:schooldays/m:daysofweek')[0]
            dows = [self._dow_map[d]
                    for d in node.content.split()]

            node = doc.query('/m:schooldays/m:title')[0]
            title = node.content

            term = Term(title, first, last)
            term.addWeekdays(*dows)
            for holiday in holidays:
                if holiday in term and term.isSchoolday(holiday):
                    term.remove(holiday)

            return term
        finally:
            doc.free()


class TermFile(object):
    """Adapter adapting Term to IWriteFile"""

    adapts(ITerm)
    implements(IWriteFile)

    def __init__(self, context):
        self.context = context

    def write(self, data):
        """See IWriteFile"""
        container = self.context.__parent__
        factory = IFileFactory(container)

        if factory.isDataICal(data):
            term = factory.parseText(data)
        else:
            term = factory.parseXML(data)

        self.context.reset(term.first, term.last)
        for day in term:
            if term.isSchoolday(day):
                self.context.add(day)


class TermView(View):
    """iCalendar view for ITerm."""

    datetime_hook = datetime.datetime

    def GET(self):
        end_date = self.context.last + datetime.date.resolution
        uid_suffix = "%s@%s" % (getPath(self.context),
                                # XXX not a very nice way (cutting http://)
                                self.request._app_server[7:])
        dtstamp = self.datetime_hook.utcnow().strftime("%Y%m%dT%H%M%SZ")
        result = [
            "BEGIN:VCALENDAR",
            "PRODID:-//SchoolTool.org/NONSGML SchoolTool//EN",
            "VERSION:2.0",
            "BEGIN:VEVENT",
            "UID:school-period-%s" % uid_suffix,
            "SUMMARY:School Period",
            "DTSTART;VALUE=DATE:%s" % self.context.first.strftime("%Y%m%d"),
            "DTEND;VALUE=DATE:%s" % end_date.strftime("%Y%m%d"),
            "DTSTAMP:%s" % dtstamp,
            "END:VEVENT",
        ]
        for date in self.context:
            if self.context.isSchoolday(date):
                s = date.strftime("%Y%m%d")
                result += [
                    "BEGIN:VEVENT",
                    "UID:schoolday-%s-%s" % (s, uid_suffix),
                    "SUMMARY:Schoolday",
                    "DTSTART;VALUE=DATE:%s" % s,
                    "DTSTAMP:%s" % dtstamp,
                    "END:VEVENT",
                ]
        result.append("END:VCALENDAR")
        self.request.response.setHeader('Content-Type',
                                        'text/calendar; charset=UTF-8')
        return "\r\n".join(result) + "\r\n"
