# coding=utf-8


class PunctuationMixin(object):
    """
    provider mixin

    fixes show ids for stuff like "Mr. Petterson", as our matcher already sees it as "Mr Petterson" but addic7ed doesn't
    """
    def clean_punctuation(self, s):
	return s.replace(".", "").replace(":", "").replace("'", "")

