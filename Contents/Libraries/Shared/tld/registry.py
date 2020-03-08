# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from typing import Type, Dict
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'Registry',)


class Registry(type):
    REGISTRY = {

    }

    def __new__(cls, name, bases, attrs):
        new_cls = type.__new__(cls, name, bases, attrs)
        if getattr(new_cls, u'_uid', None):
            cls.REGISTRY[new_cls._uid] = new_cls
        return new_cls

    @property
    def _uid(cls):
        return getattr(cls, 'uid', cls.__name__)

    @classmethod
    def reset(cls):
        cls.REGISTRY = {

        }

    @classmethod
    def get(cls, key, default=None):
        return cls.REGISTRY.get(key, default)

    @classmethod
    def items(cls):
        return cls.REGISTRY.items()
