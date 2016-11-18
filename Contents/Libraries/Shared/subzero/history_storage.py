# coding=utf-8

import datetime

from subzero.lib.dict import DictProxy


class SubtitleHistoryItem(object):
    item_title = None
    section_title = None
    rating_key = None
    subtitle = None
    time = None

    def __init__(self, item_title, rating_key, section_title=None, subtitle=subtitle):
        self.item_title = item_title
        self.section_title = section_title
        self.rating_key = str(rating_key)
        self.subtitle = subtitle
        self.time = datetime.datetime.now()

    @property
    def title(self):
        return u"%s: %s" % (self.section_title, self.item_title)

    @property
    def score(self):
        return self.subtitle.score

    @property
    def provider_name(self):
        return self.subtitle.provider_name

    @property
    def lang_name(self):
        return self.subtitle.language.name

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return u"%s (Score: %s)" % (unicode(self.item_title), self.score)

    def __str__(self):
        return str(self.rating_key)

    def __hash__(self):
        return hash((self.rating_key, self.score))

    def __eq__(self, other):
        return (self.rating_key, self.score) == (other.rating_key, other.score)

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not (self == other)


class SubtitleHistory(DictProxy):
    store = "history"
    size = 100

    def __init__(self, storage, size=100):
        super(SubtitleHistory, self).__init__(storage)
        self.size = size

    def setup_defaults(self):
        return {"history_items": []}

    def add(self, item_title, rating_key, section_title=None, subtitle=None):
        # create copy
        items = self.history_items[:]
        item = SubtitleHistoryItem(item_title, rating_key, section_title=section_title, subtitle=subtitle)

        # insert item
        items.insert(0, item)

        # clamp item amount
        items = items[:self.size]

        # store items
        self.history_items = items
