# coding=utf-8
from subzero.lib.dict import DictProxy


class SubtitleHistory(DictProxy):
    store = "history"

    def setup_defaults(self):
        return {"items": []}


history = SubtitleHistory(Dict)
