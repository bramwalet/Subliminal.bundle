# coding=utf-8

import logging
from helpers import is_recent, format_video
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
    items = getItems(key="recently_added")
    return filter(lambda x: is_recent(x[MI_ITEM]), items)


def getOnDeckItems():
    return getItems(key="on_deck")


def getAllItems(key, base="library", value=None, flat=False):
    return getItems(key, base=base, value=value, flat=flat)


def refreshItem(rating_key, force=False, timeout=8000):
    # timeout actually is the time for which the intent will be valid
    if force:
        intent.set("force", rating_key, timeout=timeout)
    Log.Info("%s item %s", "Refreshing" if not force else "Forced-refreshing", rating_key)
    Plex["library/metadata"].refresh(rating_key)
