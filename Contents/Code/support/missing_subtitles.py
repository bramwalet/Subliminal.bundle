# coding=utf-8
import traceback
import time

from support.config import config
from support.helpers import get_plex_item_display_title, cast_bool
from support.items import get_item
from support.lib import Plex


def item_discover_missing_subs(rating_key, kind="show", added_at=None, section_title=None, internal=False, external=True, languages=()):
    item_id = int(rating_key)
    item = get_item(rating_key)

    if kind == "show":
        item_title = get_plex_item_display_title(item, kind, parent=item.season, section_title=section_title, parent_title=item.show.title)
    else:
        item_title = get_plex_item_display_title(item, kind, section_title=section_title)

    missing = set()
    languages_set = set(languages)
    for media in item.media:
        existing_subs = {"internal": [], "external": [], "count": 0}
        for part in media.parts:
            for stream in part.streams:
                if stream.stream_type == 3:
                    if stream.index:
                        key = "internal"
                    else:
                        key = "external"

                    existing_subs[key].append(Locale.Language.Match(stream.language_code or ""))
                    existing_subs["count"] = existing_subs["count"] + 1

        missing_from_part = set(languages_set)
        if existing_subs["count"]:
            existing_flat = set((existing_subs["internal"] if internal else []) + (existing_subs["external"] if external else []))
            if languages_set.issubset(existing_flat) or (len(existing_flat) >= 1 and Prefs['subtitles.only_one']):
                # all subs found
                #Log.Info(u"All subtitles exist for '%s'", item_title)
                continue

            missing_from_part = languages_set - existing_flat

        if missing_from_part:
            Log.Info(u"Subs still missing for '%s' (%s: %s): %s", item_title, rating_key, media.id,
                     missing_from_part)
            missing.update(missing_from_part)

    if missing:
        return added_at, item_id, item_title, item, missing


def items_get_all_missing_subs(items, sleep_after_request=False):
    missing = []
    for added_at, kind, section_title, key in items:
        try:
            state = item_discover_missing_subs(
                key,
                kind=kind,
                added_at=added_at,
                section_title=section_title,
                languages=config.lang_list,
                internal=cast_bool(Prefs["subtitles.scan.embedded"]),
                external=cast_bool(Prefs["subtitles.scan.external"])
            )
            if state:
                # (added_at, item_id, title, item, missing_languages)
                missing.append(state)
        except:
            Log.Error("Something went wrong when getting the state of item %s: %s", key, traceback.format_exc())
        if sleep_after_request:
            time.sleep(sleep_after_request)
    return missing


def refresh_item(item):
    if not config.no_refresh:
        Plex["library/metadata"].refresh(item)


