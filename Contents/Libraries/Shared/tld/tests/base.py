# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from backports.functools_lru_cache import lru_cache
import logging
import socket
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'internet_available_only', u'log_info')
LOG_INFO = True
LOGGER = logging.getLogger(__name__)


def log_info(func):
    u'Log some useful info.'
    if (not LOG_INFO):
        return func

    def inner(self, *args, **kwargs):
        u'Inner.'
        result = func(*([self] + list(args)), **kwargs)
        LOGGER.debug(u'\n\n%s', func.__name__)
        LOGGER.debug(u'============================')
        if func.__doc__:
            LOGGER.debug(u'""" %s """', func.__doc__.strip())
        LOGGER.debug(u'----------------------------')
        if (result is not None):
            LOGGER.debug(result)
        LOGGER.debug(u'\n++++++++++++++++++++++++++++')
        return result
    return inner


@lru_cache(maxsize=32)
def is_internet_available(host='8.8.8.8', port=53, timeout=3):
    u'Check if internet is available.\n\n    Host: 8.8.8.8 (google-public-dns-a.google.com)\n    OpenPort: 53/tcp\n    Service: domain (DNS/TCP)\n    '
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False


def internet_available_only(func):

    def inner(self, *args, **kwargs):
        u'Inner.'
        if (not is_internet_available()):
            LOGGER.debug(u'\n\n%s', func.__name__)
            LOGGER.debug(u'============================')
            if func.__doc__:
                LOGGER.debug(u'""" %s """', func.__doc__.strip())
            LOGGER.debug(u'----------------------------')
            LOGGER.debug(u'Skipping because no Internet connection available.')
            LOGGER.debug(u'\n++++++++++++++++++++++++++++')
            return None
        result = func(*([self] + list(args)), **kwargs)
        return result
    return inner
