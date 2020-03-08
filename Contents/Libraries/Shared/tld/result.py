# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from typing import Dict
try:
    from urllib.parse import SplitResult
except ImportError:
    from six.moves.urllib_parse import SplitResult
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'Result',)


class Result(object):
    u'Container.'
    __slots__ = (u'subdomain', u'domain', u'tld', u'__fld', u'parsed_url')

    def __init__(self, tld, domain, subdomain, parsed_url):
        self.tld = tld
        self.domain = (domain if (domain != u'') else tld)
        self.subdomain = subdomain
        self.parsed_url = parsed_url
        if domain:
            self.__fld = u''.join(
                [u'{}'.format(self.domain), u'.', u'{}'.format(self.tld)])
        else:
            self.__fld = self.tld

    @property
    def extension(self):
        u'Alias of ``tld``.\n\n        :return str:\n        '
        return self.tld
    suffix = extension

    @property
    def fld(self):
        u'First level domain.\n\n        :return:\n        :rtype: str\n        '
        return self.__fld

    def __str__(self):
        return self.tld
    __repr__ = __str__

    @property
    def __dict__(self):
        u'Mimic __dict__ functionality.\n\n        :return:\n        :rtype: dict\n        '
        return {
            u'tld': self.tld,
            u'domain': self.domain,
            u'subdomain': self.subdomain,
            u'fld': self.fld,
            u'parsed_url': self.parsed_url,
        }
