# coding=utf-8

from subzero.lib.dict import DictProxy


class SubtitleHistoryItem(object):
    title = None
    rating_key = None
    score = None

    def __init__(self, title, rating_key, score):
        self.title = title
        self.rating_key = str(rating_key)
        self.score = score

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return u"%s (Score: %s)" % (unicode(self.title), self.score)

    def __str__(self):
        return str(self.rating_key)

    def __hash__(self):
        return hash((self.title, self.rating_key, self.score))

    def __eq__(self, other):
        return (self.title, self.rating_key, self.score) == (other.title, other.rating_key, other.score)

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

    def add(self, title, rating_key, score):
        # create copy
        items = self.history_items[:]
        item = SubtitleHistoryItem(title, rating_key, score)

        # remove duplicates
        if item in items:
            items.remove(item)

        # insert item
        items.insert(0, item)

        # clamp item amount
        items = items[:self.size]

        # store items
        self.history_items = items
