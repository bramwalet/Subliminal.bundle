# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'Trie', u'TrieNode')


class TrieNode(object):
    u'Class representing a single Trie node.'
    __slots__ = (u'children', u'exception', u'leaf', u'private')

    def __init__(self):
        self.children = None
        self.exception = None
        self.leaf = False
        self.private = False


class Trie(object):
    u'An adhoc Trie data structure to store tlds in reverse notation order.'

    def __init__(self):
        self.root = TrieNode()
        self.__nodes = 0

    def __len__(self):
        return self.__nodes

    def add(self, tld, private=False):
        node = self.root
        for part in reversed(tld.split(u'.')):
            if part.startswith(u'!'):
                node.exception = part[1:]
                break
            if (node.children is None):
                node.children = {

                }
                child = TrieNode()
            else:
                child = node.children.get(part)
                if (child is None):
                    child = TrieNode()
            node.children[part] = child
            node = child
        node.leaf = True
        if private:
            node.private = True
        self.__nodes += 1
