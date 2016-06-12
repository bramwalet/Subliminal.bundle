# coding=utf-8
import threading

lock = threading.Lock()


class Debouncer(object):
    call_history = set()

    def get_lookup_key(self, args, kwargs):
        func_name = list(args).pop(0).__name__
        return tuple([func_name] + [(key, value) for key, value in kwargs.iteritems()])

    def __contains__(self, item):
        args, kwargs = item
        lookup = self.get_lookup_key(args, kwargs)
        with lock:
            return lookup in self.call_history

    def add(self, args, kwargs):
        with lock:
            self.call_history.add(self.get_lookup_key(args, kwargs))

debouncer = Debouncer()
