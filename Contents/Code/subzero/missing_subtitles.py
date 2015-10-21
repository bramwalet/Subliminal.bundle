# coding=utf-8

import datetime
import logging
import sys

from plex import Plex

logger = logging.getLogger(__name__)


def findMissingSubtitles(list_item, kind="episode", internal=False, external=True, languages=["eng"], section_blacklist=["3"], series_blacklist=["26059"], dry_run=False):
    existing_subs = {"internal": [], "external": [], "count": 0}

    # get requested item again to have access to the streams - should not be necessary
    item_id = int(list_item.key.split("/")[-1])
    item_container = Plex["library"].metadata(item_id)

    # don't process blacklisted sections
    if item_container.section.key in section_blacklist:
        return

    item = list(item_container)[0]

    if kind == "episode" and item.show.rating_key in series_blacklist:
        logger.debug("Skipping show %s in blacklist", item.show.key)
        return
    elif kind == "movie" and item.rating_key in movie_blacklist:
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
                existing_subs["count"] == existing_subs["count"] + 1

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
