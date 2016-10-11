# coding=utf-8

import plex
from subzero.intent import TempIntent
from subzero.lib.dict import DictProxy
from subzero.lib.httpfake import PlexPyNativeResponseProxy


class PlexPyNativeRequestProxy(object):
    """
    A really dumb object that tries to mimic requests.Request in an incomplete way, so that plex.Plex
    uses native plex HTTPRequests instead of the better requests.Request class.

    This allows us to operate freely on 127.0.0.1's PMS.

    To be used in conjunction with subzero.lib.httpfake.PlexPyNativeResponseProxy
    """
    url = None
    data = None
    headers = None
    method = None

    def prepare(self):
        return self

    def send(self):
        # fixme: add self.data to HTTP.Request
        data = None
        status_code = 200
        try:
            data = HTTP.Request(self.url, headers=self.headers, immediate=True, method=self.method)
        except Ex.HTTPError as e:
            status_code = e.code
        return PlexPyNativeResponseProxy(data, status_code, self)


plex.request.Request = PlexPyNativeRequestProxy

Plex = plex.Plex


class IntentDictStorage(DictProxy):
    store = "intent"

    def setup_defaults(self):
        return {"force": {}}


def get_intent():
    """
    use this to get an intent from inside a separate thread
    :return:
    """
    return TempIntent(store=IntentDictStorage(Dict))
