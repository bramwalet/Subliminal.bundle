# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest
import subprocess
from .base import log_info, internet_available_only
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'GPL 2.0/LGPL 2.1'
__all__ = (u'TestCommands',)
LOGGER = logging.getLogger(__name__)


class TestCommands(unittest.TestCase):
    u'Tld commands tests.'

    def setUp(self):
        u'Set up.'

    @internet_available_only
    @log_info
    def test_1_update_tld_names_command(self):
        u'Test updating the tld names (re-fetch mozilla source).'
        res = subprocess.check_output([u'update-tld-names']).strip()
        self.assertEqual(res, b'')
        return res

    @internet_available_only
    @log_info
    def test_1_update_tld_names_mozilla_command(self):
        u'Test updating the tld names (re-fetch mozilla source).'
        res = subprocess.check_output(
            [u'update-tld-names', u'mozilla']).strip()
        self.assertEqual(res, b'')
        return res


if (__name__ == u'__main__'):
    unittest.main()
