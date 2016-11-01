# coding=utf-8
from subzero.history_storage import SubtitleHistory

get_history = lambda: SubtitleHistory(Dict, int(Prefs["history_size"]))
