# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from .conf import get_setting
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'TldBadUrl', u'TldDomainNotFound',
           u'TldImproperlyConfigured', u'TldIOError')


class TldIOError(IOError):
    u'TldIOError.\n\n    Supposed to be thrown when problems with reading/writing occur.\n    '

    def __init__(self, msg=None):
        tld_names_local_path = get_setting(u'NAMES_LOCAL_PATH')
        if (msg is None):
            msg = (u"Can't read from or write to the %s file!" %
                   tld_names_local_path)
        super(TldIOError, self).__init__(msg)


class TldDomainNotFound(ValueError):
    u"TldDomainNotFound.\n\n    Supposed to be thrown when domain name is not found (didn't match) the\n    local TLD policy.\n    "

    def __init__(self, domain_name):
        super(TldDomainNotFound, self).__init__(
            (u"Domain %s didn't match any existing TLD name!" % domain_name))


class TldBadUrl(ValueError):
    u'TldBadUrl.\n\n    Supposed to be thrown when bad URL is given.\n    '

    def __init__(self, url):
        super(TldBadUrl, self).__init__((u'Is not a valid URL %s!' % url))


class TldImproperlyConfigured(Exception):
    u'TldImproperlyConfigured.\n\n    Supposed to be thrown when code is improperly configured. Typical use-case\n    is when user tries to use `get_tld` function with both `search_public` and\n    `search_private` set to False.\n    '

    def __init__(self, msg=None):
        if (msg is None):
            msg = u'Improperly configured.'
        else:
            msg = (u'Improperly configured. %s' % msg)
        super(TldImproperlyConfigured, self).__init__(msg)
