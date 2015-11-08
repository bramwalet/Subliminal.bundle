# coding=utf-8

import logging
from helpers import is_recent, format_item
from subzero import intent
from lib import Plex
from config import config

logger = logging.getLogger(__name__)

MI_KIND, MI_TITLE, MI_ITEM = 0, 1, 2


def getMergedItems(key="recently_added"):
    """
    plex has certain views that return multiple item types. recently_added and on_deck for example
    """
    items = []
    for item in getattr(Plex['library'], key)():
        if item.type == "season":
            for child in item.children():
                # print u"Series: %s, Season: %s, Episode: %s %s" % (item.show.title, item.title, child.index, child.title)
                items.append(("episode", format_item(child, "show", parent=item, section_title=None), child))

        elif item.type == "episode":
            items.append(("episode", format_item(item, "show", parent=item.season, section_title=None, parent_title=item.show.title), item))

        elif item.type == "movie":
            items.append(("movie", format_item(item, "movie"), item))

    return items


def getRecentlyAddedItems():
    items = getMergedItems(key="recently_added")
    return filter(lambda x: is_recent(x[MI_ITEM].added_at), items)


def getRecentItems():
    """
    actually get the recent items, not limited like /library/recentlyAdded
    :return:
    """
    args = {
        "X-Plex-Token": Dict["token"]
    }
    computed_args = "&".join(["%s=%s" % (key, String.Quote(value)) for key, value in args.iteritems()])
    episode_re = re.compile(ur'ratingKey="(?P<key>\d+)"'
                            ur'.+?grandparentRatingKey="(?P<parent_key>\d+)"'
                            ur'.+?title="(?P<title>.*?)"'
                            ur'.+?grandparentTitle="(?P<parent_title>.*?)"'
                            ur'.+?index="(?P<episode>\d+?)"'
                            ur'.+?parentIndex="(?P<season>\d+?)".+?addedAt="(?P<added>\d+)"')
    movie_re = re.compile(ur'ratingKey="(?P<key>\d+)".+?title="(?P<title>.*?)".+?addedAt="(?P<added>\d+)"')
    available_keys = ("key", "title", "parent_key", "parent_title", "season", "episode", "added")
    recent = []
    for section in Plex["library"].sections():
        if section.type not in ("movie", "show") or section.key in config.scheduler_section_blacklist:
            Log.Debug(u"Skipping section: %s" % section.title)
            continue

        request = HTTP.Request("https://127.0.0.1:32400/library/sections/%d/recentlyAdded%s" %
                               (int(section.key), ("?%s" % computed_args) if computed_args else ""), immediate=True)
        matcher = episode_re if section.type == "show" else movie_re
        matches = [m.groupdict() for m in matcher.finditer(request.content)]
        for match in matches:
            data = dict((key, match[key] if key in match else None) for key in available_keys)
            if section.type == "show" and data["parent_key"] in config.scheduler_series_blacklist:
                Log.Debug(u"Skipping series: %s" % data["parent_title"])
                continue
            if data["key"] in config.scheduler_item_blacklist:
                Log.Debug(u"Skipping item: %s" % data["title"])
                continue
            if is_recent(int(data["added"])):
                recent.append((int(data["added"]), section.type, section.title, data["key"]))

    return recent


def getOnDeckItems():
    return [(int(item.added_at), item.rating_key, title) for kind, title, item in getMergedItems(key="on_deck")]


def refreshItem(rating_key, force=False, timeout=8000):
    # timeout actually is the time for which the intent will be valid
    if force:
        intent.set("force", rating_key, timeout=timeout)
    Log.Info("%s item %s", "Refreshing" if not force else "Forced-refreshing", rating_key)
    Plex["library/metadata"].refresh(rating_key)
