# coding=utf-8
import traceback
import time

import os

from support.config import config
from support.helpers import get_plex_item_display_title, cast_bool
from support.items import get_item
from support.lib import Plex
from support.storage import get_subtitle_storage
from subzero.video import has_external_subtitle


def item_discover_missing_subs(rating_key, kind="show", added_at=None, section_title=None, internal=False, external=True, languages=()):
    item_id = int(rating_key)
    item = get_item(rating_key)

    if kind == "show":
        item_title = get_plex_item_display_title(item, kind, parent=item.season, section_title=section_title, parent_title=item.show.title)
    else:
        item_title = get_plex_item_display_title(item, kind, section_title=section_title)

    subtitle_storage = get_subtitle_storage()
    stored_subs = subtitle_storage.load(rating_key)
    subtitle_storage.destroy()

    subtitle_target_dir, tdir_is_absolute = config.subtitle_sub_dir

    ietf_as_alpha3 = cast_bool(Prefs["subtitles.language.ietf_normalize"])

    missing = set()
    languages_set = set(languages)
    for media in item.media:
        existing_subs = {"internal": [], "external": [], "own_external": [], "count": 0}
        for part in media.parts:

            # did we already download an external subtitle before?
            if subtitle_target_dir and stored_subs:
                for language in languages_set:
                    if has_external_subtitle(part.id, stored_subs, language):
                        # check the existence of the actual subtitle file

                        # get media filename without extension
                        part_basename = os.path.splitext(os.path.basename(part.file))[0]

                        # compute target directory for subtitle
                        # fixme: move to central location
                        if tdir_is_absolute:
                            possible_subtitle_path_base = subtitle_target_dir
                        else:
                            possible_subtitle_path_base = os.path.join(os.path.dirname(part.file), subtitle_target_dir)

                        possible_subtitle_path_base = os.path.realpath(possible_subtitle_path_base)

                        # folder actually exists?
                        if not os.path.isdir(possible_subtitle_path_base):
                            continue

                        found_any = False
                        for ext in config.subtitle_formats:
                            if cast_bool(Prefs['subtitles.only_one']):
                                possible_subtitle_path = os.path.join(possible_subtitle_path_base,
                                                                      u"%s.%s" % (part_basename, ext))
                            else:
                                possible_subtitle_path = os.path.join(possible_subtitle_path_base,
                                                                      u"%s.%s.%s" % (part_basename, language, ext))

                            # check for subtitle existence
                            if os.path.isfile(possible_subtitle_path):
                                found_any = True
                                Log.Debug(u"Found: %s", possible_subtitle_path)
                                break

                        if found_any:
                            existing_subs["own_external"].append(language)
                            existing_subs["count"] = existing_subs["count"] + 1

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
            existing_flat = set((existing_subs["internal"] if internal else [])
                                + (existing_subs["external"] if external else [])
                                + existing_subs["own_external"])

            check_languages = set(languages)
            if ietf_as_alpha3:
                existing_flat = list(existing_flat)
                for language in existing_flat:
                    language.country_orig = language.country
                    language.country = None

                existing_flat = set(existing_flat)

                check_languages = list(check_languages)
                for language in check_languages:
                    language.country_orig = language.country
                    language.country = None

                check_languages = set(check_languages)

            if check_languages.issubset(existing_flat) or (len(existing_flat) >= 1 and Prefs['subtitles.only_one']):
                # all subs found
                #Log.Info(u"All subtitles exist for '%s'", item_title)
                continue

            missing_from_part = check_languages - existing_flat
            if ietf_as_alpha3:
                missing_from_part = list(missing_from_part)
                for language in missing_from_part:
                    if language.country_orig:
                        language.country = language.country_orig

                missing_from_part = set(missing_from_part)

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


