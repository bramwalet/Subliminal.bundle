# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from six import with_metaclass as _py_backwards_six_withmetaclass
from codecs import open as codecs_open
try:
    from urllib.request import urlopen
except ImportError:
    from six.moves.urllib.request import urlopen as urlopen
from .exceptions import TldIOError, TldImproperlyConfigured
from .helpers import project_dir
from .registry import Registry
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'BaseTLDSourceParser',)


class BaseTLDSourceParser(
        _py_backwards_six_withmetaclass(Registry, *[object])):
    u'Base TLD source parser.'
    uid = None
    source_url = None
    local_path = None

    @classmethod
    def validate(cls):
        u'Constructor.'
        if (not cls.uid):
            raise TldImproperlyConfigured(
                u'The `uid` property of the TLD source parser shall be defined.')

    @classmethod
    def get_tld_names(cls, fail_silently=False, retry_count=0):
        u'Get tld names.\n\n        :param fail_silently:\n        :param retry_count:\n        :return:\n        '
        cls.validate()
        raise NotImplementedError(
            u'Your TLD source parser shall implement `get_tld_names` method.')

    @classmethod
    def update_tld_names(cls, fail_silently=False):
        u'Update the local copy of the TLD file.\n\n        :param fail_silently:\n        :return:\n        '
        try:
            remote_file = urlopen(cls.source_url)
            local_file = codecs_open(project_dir(
                cls.local_path), u'wb', encoding='utf8')
            local_file.write(remote_file.read().decode(u'utf8'))
            local_file.close()
            remote_file.close()
        except Exception as err:
            if fail_silently:
                return False
            raise TldIOError(err)
        return True
