# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from typing import Any
from . import defaults
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'get_setting', u'reset_settings', u'set_setting', u'settings')


class Settings(object):
    u'Settings registry.'

    def __init__(self):
        self._settings = {

        }
        self._settings_get = self._settings.get

    def set(self, name, value):
        u'\n        Override default settings.\n\n        :param str name:\n        :param mixed value:\n        '
        self._settings[name] = value

    def get(self, name, default=None):
        u'\n        Gets a variable from local settings.\n\n        :param str name:\n        :param mixed default: Default value.\n        :return mixed:\n        '
        if (name in self._settings):
            return self._settings_get(name, default)
        elif hasattr(defaults, name):
            return getattr(defaults, name, default)
        return default

    def reset(self):
        u'Reset settings.'
        for name in defaults.__all__:
            self.set(name, getattr(defaults, name))


settings = Settings()
get_setting = settings.get
set_setting = settings.set
reset_settings = settings.reset
