# coding=utf-8

import re

clean_whitespace_re = re.compile(r'\s+')


class PunctuationMixin(object):
    """
    provider mixin

    fixes show ids for stuff like "Mr. Petterson", as our matcher already sees it as "Mr Petterson" but addic7ed doesn't
    """

    def clean_punctuation(self, s):
        return s.replace(".", "").replace(":", "").replace("'", "").replace("&", "").replace("-", "")

    def clean_whitespace(self, s):
        return clean_whitespace_re.sub("", s)

    def full_clean(self, s):
        return self.clean_whitespace(self.clean_punctuation(s))
