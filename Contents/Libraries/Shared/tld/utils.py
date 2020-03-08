# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import unicode_literals
import argparse
from codecs import open as codecs_open
from backports.functools_lru_cache import lru_cache
from os.path import isabs
import sys
from typing import Dict, Type, Union, Tuple, List
try:
    from urllib.parse import urlsplit, SplitResult
except ImportError:
    from six.moves.urllib_parse import urlsplit, SplitResult
from .base import BaseTLDSourceParser
from .exceptions import TldBadUrl, TldDomainNotFound, TldImproperlyConfigured, TldIOError
from .helpers import project_dir
from .trie import Trie
from .registry import Registry
from .result import Result
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'BaseMozillaTLDSourceParser', u'get_fld', u'get_tld', u'get_tld_names', u'get_tld_names_container', u'is_tld', u'MozillaTLDSourceParser', u'parse_tld',
           u'pop_tld_names_container', u'process_url', u'reset_tld_names', u'Result', u'update_tld_names', u'update_tld_names_cli', u'update_tld_names_container')
tld_names = {

}


def get_tld_names_container():
    u'Get container of all tld names.\n\n    :return:\n    :rtype dict:\n    '
    global tld_names
    return tld_names


def update_tld_names_container(tld_names_local_path, trie_obj):
    u'Update TLD Names container item.\n\n    :param tld_names_local_path:\n    :param trie_obj:\n    :return:\n    '
    global tld_names
    tld_names.update({
        tld_names_local_path: trie_obj,
    })


def pop_tld_names_container(tld_names_local_path):
    u'Remove TLD names container item.\n\n    :param tld_names_local_path:\n    :return:\n    '
    global tld_names
    tld_names.pop(tld_names_local_path, None)


@lru_cache(maxsize=128, typed=True)
def update_tld_names(fail_silently=False, parser_uid=None):
    u'Update TLD names.\n\n    :param fail_silently:\n    :param parser_uid:\n    :return:\n    '
    results = []
    results_append = results.append
    if parser_uid:
        parser_cls = Registry.get(parser_uid, None)
        if (parser_cls and parser_cls.source_url):
            results_append(parser_cls.update_tld_names(
                fail_silently=fail_silently))
    else:
        for (parser_uid, parser_cls) in Registry.items():
            if (parser_cls and parser_cls.source_url):
                results_append(parser_cls.update_tld_names(
                    fail_silently=fail_silently))
    return all(results)


def update_tld_names_cli():
    u'CLI wrapper for update_tld_names.\n\n    Since update_tld_names returns True on success, we need to negate the\n    result to match CLI semantics.\n    '
    parser = argparse.ArgumentParser(description='Update TLD names')
    parser.add_argument(u'parser_uid', nargs='?', default=None,
                        help='UID of the parser to update TLD names for.')
    parser.add_argument(u'--fail-silently', dest='fail_silently',
                        default=False, action='store_true', help='Fail silently')
    args = parser.parse_args(sys.argv[1:])
    parser_uid = args.parser_uid
    fail_silently = args.fail_silently
    return int((not update_tld_names(parser_uid=parser_uid, fail_silently=fail_silently)))


def get_tld_names(fail_silently=False, retry_count=0, parser_class=None):
    u'Build the ``tlds`` list if empty. Recursive.\n\n    :param fail_silently: If set to True, no exceptions are raised and None\n        is returned on failure.\n    :param retry_count: If greater than 1, we raise an exception in order\n        to avoid infinite loops.\n    :param parser_class:\n    :type fail_silently: bool\n    :type retry_count: int\n    :type parser_class: BaseTLDSourceParser\n    :return: List of TLD names\n    :rtype: obj:`tld.utils.Trie`\n    '
    if (not parser_class):
        parser_class = MozillaTLDSourceParser
    return parser_class.get_tld_names(fail_silently=fail_silently, retry_count=retry_count)


class BaseMozillaTLDSourceParser(BaseTLDSourceParser):

    @classmethod
    def get_tld_names(cls, fail_silently=False, retry_count=0):
        u'Parse.\n\n        :param fail_silently:\n        :param retry_count:\n        :return:\n        '
        if (retry_count > 1):
            if fail_silently:
                return None
            else:
                raise TldIOError
        global tld_names
        _tld_names = tld_names
        if ((cls.local_path in _tld_names) and (_tld_names[cls.local_path] is not None)):
            return _tld_names
        local_file = None
        try:
            if isabs(cls.local_path):
                local_path = cls.local_path
            else:
                local_path = project_dir(cls.local_path)
            local_file = codecs_open(local_path, u'r', encoding='utf8')
            trie = Trie()
            trie_add = trie.add
            private_section = False
            for line in local_file:
                if (u'===BEGIN PRIVATE DOMAINS===' in line):
                    private_section = True
                if (u'// xn--' in line):
                    line = line.split()[1]
                if (line[0] in (u'/', u'\n')):
                    continue
                trie_add(u''.join([u'{}'.format(line.strip())]),
                         private=private_section)
            update_tld_names_container(cls.local_path, trie)
            local_file.close()
        except IOError as err:
            cls.update_tld_names(fail_silently=fail_silently)
            retry_count += 1
            return cls.get_tld_names(fail_silently=fail_silently, retry_count=retry_count)
        except Exception as err:
            if fail_silently:
                return None
            else:
                raise err
        finally:
            try:
                local_file.close()
            except Exception:
                pass
        return _tld_names


class MozillaTLDSourceParser(BaseMozillaTLDSourceParser):
    u'Mozilla TLD source.'
    uid = u'mozilla'
    source_url = u'http://mxr.mozilla.org/mozilla/source/netwerk/dns/src/effective_tld_names.dat?raw=1'
    local_path = u'res/effective_tld_names.dat.txt'


def process_url(url, fail_silently=False, fix_protocol=False, search_public=True, search_private=True, parser_class=MozillaTLDSourceParser):
    u'Process URL.\n\n    :param parser_class:\n    :param url:\n    :param fail_silently:\n    :param fix_protocol:\n    :param search_public:\n    :param search_private:\n    :return:\n    '
    if (not (search_public or search_private)):
        raise TldImproperlyConfigured(
            u'Either `search_public` or `search_private` (or both) shall be set to True.')
    _tld_names = get_tld_names(
        fail_silently=fail_silently, parser_class=parser_class)
    if (not isinstance(url, SplitResult)):
        url = url.lower()
        if (fix_protocol and (not url.startswith((u'//', u'http://', u'https://')))):
            url = u''.join([u'https://', u'{}'.format(url)])
        parsed_url = urlsplit(url)
    else:
        parsed_url = url
    domain_name = parsed_url.hostname
    if (not domain_name):
        if fail_silently:
            return (None, None, parsed_url)
        else:
            raise TldBadUrl(url=url)
    domain_parts = domain_name.split(u'.')
    tld_names_local_path = parser_class.local_path
    node = _tld_names[tld_names_local_path].root
    current_length = 0
    tld_length = 0
    match = None
    len_domain_parts = len(domain_parts)
    for i in reversed(range(len_domain_parts)):
        part = domain_parts[i]
        if (node.children is None):
            break
        if (part == node.exception):
            break
        child = node.children.get(part)
        if (child is None):
            child = node.children.get(u'*')
        if (child is None):
            break
        current_length += 1
        node = child
        if node.leaf:
            tld_length = current_length
            match = node
    if ((match is None) or (not match.leaf) or ((not search_public) and (not match.private)) or ((not search_private) and match.private)):
        if fail_silently:
            return (None, None, parsed_url)
        else:
            raise TldDomainNotFound(domain_name=domain_name)
    if (len_domain_parts == tld_length):
        non_zero_i = (- 1)
    else:
        non_zero_i = max(1, (len_domain_parts - tld_length))
    return (domain_parts, non_zero_i, parsed_url)


def get_fld(url, fail_silently=False, fix_protocol=False, search_public=True, search_private=True, parser_class=MozillaTLDSourceParser, **kwargs):
    u"Extract the first level domain.\n\n    Extract the top level domain based on the mozilla's effective TLD names\n    dat file. Returns a string. May throw ``TldBadUrl`` or\n    ``TldDomainNotFound`` exceptions if there's bad URL provided or no TLD\n    match found respectively.\n\n    :param url: URL to get top level domain from.\n    :param fail_silently: If set to True, no exceptions are raised and None\n        is returned on failure.\n    :param fix_protocol: If set to True, missing or wrong protocol is\n        ignored (https is appended instead).\n    :param search_public: If set to True, search in public domains.\n    :param search_private: If set to True, search in private domains.\n    :param parser_class:\n    :type url: str\n    :type fail_silently: bool\n    :type fix_protocol: bool\n    :type search_public: bool\n    :type search_private: bool\n    :return: String with top level domain (if ``as_object`` argument\n        is set to False) or a ``tld.utils.Result`` object (if ``as_object``\n        argument is set to True); returns None on failure.\n    :rtype: str\n    "
    if (u'as_object' in kwargs):
        raise TldImproperlyConfigured(
            u'`as_object` argument is deprecated for `get_fld`. Use `get_tld` instead.')
    (domain_parts, non_zero_i, parsed_url) = process_url(url=url, fail_silently=fail_silently,
                                                         fix_protocol=fix_protocol, search_public=search_public, search_private=search_private, parser_class=parser_class)
    if (domain_parts is None):
        return None
    if (non_zero_i < 0):
        return parsed_url.hostname
    return u'.'.join(domain_parts[(non_zero_i - 1):])


def get_tld(url, fail_silently=False, as_object=False, fix_protocol=False, search_public=True, search_private=True, parser_class=MozillaTLDSourceParser):
    u"Extract the top level domain.\n\n    Extract the top level domain based on the mozilla's effective TLD names\n    dat file. Returns a string. May throw ``TldBadUrl`` or\n    ``TldDomainNotFound`` exceptions if there's bad URL provided or no TLD\n    match found respectively.\n\n    :param url: URL to get top level domain from.\n    :param fail_silently: If set to True, no exceptions are raised and None\n        is returned on failure.\n    :param as_object: If set to True, ``tld.utils.Result`` object is returned,\n        ``domain``, ``suffix`` and ``tld`` properties.\n    :param fix_protocol: If set to True, missing or wrong protocol is\n        ignored (https is appended instead).\n    :param search_public: If set to True, search in public domains.\n    :param search_private: If set to True, search in private domains.\n    :param parser_class:\n    :type url: str\n    :type fail_silently: bool\n    :type as_object: bool\n    :type fix_protocol: bool\n    :type search_public: bool\n    :type search_private: bool\n    :return: String with top level domain (if ``as_object`` argument\n        is set to False) or a ``tld.utils.Result`` object (if ``as_object``\n        argument is set to True); returns None on failure.\n    :rtype: str\n    "
    (domain_parts, non_zero_i, parsed_url) = process_url(url=url, fail_silently=fail_silently,
                                                         fix_protocol=fix_protocol, search_public=search_public, search_private=search_private, parser_class=parser_class)
    if (domain_parts is None):
        return None
    if (not as_object):
        if (non_zero_i < 0):
            return parsed_url.hostname
        return u'.'.join(domain_parts[non_zero_i:])
    if (non_zero_i < 0):
        subdomain = u''
        domain = u''
        _tld = parsed_url.hostname
    else:
        subdomain = u'.'.join(domain_parts[:(non_zero_i - 1)])
        domain = u'.'.join(domain_parts[(non_zero_i - 1):non_zero_i])
        _tld = u'.'.join(domain_parts[non_zero_i:])
    return Result(subdomain=subdomain, domain=domain, tld=_tld, parsed_url=parsed_url)


def parse_tld(url, fail_silently=False, fix_protocol=False, search_public=True, search_private=True, parser_class=MozillaTLDSourceParser):
    u'Parse TLD into parts.\n\n    :param url:\n    :param fail_silently:\n    :param fix_protocol:\n    :param search_public:\n    :param search_private:\n    :param parser_class:\n    :return:\n    :rtype: tuple\n    '
    try:
        obj = get_tld(url, fail_silently=fail_silently, as_object=True, fix_protocol=fix_protocol,
                      search_public=search_public, search_private=search_private, parser_class=parser_class)
        _tld = obj.tld
        domain = obj.domain
        subdomain = obj.subdomain
    except (TldBadUrl, TldDomainNotFound, TldImproperlyConfigured, TldIOError):
        _tld = None
        domain = None
        subdomain = None
    return (_tld, domain, subdomain)


def is_tld(value, search_public=True, search_private=True, parser_class=MozillaTLDSourceParser):
    u'Check if given URL is tld.\n\n    :param value: URL to get top level domain from.\n    :param search_public: If set to True, search in public domains.\n    :param search_private: If set to True, search in private domains.\n    :param parser_class:\n    :type value: str\n    :type search_public: bool\n    :type search_private: bool\n    :return:\n    :rtype: bool\n    '
    _tld = get_tld(url=value, fail_silently=True, fix_protocol=True,
                   search_public=search_public, search_private=search_private, parser_class=parser_class)
    return (value == _tld)


def reset_tld_names(tld_names_local_path=None):
    u'Reset the ``tld_names`` to empty value.\n\n    If ``tld_names_local_path`` is given, removes specified\n    entry from ``tld_names`` instead.\n\n    :param tld_names_local_path:\n    :type tld_names_local_path: str\n    :return:\n    '
    if tld_names_local_path:
        pop_tld_names_container(tld_names_local_path)
    else:
        global tld_names
        tld_names = {

        }
