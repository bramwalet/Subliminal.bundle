# coding=utf-8

from subzero.lib.dict import DictProxy


class SubtitleHistoryItem(object):
    title = None
    rating_key = None

    def __init__(self, title, rating_key):
        self.title = title
        self.rating_key = str(rating_key)

    def __hash__(self):
        return hash((self.title, self.rating_key))


class SubtitleHistory(DictProxy):
    store = "history"
    size = 100

    def __init__(self, storage, size=100):
        super(SubtitleHistory, self).__init__(storage)
        self.size = size

    def setup_defaults(self):
        return {"history_items": []}

    def add(self, title, rating_key):
        # create copy
        items = self.history_items[:]
        item = SubtitleHistoryItem(title, rating_key)

        # remove duplicates
        if item in items:
            items.remove(item)

        # insert item
        items.insert(0, item)

        # clamp item amount
        items = items[:self.size]

        # store items
        self.history_items = items
