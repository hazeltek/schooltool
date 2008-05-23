#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2006 Shuttleworth Foundation
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

from zope.app.component.hooks import getSite, setSite
from zope.app.component.interfaces import ISite
from zope.component import queryUtility
from zope.traversing.api import traverse


class UtilitySpecification(object):
    """A specification of a utility.

    A utility gets:

    factory - the factory creating the utility.
    iface - the interface provided by the utility (by which it is looked up)
    name - optional utility name
    setUp - an optional setUp function for the utility. This can
            for instance be used for setting up indexes in a catalog.
            The setUp function gets passed the utility as an argument.
    override - override previous local utility setups. Replaces that
               utility with this one. Defaults to False
    storage_name - name the utility as visible in the ZMI.
                   If not specified will be autogenerated.
    """

    def __init__(self, factory, iface, name='', setUp=None,
                 override=False, storage_name=None):
        if storage_name is None:
            storage_name = iface.__module__ + '.' + iface.__name__
            if name:
                storage_name += '.' + name
        self.storage_name = storage_name
        self.factory = factory
        self.setUp = setUp
        self.iface = iface
        self.utility_name = name
        self.override = override


def setUpUtilities(site, specs):
   manager = site.getSiteManager()
   default = traverse(site, '++etc++site/default')
   for spec in specs:
       local_utility = getLocalUtility(default, spec)
       if local_utility is not None:
           if spec.override:
               # override existing utility
               name = local_utility.__name__
               manager.unregisterUtility(local_utility, spec.iface, name)
               del default[name]
           else:
               # do not register this utility; we already got it
               continue
       utility = spec.factory()
       default[spec.storage_name] = utility
       if spec.setUp is not None:
           spec.setUp(utility)
       manager.registerUtility(utility, spec.iface, spec.utility_name)


def getLocalUtility(default, spec):
    util = queryUtility(spec.iface, name=spec.utility_name, default=None)
    if util is None or getattr(util, '__parent__', None) is default:
        return util
    else:
        return None


class UtilitySetUp(UtilitySpecification):
    """Set up a single utility."""

    def __call__(self, event):
        site = event.object
        setUpUtilities(site, [self])


class MultiUtilitySetUp(object):
    """Set up multiple related utilities that need to be in order.

    (for instance intids needs to be set up before the catalog is).
    """

    def __init__(self, *specifications):
        self.specifications = specifications

    def __call__(self, event):
        site = event.object
        setUpUtilities(site, self.specifications)
