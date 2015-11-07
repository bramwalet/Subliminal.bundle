# coding=utf-8

import types
from support.items import getRecentlyAddedItems, MI_ITEM
from support.config import config
from support.helpers import format_video
from lib import Plex


def itemDiscoverMissing(rating_key, kind="episode", internal=False, external=True, languages=(), section_blacklist=(), series_blacklist=(),
                        item_blacklist=()):
    existing_subs = {"internal": [], "external": [], "count": 0}

    item_id = int(rating_key)
    item_container = Plex["library"].metadata(item_id)

    # don't process blacklisted sections
    if item_container.section.key in section_blacklist:
        return

    item = list(item_container)[0]

    if kind == "episode":
        item_title = format_video(item, kind, parent=item.season, parentTitle=item.show.title)
    else:
        item_title = format_video(item, kind)

    if kind == "episode" and item.show.rating_key in series_blacklist:
        Log.Info("Skipping show %s in blacklist", item.show.key)
        return
    elif item.rating_key in item_blacklist:
        Log.Info("Skipping item %s in blacklist", item.key)
        return

    video = item.media

    for part in video.parts:
        for stream in part.streams:
            if stream.stream_type == 3:
                if stream.index:
                    key = "internal"
                else:
                    key = "external"

                existing_subs[key].append(Locale.Language.Match(stream.language_code or ""))
                existing_subs["count"] = existing_subs["count"] + 1

    missing = languages
    if existing_subs["count"]:
        existing_flat = (existing_subs["internal"] if internal else []) + (existing_subs["external"] if external else [])
        languages_set = set(languages)
        if languages_set.issubset(existing_flat):
            # all subs found
            Log.Info(u"All subtitles exist for '%s'", item_title)
            return

        missing = languages_set - set(existing_flat)
        Log.Info(u"Subs still missing for '%s': %s", item_title, missing)

    if missing:
        return item_id, item_title


def getAllRecentlyAddedMissing():
    items = getRecentlyAddedItems()
    missing = []
    for kind, title, item in items:
        state = itemDiscoverMissing(
            item.rating_key,
            kind=kind,
            languages=config.langList,
            internal=bool(Prefs["subtitles.scan.embedded"]),
            external=bool(Prefs["subtitles.scan.external"]),
            section_blacklist=config.scheduler_section_blacklist,
            series_blacklist=config.scheduler_series_blacklist,
            item_blacklist=config.scheduler_item_blacklist
        )
        if state:
            # (item_id, title)
            missing.append(state)
    return missing


def searchMissing(item, title):
    Plex["library/metadata"].refresh(item)


def searchAllMissing(items):
    for item, title in items:
        searchMissing(item, title)
