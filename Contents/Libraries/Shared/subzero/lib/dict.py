# coding=utf-8


class DictProxy(object):
    store = None

    def __init__(self, d):
        self.Dict = d
        super(DictProxy, self).__init__()

        if self.store not in self.Dict or not self.Dict[self.store]:
            self.Dict[self.store] = self.setup_defaults()
        self.save()

    def __getattr__(self, name):
        if name in self.Dict[self.store]:
            return self.Dict[self.store][name]
        return getattr(super(self.DictProxy, self), name)

    def __cmp__(self, d):
        return cmp(self.Dict[self.store], d)

    def __contains__(self, item):
        return item in self.Dict[self.store]

    def __setitem__(self, key, item):
        self.Dict[self.store][key] = item
        self.Dict.Save()

    def __iter__(self):
        return iter(self.Dict[self.store])

    def __getitem__(self, key):
        if key in self.Dict[self.store]:
            return self.Dict[self.store][key]

    def __repr__(self):
        return repr(self.Dict[self.store])

    def __str__(self):
        return str(self.Dict[self.store])

    def __len__(self):
        return len(self.Dict[self.store].keys())

    def __delitem__(self, key):
        del self.Dict[self.store][key]

    def save(self):
        self.Dict.Save()

    def clear(self):
        del self.Dict[self.store]
        return None

    def copy(self):
        return self.Dict[self.store].copy()

    def has_key(self, k):
        return k in self.Dict[self.store]

    def pop(self, k, d=None):
        return self.Dict[self.store].pop(k, d)

    def update(self, *args, **kwargs):
        return self.Dict[self.store].update(*args, **kwargs)

    def keys(self):
        return self.Dict[self.store].keys()

    def values(self):
        return self.Dict[self.store].values()

    def items(self):
        return self.Dict[self.store].items()

    def __unicode__(self):
        return unicode(repr(self.Dict[self.store]))

    def setup_defaults(self):
        raise NotImplementedError