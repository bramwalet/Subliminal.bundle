# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import logging
from os.path import abspath, join
import unittest
from tempfile import gettempdir
from typing import Type
try:
    from urllib.parse import urlsplit
except ImportError:
    from six.moves.urllib_parse import urlsplit
from faker import Faker
from .. import defaults
from ..base import BaseTLDSourceParser
from ..conf import get_setting, reset_settings, set_setting
from ..exceptions import TldBadUrl, TldDomainNotFound, TldImproperlyConfigured, TldIOError
from ..helpers import project_dir
from ..registry import Registry
from ..utils import get_fld, get_tld, get_tld_names, get_tld_names_container, is_tld, MozillaTLDSourceParser, BaseMozillaTLDSourceParser, parse_tld, reset_tld_names, update_tld_names, update_tld_names_cli
from .base import internet_available_only, log_info
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'TestCore',)
LOGGER = logging.getLogger(__name__)


class TestCore(unittest.TestCase):
    u'Core tld functionality tests.'

    @classmethod
    def setUpClass(cls):
        cls.faker = Faker()
        cls.temp_dir = gettempdir()

    def setUp(self):
        u'Set up.'
        self.good_patterns = [{
            u'url': u'http://www.google.co.uk',
            u'fld': u'google.co.uk',
            u'subdomain': u'www',
            u'domain': u'google',
            u'suffix': u'co.uk',
            u'tld': u'co.uk',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://www.v2.google.co.uk',
            u'fld': u'google.co.uk',
            u'subdomain': u'www.v2',
            u'domain': u'google',
            u'suffix': u'co.uk',
            u'tld': u'co.uk',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://хром.гугл.рф',
            u'fld': u'гугл.рф',
            u'subdomain': u'хром',
            u'domain': u'гугл',
            u'suffix': u'рф',
            u'tld': u'рф',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://www.google.co.uk:8001/lorem-ipsum/',
            u'fld': u'google.co.uk',
            u'subdomain': u'www',
            u'domain': u'google',
            u'suffix': u'co.uk',
            u'tld': u'co.uk',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://www.me.cloudfront.net',
            u'fld': u'me.cloudfront.net',
            u'subdomain': u'www',
            u'domain': u'me',
            u'suffix': u'cloudfront.net',
            u'tld': u'cloudfront.net',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://www.v2.forum.tech.google.co.uk:8001/lorem-ipsum/',
            u'fld': u'google.co.uk',
            u'subdomain': u'www.v2.forum.tech',
            u'domain': u'google',
            u'suffix': u'co.uk',
            u'tld': u'co.uk',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'https://pantheon.io/',
            u'fld': u'pantheon.io',
            u'subdomain': u'',
            u'domain': u'pantheon',
            u'suffix': u'io',
            u'tld': u'io',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'v2.www.google.com',
            u'fld': u'google.com',
            u'subdomain': u'v2.www',
            u'domain': u'google',
            u'suffix': u'com',
            u'tld': u'com',
            u'kwargs': {
                u'fail_silently': True,
                u'fix_protocol': True,
            },
        }, {
            u'url': u'//v2.www.google.com',
            u'fld': u'google.com',
            u'subdomain': u'v2.www',
            u'domain': u'google',
            u'suffix': u'com',
            u'tld': u'com',
            u'kwargs': {
                u'fail_silently': True,
                u'fix_protocol': True,
            },
        }, {
            u'url': u'http://foo@bar.com',
            u'fld': u'bar.com',
            u'subdomain': u'',
            u'domain': u'bar',
            u'suffix': u'com',
            u'tld': u'com',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://user:foo@bar.com',
            u'fld': u'bar.com',
            u'subdomain': u'',
            u'domain': u'bar',
            u'suffix': u'com',
            u'tld': u'com',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'https://faguoren.xn--fiqs8s',
            u'fld': u'faguoren.xn--fiqs8s',
            u'subdomain': u'',
            u'domain': u'faguoren',
            u'suffix': u'xn--fiqs8s',
            u'tld': u'xn--fiqs8s',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'blogs.lemonde.paris',
            u'fld': u'lemonde.paris',
            u'subdomain': u'blogs',
            u'domain': u'lemonde',
            u'suffix': u'paris',
            u'tld': u'paris',
            u'kwargs': {
                u'fail_silently': True,
                u'fix_protocol': True,
            },
        }, {
            u'url': u'axel.brighton.ac.uk',
            u'fld': u'brighton.ac.uk',
            u'subdomain': u'axel',
            u'domain': u'brighton',
            u'suffix': u'ac.uk',
            u'tld': u'ac.uk',
            u'kwargs': {
                u'fail_silently': True,
                u'fix_protocol': True,
            },
        }, {
            u'url': u'm.fr.blogspot.com.au',
            u'fld': u'fr.blogspot.com.au',
            u'subdomain': u'm',
            u'domain': u'fr',
            u'suffix': u'blogspot.com.au',
            u'tld': u'blogspot.com.au',
            u'kwargs': {
                u'fail_silently': True,
                u'fix_protocol': True,
            },
        }, {
            u'url': u'help.www.福岡.jp',
            u'fld': u'www.福岡.jp',
            u'subdomain': u'help',
            u'domain': u'www',
            u'suffix': u'福岡.jp',
            u'tld': u'福岡.jp',
            u'kwargs': {
                u'fail_silently': True,
                u'fix_protocol': True,
            },
        }, {
            u'url': u'syria.arabic.variant.سوريا',
            u'fld': u'variant.سوريا',
            u'subdomain': u'syria.arabic',
            u'domain': u'variant',
            u'suffix': u'سوريا',
            u'tld': u'سوريا',
            u'kwargs': {
                u'fail_silently': True,
                u'fix_protocol': True,
            },
        }, {
            u'url': u'http://www.help.kawasaki.jp',
            u'fld': u'www.help.kawasaki.jp',
            u'subdomain': u'',
            u'domain': u'www',
            u'suffix': u'help.kawasaki.jp',
            u'tld': u'help.kawasaki.jp',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://www.city.kawasaki.jp',
            u'fld': u'city.kawasaki.jp',
            u'subdomain': u'www',
            u'domain': u'city',
            u'suffix': u'kawasaki.jp',
            u'tld': u'kawasaki.jp',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://fedoraproject.org',
            u'fld': u'fedoraproject.org',
            u'subdomain': u'',
            u'domain': u'fedoraproject',
            u'suffix': u'org',
            u'tld': u'org',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://www.cloud.fedoraproject.org',
            u'fld': u'www.cloud.fedoraproject.org',
            u'subdomain': u'',
            u'domain': u'www',
            u'suffix': u'cloud.fedoraproject.org',
            u'tld': u'cloud.fedoraproject.org',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'https://www.john.app.os.fedoraproject.org',
            u'fld': u'john.app.os.fedoraproject.org',
            u'subdomain': u'www',
            u'domain': u'john',
            u'suffix': u'app.os.fedoraproject.org',
            u'tld': u'app.os.fedoraproject.org',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'ftp://www.xn--mxail5aa.xn--11b4c3d',
            u'fld': u'xn--mxail5aa.xn--11b4c3d',
            u'subdomain': u'www',
            u'domain': u'xn--mxail5aa',
            u'suffix': u'xn--11b4c3d',
            u'tld': u'xn--11b4c3d',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://cloud.fedoraproject.org',
            u'fld': u'cloud.fedoraproject.org',
            u'subdomain': u'',
            u'domain': u'cloud.fedoraproject.org',
            u'suffix': u'cloud.fedoraproject.org',
            u'tld': u'cloud.fedoraproject.org',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'github.io',
            u'fld': u'github.io',
            u'subdomain': u'',
            u'domain': u'github.io',
            u'suffix': u'github.io',
            u'tld': u'github.io',
            u'kwargs': {
                u'fail_silently': True,
                u'fix_protocol': True,
            },
        }, {
            u'url': urlsplit(u'http://lemonde.fr/article.html'),
            u'fld': u'lemonde.fr',
            u'subdomain': u'',
            u'domain': u'lemonde',
            u'suffix': u'fr',
            u'tld': u'fr',
            u'kwargs': {
                u'fail_silently': True,
            },
        }]
        self.bad_patterns = {
            u'v2.www.google.com': {
                u'exception': TldBadUrl,
            },
            u'/index.php?a=1&b=2': {
                u'exception': TldBadUrl,
            },
            u'http://www.tld.doesnotexist': {
                u'exception': TldDomainNotFound,
            },
            u'https://2001:0db8:0000:85a3:0000:0000:ac1f:8001': {
                u'exception': TldDomainNotFound,
            },
            u'http://192.169.1.1': {
                u'exception': TldDomainNotFound,
            },
            u'http://localhost:8080': {
                u'exception': TldDomainNotFound,
            },
            u'https://localhost': {
                u'exception': TldDomainNotFound,
            },
            u'https://localhost2': {
                u'exception': TldImproperlyConfigured,
                u'kwargs': {
                    u'search_public': False,
                    u'search_private': False,
                },
            },
        }
        self.invalid_tlds = {u'v2.www.google.com', u'tld.doesnotexist',
                             u'2001:0db8:0000:85a3:0000:0000:ac1f', u'192.169.1.1', 'localhost', u'google.com'}
        self.tld_names_local_path_custom = project_dir(
            join(u'tests', u'res', u'effective_tld_names_custom.dat.txt'))
        self.good_patterns_custom_parser = [{
            u'url': u'http://www.foreverchild',
            u'fld': u'www.foreverchild',
            u'subdomain': u'',
            u'domain': u'www',
            u'suffix': u'foreverchild',
            u'tld': u'foreverchild',
            u'kwargs': {
                u'fail_silently': True,
            },
        }, {
            u'url': u'http://www.v2.foreverchild',
            u'fld': u'v2.foreverchild',
            u'subdomain': u'www',
            u'domain': u'v2',
            u'suffix': u'foreverchild',
            u'tld': u'foreverchild',
            u'kwargs': {
                u'fail_silently': True,
            },
        }]
        reset_settings()

    def tearDown(self):
        u'Tear down.'
        reset_settings()
        Registry.reset()

    @property
    def good_url(self):
        return self.good_patterns[0][u'url']

    @property
    def bad_url(self):
        return list(self.bad_patterns.keys())[0]

    def get_custom_parser_class(self, uid='custom_mozilla', source_url=None, local_path='tests/res/effective_tld_names_custom.dat.txt'):
        parser_class = type('CustomMozillaTLDSourceParser', (BaseMozillaTLDSourceParser,), {
            'uid': uid,
            'source_url': source_url,
            'local_path': local_path,
        })
        return parser_class

    @log_info
    def test_0_tld_names_loaded(self):
        u'Test if tld names are loaded.'
        get_fld(u'http://www.google.co.uk')
        from ..utils import tld_names
        res = (len(tld_names) > 0)
        self.assertTrue(res)
        return res

    @internet_available_only
    @log_info
    def test_1_update_tld_names(self):
        u'Test updating the tld names (re-fetch mozilla source).'
        res = update_tld_names(fail_silently=False)
        self.assertTrue(res)
        return res

    @log_info
    def test_2_fld_good_patterns_pass(self):
        u'Test good URL patterns.'
        res = []
        for data in self.good_patterns:
            _res = get_fld(data[u'url'], **data[u'kwargs'])
            self.assertEqual(_res, data[u'fld'])
            res.append(_res)
        return res

    @log_info
    def test_3_fld_bad_patterns_pass(self):
        u'Test bad URL patterns.'
        res = []
        for (url, params) in self.bad_patterns.items():
            _res = get_fld(url, fail_silently=True)
            self.assertEqual(_res, None)
            res.append(_res)
        return res

    @log_info
    def test_4_override_settings(self):
        u'Testing settings override.'

        def override_settings():
            u'Override settings.'
            return get_setting(u'DEBUG')
        self.assertEqual(defaults.DEBUG, override_settings())
        set_setting(u'DEBUG', True)
        self.assertEqual(True, override_settings())
        return override_settings()

    @log_info
    def test_5_tld_good_patterns_pass_parsed_object(self):
        u'Test good URL patterns.'
        res = []
        for data in self.good_patterns:
            kwargs = copy.copy(data[u'kwargs'])
            kwargs.update({
                u'as_object': True,
            })
            _res = get_tld(data[u'url'], **kwargs)
            self.assertEqual(_res.tld, data[u'tld'])
            self.assertEqual(_res.subdomain, data[u'subdomain'])
            self.assertEqual(_res.domain, data[u'domain'])
            self.assertEqual(_res.suffix, data[u'suffix'])
            self.assertEqual(_res.fld, data[u'fld'])
            self.assertEqual(unicode(_res).encode(u'utf8'),
                             data[u'tld'].encode(u'utf8'))
            self.assertEqual(_res.__dict__, {
                u'tld': _res.tld,
                u'domain': _res.domain,
                u'subdomain': _res.subdomain,
                u'fld': _res.fld,
                u'parsed_url': _res.parsed_url,
            })
            res.append(_res)
        return res

    @log_info
    def test_6_override_full_names_path(self):
        default = project_dir(u'dummy.txt')
        override_base = u'/tmp/test'
        set_setting(u'NAMES_LOCAL_PATH_PARENT', override_base)
        modified = project_dir(u'dummy.txt')
        self.assertNotEqual(default, modified)
        self.assertEqual(modified, abspath(u'/tmp/test/dummy.txt'))

    @log_info
    def test_7_public_private(self):
        res = get_fld(u'http://silly.cc.ua',
                      fail_silently=True, search_private=False)
        self.assertEqual(res, None)
        res = get_fld(u'http://silly.cc.ua',
                      fail_silently=True, search_private=True)
        self.assertEqual(res, u'silly.cc.ua')
        res = get_fld(u'mercy.compute.amazonaws.com',
                      fail_silently=True, search_private=False, fix_protocol=True)
        self.assertEqual(res, None)
        res = get_fld(u'http://whatever.com',
                      fail_silently=True, search_public=False)
        self.assertEqual(res, None)

    @log_info
    def test_8_fld_bad_patterns_exceptions(self):
        u'Test exceptions.'
        res = []
        for (url, params) in self.bad_patterns.items():
            kwargs = (params[u'kwargs'] if (u'kwargs' in params) else {

            })
            kwargs.update({
                u'fail_silently': False,
            })
            with self.assertRaises(params[u'exception']):
                _res = get_fld(url, **kwargs)
                res.append(_res)
        return res

    @log_info
    def test_9_tld_good_patterns_pass(self):
        u'Test `get_tld` good URL patterns.'
        res = []
        for data in self.good_patterns:
            _res = get_tld(data[u'url'], **data[u'kwargs'])
            self.assertEqual(_res, data[u'tld'])
            res.append(_res)
        return res

    @log_info
    def test_10_tld_bad_patterns_pass(self):
        u'Test `get_tld` bad URL patterns.'
        res = []
        for (url, params) in self.bad_patterns.items():
            _res = get_tld(url, fail_silently=True)
            self.assertEqual(_res, None)
            res.append(_res)
        return res

    @log_info
    def test_11_parse_tld_good_patterns(self):
        u'Test `parse_tld` good URL patterns.'
        res = []
        for data in self.good_patterns:
            _res = parse_tld(data[u'url'], **data[u'kwargs'])
            self.assertEqual(
                _res, (data[u'tld'], data[u'domain'], data[u'subdomain']))
            res.append(_res)
        return res

    @log_info
    def test_12_is_tld_good_patterns(self):
        u'Test `is_tld` good URL patterns.'
        for data in self.good_patterns:
            self.assertTrue(is_tld(data[u'tld']))

    @log_info
    def test_13_is_tld_bad_patterns(self):
        u'Test `is_tld` bad URL patterns.'
        for _tld in self.invalid_tlds:
            self.assertFalse(is_tld(_tld))

    @log_info
    def test_14_fail_update_tld_names(self):
        u'Test fail `update_tld_names`.'
        parser_class = self.get_custom_parser_class(
            uid='custom_mozilla_2', source_url='i-do-not-exist')
        with self.assertRaises(TldIOError):
            update_tld_names(fail_silently=False, parser_uid=parser_class.uid)
        self.assertFalse(update_tld_names(
            fail_silently=True, parser_uid=parser_class.uid))

    @log_info
    def test_15_fail_get_fld_wrong_kwargs(self):
        u'Test fail `get_fld` with wrong kwargs.'
        with self.assertRaises(TldImproperlyConfigured):
            get_fld(self.good_url, as_object=True)

    @log_info
    def test_16_fail_parse_tld(self):
        u'Test fail `parse_tld`.\n\n        Assert raise TldIOError on wrong `NAMES_SOURCE_URL` for `parse_tld`.\n        '
        parser_class = self.get_custom_parser_class(
            source_url='i-do-not-exist')
        parsed_tld = parse_tld(
            self.bad_url, fail_silently=False, parser_class=parser_class)
        self.assertEqual(parsed_tld, (None, None, None))

    @log_info
    def test_17_get_tld_names_and_reset_tld_names(self):
        u'Test fail `get_tld_names` and repair using `reset_tld_names`.'
        tmp_filename = join(gettempdir(), u''.join(
            [u'{}'.format(self.faker.uuid4()), u'.dat.txt']))
        parser_class = self.get_custom_parser_class(
            source_url='i-do-not-exist', local_path=tmp_filename)
        reset_tld_names()
        if True:
            with self.assertRaises(TldIOError):
                get_tld_names(fail_silently=False, parser_class=parser_class)
        tmp_filename = join(gettempdir(), u''.join(
            [u'{}'.format(self.faker.uuid4()), u'.dat.txt']))
        parser_class_2 = self.get_custom_parser_class(
            source_url='i-do-not-exist-2', local_path=tmp_filename)
        reset_tld_names()
        if True:
            self.assertIsNone(get_tld_names(
                fail_silently=True, parser_class=parser_class_2))

    @internet_available_only
    @log_info
    def test_18_update_tld_names_cli(self):
        u'Test the return code of the CLI version of `update_tld_names`.'
        reset_tld_names()
        res = update_tld_names_cli()
        self.assertEqual(res, 0)

    @log_info
    def test_19_parse_tld_custom_tld_names_good_patterns(self):
        u'Test `parse_tld` good URL patterns for custom tld names.'
        res = []
        for data in self.good_patterns_custom_parser:
            kwargs = copy.copy(data[u'kwargs'])
            kwargs.update({
                u'parser_class': self.get_custom_parser_class(),
            })
            _res = parse_tld(data[u'url'], **kwargs)
            self.assertEqual(
                _res, (data[u'tld'], data[u'domain'], data[u'subdomain']))
            res.append(_res)
        return res

    @log_info
    def test_20_tld_custom_tld_names_good_patterns_pass_parsed_object(self):
        u'Test `get_tld` good URL patterns for custom tld names.'
        res = []
        for data in self.good_patterns_custom_parser:
            kwargs = copy.copy(data[u'kwargs'])
            kwargs.update({
                u'as_object': True,
                u'parser_class': self.get_custom_parser_class(),
            })
            _res = get_tld(data[u'url'], **kwargs)
            self.assertEqual(_res.tld, data[u'tld'])
            self.assertEqual(_res.subdomain, data[u'subdomain'])
            self.assertEqual(_res.domain, data[u'domain'])
            self.assertEqual(_res.suffix, data[u'suffix'])
            self.assertEqual(_res.fld, data[u'fld'])
            self.assertEqual(unicode(_res).encode(u'utf8'),
                             data[u'tld'].encode(u'utf8'))
            self.assertEqual(_res.__dict__, {
                u'tld': _res.tld,
                u'domain': _res.domain,
                u'subdomain': _res.subdomain,
                u'fld': _res.fld,
                u'parsed_url': _res.parsed_url,
            })
            res.append(_res)
        return res

    @log_info
    def test_21_reset_tld_names_for_custom_parser(self):
        u'Test `reset_tld_names` for `tld_names_local_path`.'
        res = []
        parser_class = self.get_custom_parser_class()
        for data in self.good_patterns_custom_parser:
            kwargs = copy.copy(data[u'kwargs'])
            kwargs.update({
                u'as_object': True,
                u'parser_class': self.get_custom_parser_class(),
            })
            _res = get_tld(data[u'url'], **kwargs)
            self.assertEqual(_res.tld, data[u'tld'])
            self.assertEqual(_res.subdomain, data[u'subdomain'])
            self.assertEqual(_res.domain, data[u'domain'])
            self.assertEqual(_res.suffix, data[u'suffix'])
            self.assertEqual(_res.fld, data[u'fld'])
            self.assertEqual(unicode(_res).encode(u'utf8'),
                             data[u'tld'].encode(u'utf8'))
            self.assertEqual(_res.__dict__, {
                u'tld': _res.tld,
                u'domain': _res.domain,
                u'subdomain': _res.subdomain,
                u'fld': _res.fld,
                u'parsed_url': _res.parsed_url,
            })
            res.append(_res)
        tld_names = get_tld_names_container()
        self.assertIn(parser_class.local_path, tld_names)
        reset_tld_names(parser_class.local_path)
        self.assertNotIn(parser_class.local_path, tld_names)
        return res

    @log_info
    def test_22_fail_define_custom_parser_class_without_uid(self):
        u'Test fail define custom parser class without `uid`.'

        class CustomParser(BaseTLDSourceParser):
            pass

        class AnotherCustomParser(BaseTLDSourceParser):
            uid = u'another-custom-parser'
        with self.assertRaises(TldImproperlyConfigured):
            CustomParser.get_tld_names()
        with self.assertRaises(NotImplementedError):
            AnotherCustomParser.get_tld_names()

    @log_info
    def test_23_len_trie_nodes(self):
        u'Test len of the trie nodes.'
        get_tld(u'http://delusionalinsanity.com')
        tld_names = get_tld_names_container()
        self.assertGreater(
            len(tld_names[MozillaTLDSourceParser.local_path]), 0)

    @log_info
    def test_24_get_tld_names_no_arguments(self):
        u'Test len of the trie nodes.'
        tld_names = get_tld_names()
        self.assertGreater(len(tld_names), 0)


if (__name__ == u'__main__'):
    unittest.main()
