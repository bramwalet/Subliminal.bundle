# coding=utf-8

from subzero.lib.dict import DictProxy


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

    def get_title_key(self, kind, key):
        return "%s_%s" % (kind, key)

    def add_title(self, kind, key, title):
        self["titles"][self.get_title_key(kind, key)] = title

    def remove_title(self, kind, key):
        title_key = self.get_title_key(kind, key)
        if title_key in self.titles:
            del self.titles[title_key]

    def get_title(self, kind, key):
        title_key = self.get_title_key(kind, key)
        if title_key in self.titles:
            return self.titles[title_key]

    def save(self):
        Dict.Save()

    def setup_defaults(self):
        return {"sections": [], "series": [], "items": [], "titles": {}}

ignore_list = IgnoreDict(Dict)
