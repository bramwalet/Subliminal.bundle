# coding=utf-8

import logging
from helpers import is_recent, format_item
from subzero import intent
from lib import Plex
from config import config

logger = logging.getLogger(__name__)

MI_KIND, MI_TITLE, MI_KEY, MI_DEEPER, MI_ITEM = 0, 1, 2, 3, 4


def getItems(key="recently_added", base="library", value=None, flat=True):
    """
    plex has certain views that return multiple item types. recently_added and on_deck for example
    """
    items = []
    print "Plex[%s].%s(%s)" % (base, key, value)
    for item in getattr(Plex[base], key)(*[value] if value else []):
        if hasattr(item, "scanner"):
            kind = "section"
        else:
            kind = item.type

        print "KIND: ", kind

        if kind == "season":
            if flat:
                # return episodes
                for child in item.children():
                    # print u"Series: %s, Season: %s, Episode: %s %s" % (item.show.title, item.title, child.index, child.title)
                    items.append(("episode", format_video(child, "episode", parent=item), item.rating_key, False, child))
            else:
                # return seasons
                items.append(("season", item.title, item.rating_key, True, item))

        elif kind == "section":
            items.append(("section", item.title, item.key, True, item))

        elif kind == "episode":
            items.append(
                (kind, format_video(item, kind, parent=item.season, parentTitle=item.show.title), item.rating_key, False, item))

        elif kind == "movie":
            items.append((kind, format_video(item, kind), item.rating_key, False, item))

        elif kind == "show":
            items.append((kind, item.title, item.rating_key, True, item))

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
    items = getItems(key="recently_added")
    return filter(lambda x: is_recent(x[MI_ITEM]), items)


def getOnDeckItems():
    return getItems(key="on_deck")


def getAllItems(key, base="library", value=None, flat=False):
    return getItems(key, base=base, value=value, flat=flat)
    return [(int(item.added_at), item.rating_key, title) for kind, title, item in getMergedItems(key="on_deck")]


def refreshItem(rating_key, force=False, timeout=8000):
    # timeout actually is the time for which the intent will be valid
    if force:
        intent.set("force", rating_key, timeout=timeout)
    Log.Info("%s item %s", "Refreshing" if not force else "Forced-refreshing", rating_key)
    Plex["library/metadata"].refresh(rating_key)
