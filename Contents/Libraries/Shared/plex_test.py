# coding=utf-8

import datetime
import logging
import sys
from plex import Plex
from plex.client import PlexClient

logger = logging.getLogger(__name__)

now = datetime.datetime.now()


def is_recent(item):
    addedAt = datetime.datetime.fromtimestamp(item.added_at)
    if now - datetime.timedelta(weeks=2) > addedAt:
        return False
    return True


def findMissingSubtitles(list_item, _type="episode", internal=False, external=True, languages=["eng"], section_blacklist=["3"],
                         series_blacklist=["26059"], dry_run=False):
    existing_subs = {"internal": [], "external": [], "count": 0}

    # get requested item again to have access to the streams - should not be necessary
    item_id = int(list_item.key.split("/")[-1])
    item_container = Plex["library"].metadata(item_id)

    # don't process blacklisted sections
    if item_container.section.key in section_blacklist:
        return

    item = list(item_container)[0]

    if _type == "episode" and item.show.rating_key in series_blacklist:
        logger.debug("Skipping show %s in blacklist", item.show.key)
        return
    elif _type == "movie" and item.rating_key in movie_blacklist:
        logger.debug("Skipping movie %s in blacklist", item.key)
        return

    video = item.media

    for part in video.parts:
        for stream in part.streams:
            if stream.stream_type == 3:
                if stream.index:
                    key = "internal"
                else:
                    key = "external"

                existing_subs[key].append(stream.language_code)
                existing_subs["count"] += 1

    missing = languages
    if existing_subs["count"]:
        existing_flat = existing_subs["internal"] if internal else [] + existing_subs["external"] if external else []
        languages_set = set(languages)
        if languages_set.issubset(existing_flat):
            # all subs found
            logger.debug(u"All subtitles existing for %s", item.title)
            return
        else:
            missing = languages_set - set(existing_flat)
            logger.info(u"Subs still missing: %s", missing)

    if missing:
        logger.info("Triggering refresh for '%s'", item.title)
        if not dry_run:
            Plex["library/metadata"].refresh(item_id)


def run():
    token = sys.argv[1]
    Plex.configuration.defaults.authentication(token)
    sections = Plex["library"].sections()
    #section = list(sections)[0]
    #print section.title, section.path, dir(section), list(section._children)[0].path
    #return
    for container in sections:
        print container.title
        for location in container:
            print location.path

    return
    itemCount = 0
    dry_run = "--dry-run" in sys.argv
    with Plex.configuration.authentication("asdfasdfasdf"):
        print Plex.configuration.stack[1].data
    # Plex[":/plugins"].restart("com.plexapp.agents.subzero")
    # Plex[":/plugins/*/prefs"].set("com.plexapp.agents.subzero", "reset_storage", True)
    return

    for item in Plex['library'].recently_added():
        if item.type == "season":
            for child in item.children():
                if is_recent(child):
                    print u"Series: %s, Season: %s, Episode: %s %s" % (item.show.title, item.title, child.index, child.title)
                    findMissingSubtitles(child, _type="episode", dry_run=dry_run)
                    itemCount += 1

        elif item.type == "movie":
            if is_recent(item):
                print "Movie: ", item.title
                findMissingSubtitles(item, _type="movie", dry_run=dry_run)
                itemCount += 1

    print "Items: ", itemCount


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    run()
