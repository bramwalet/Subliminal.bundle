# coding=utf-8
from subzero.lib.dict import DictProxy


class SubtitleHistoryItem(object):
    title = None
    rating_key = None

    def __init__(self, title, rating_key):
        self.title = title
        self.rating_key = rating_key

    def __hash__(self):
        return hash((self.title, self.rating_key))


class SubtitleHistory(DictProxy):
    store = "history"

    def setup_defaults(self):
        return {"items": []}

    def add(self, title, rating_key):
        # create copy
        items = self.items[:]
        item = SubtitleHistoryItem(title, rating_key)

        # remove duplicates
        if item in items:
            items.remove(item)

        # insert item
        items.insert(0, item)

        # clamp item amount
        items = items[:int(Prefs["history_size"])]

        # store items
        self.items = items

get_history = lambda: SubtitleHistory(Dict)
