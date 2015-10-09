# coding=utf-8


class PunctuationMixin(object):
    def clean_punctuation(self, s):
        # fixes show ids for stuff like "Mr. Petterson", as our matcher already sees it as "Mr Petterson" but addic7ed doesn't
	return s.replace(".", "")