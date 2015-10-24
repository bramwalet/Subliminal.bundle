# coding=utf-8

import logging
from plex import Plex
from helpers import is_recent
logger = logging.getLogger(__name__)


def getRecentItems():
    itemCount = 0
    recent_items = []
    for item in Plex['library'].recently_added():
        if item.type == "season":
            for child in item.children():
                if is_recent(child):
                    #print u"Series: %s, Season: %s, Episode: %s %s" % (item.show.title, item.title, child.index, child.title)
                    #findMissingSubtitles(child, _type="episode", dry_run=dry_run)
		    recent_items.append(("episode", child))
                    itemCount += 1

        elif item.type == "movie":
            if is_recent(item):
                #print "Movie: ", item.title
                #findMissingSubtitles(item, _type="movie", dry_run=dry_run)
		recent_items.append(("movie", item))
                itemCount += 1

    Log.Debug("Recent items found: %s", itemCount)
    return recent_items
