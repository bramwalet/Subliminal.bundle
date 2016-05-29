# coding=utf-8

import datetime
import threading

lock = threading.Lock()


class TempIntent(dict):
    timeout = 1000  # milliseconds
    store = None

    def __init__(self, timeout=1000):
        self.timeout = timeout
        with lock:
            self.store = {}

    def __getattr__(self, name):
        if name in self:
            return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]

    def get(self, kind, *keys):
        with lock:
            # iter all requested keys
            for key in keys:
                hit = False

                # skip key if invalid
                if not key:
                    continue

                # valid kind?
                if kind in self["store"]:
                    now = datetime.datetime.now()

                    # iter all known kinds (previously created)
                    for known_key in self["store"][kind].keys():
                        # may need locking, for now just play it safe
                        ends = self["store"][kind].get(known_key, None)
                        if not ends:
                            continue

                        timed_out = False
                        if now > ends:
                            timed_out = True

                        # key and kind in storage, and not timed out = hit
                        if known_key == key and not timed_out:
                            hit = True

                        if timed_out:
                            try:
                                del self["store"][kind][key]
                            except:
                                continue

                    if hit:
                        return True
        return False

    def resolve(self, kind, key):
        with lock:
            if kind in self["store"] and key in self["store"][kind]:
                del self["store"][kind][key]
                return True
            return False

    def set(self, kind, key, timeout=None):
        with lock:
            if kind not in self["store"]:
                self["store"][kind] = {}
            self["store"][kind][key] = datetime.datetime.now() + datetime.timedelta(milliseconds=timeout or self.timeout)

    def has(self, kind, key):
        with lock:
            if kind not in self["store"]:
                return False
            return key in self["store"][kind]


intent = TempIntent()
