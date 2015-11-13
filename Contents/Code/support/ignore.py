# coding=utf-8

from subzero import iter


class DictProxy(object):
    store = None
    translate_keys = None
    keys_verbose = None

    patch_sandbox_methods = ("cmp", "contains", "unicode")

    def __init__(self):
        super(DictProxy, self).__init__()

        # we can't define some methods due to the plex sandbox, dynamically set them
        for item in self.patch_sandbox_methods:
            setattr(self, "__%s__" % item, getattr(self, "%s__" % item))

        if self.store not in Dict:
            Dict[self.store] = self.setup_defaults()

    def __getattr__(self, name):
        if name in Dict[self.store]:
            return Dict[self.store][name]
        return getattr(super(DictProxy, self), name)

    def cmp__(self, d):
        return cmp(Dict[self.store], d)

    def contains__(self, item):
        return item in Dict[self.store]

    def __setitem__(self, key, item):
        Dict[self.store][key] = item

    def __iter__(self):
        return iter(Dict[self.store])

    def __getitem__(self, key):
        if key in Dict[self.store]:
            return Dict[self.store][key]

    def __repr__(self):
        return repr(Dict[self.store])

    def __str__(self):
        return str(Dict[self.store])

    def __len__(self):
        return len(Dict[self.store].keys())

    def __delitem__(self, key):
        del Dict[self.store][key]

    def clear(self):
        del Dict[self.store]
        return None

    def copy(self):
        return Dict[self.store].copy()

    def has_key(self, k):
        return k in Dict[self.store]

    def pop(self, k, d=None):
        return Dict[self.store].pop(k, d)

    def update(self, *args, **kwargs):
        return Dict[self.store].update(*args, **kwargs)

    def keys(self):
        return Dict[self.store].keys()

    def values(self):
        return Dict[self.store].values()

    def items(self):
        return Dict[self.store].items()

    def unicode__(self):
        return unicode(repr(Dict[self.store]))

    def setup_defaults(self):
        raise NotImplementedError


class IgnoreDict(DictProxy):
    store = "ignore"

    translate_keys = {
        "section": "sections",
        "show": "series",
        "movie": "items",
        "episode": "items"
    }

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
