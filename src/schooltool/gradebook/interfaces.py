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
"""Gradebook interfaces

$Id$
"""
__docformat__ = 'reStructuredText'

import zope.interface
from schooltool.requirement import interfaces
from schooltool import SchoolToolMessage as _

class IActivities(interfaces.IRequirement):
    '''A list of activities that must be fulfilled in a course or section.'''

class IActivity(interfaces.IRequirement):
    '''An activity to be graded'''

    description = zope.schema.Text(
        title=_("Description"),
        description=_("A detailed description of the activity."),
        required=False)

    # XXX: Should be a choice field.
    category = zope.schema.TextLine(
        title=_("Category"),
        description=_("The activity category"),
        required=True)

    scoresystem = zope.interface.Attribute(
        'Score system to be used for the grading')

class IGradebook(zope.interface.Interface):
    """The gradebook of a section.

    The gradebook provides an API that allows the user to treat it like a
    gradebook spreadsheet/table.
    """

    def hasEvaluation(student, activity):
        """Check whether an evaluation exists for a student-activity pair."""

    def getEvaluation(student, activity):
        """Get the evaluation of a student for a given activity."""

    def evaluate(student, activity, score):
        """Evaluate a student for an activity"""

    def removeEvaluation(student, activity):
        """Remove evaluation."""

    def getEvaluationsForStudent(student):
        """Get the evaluations of the section for this student.

        Return iteratable of 2-tuples of the form (activity, evaluation).
        """

    def getEvaluationsForActivity(activity):
        """Get the evaluations of a particular activity in the section.

        Return iteratable of 2-tuples of the form (student, evaluation).
        """


class IStatistics(zope.interface.Interface):
    """Statistics for the gradebook"""

    def calculateAverage(activity):
        """Calculate the average of the activity."""

    def calculatePercentAverage(activity):
        """Calculate the average as a percentage for the activity."""

    def calculateMedian(activity):
        """Calculate the median of the activity."""

    def calculateStandardDeviation(activity):
        """Calculate the standard deviation of the activity."""

    def calculateVariance(activity):
        """Calculate the variance of the activity."""
