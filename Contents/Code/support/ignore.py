# coding=utf-8

from helpers import DictProxy


class IgnoreDict(DictProxy):
    store = "ignore"

    # single item keys returned by helpers.items.getItems mapped to their parents
    translate_keys = {
        "section": "sections",
        "show": "series",
        "movie": "items",
        "episode": "items"
    }

    # getItems types mapped to their verbose names
    keys_verbose = {
        "sections": "Section",
        "series": "Series",
        "items": "Item",
    }

    def translate_key(self, name):
        return self.translate_keys.get(name)

    def verbose(self, name):
        return self.keys_verbose.get(name)

    def setup_defaults(self):
        return {"sections": [], "series": [], "items": []}

ignore_list = IgnoreDict()
