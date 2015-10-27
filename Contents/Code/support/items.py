# coding=utf-8

import logging
from helpers import is_recent, format_video
from subzero import intent
from config import config
logger = logging.getLogger(__name__)

MI_KIND, MI_TITLE, MI_ITEM = 0, 1, 2
def getMergedItems(key="recently_added"):
    """
    plex has certain views that return multiple item types. recently_added and on_deck for example
    """
    items = []
    for item in getattr(config.Plex['library'], key)():
        if item.type == "season":
            for child in item.children():
                #print u"Series: %s, Season: %s, Episode: %s %s" % (item.show.title, item.title, child.index, child.title)
		items.append(("episode", format_video(child, "episode", parent=item), child))
	
	elif item.type == "episode":
	    items.append(("episode", format_video(item, "episode", parent=item.season, parentTitle=item.show.title), item))

        elif item.type == "movie":
	    items.append(("movie", format_video(item, "movie"), item))

    return items

def getRecentlyAddedItems():
    items = getMergedItems(key="recently_added")
    return filter(lambda x: is_recent(x[MI_ITEM]), items)

def getOnDeckItems():
    return getMergedItems(key="on_deck")
    

def refreshItem(rating_key, force=False, timeout=8000):
    # timeout actually is the time for which the intent will be valid
    if force:
	intent.set("force", rating_key, timeout=timeout)
    Log.Info("%s item %s", "Refreshing" if not force else "Forced-refreshing", rating_key)
    config.Plex["library/metadata"].refresh(rating_key)
