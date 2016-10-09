# coding=utf-8

import datetime
import pprint
import copy


def get_subtitle_info(rating_key):
    return Dict["subs"].get(rating_key)


def whack_missing_parts(scanned_video_part_map, existing_parts=None):
    """
    cleans out our internal storage's video parts (parts may get updated/deleted/whatever)
    :param existing_parts: optional list of part ids known
    :param scanned_video_part_map: videos to check for
    :return:
    """
    # shortcut

    if "subs" not in Dict:
        return

    if not existing_parts:
        existing_parts = []
        for part in scanned_video_part_map.viewvalues():
            existing_parts.append(part.id)

    whacked_parts = False
    for video in scanned_video_part_map.keys():
        if video.id not in Dict["subs"]:
            continue

        parts = Dict["subs"][video.id].keys()

        for part_id in parts:
            if part_id not in existing_parts:
                Log.Info("Whacking part %s in internal storage of video %s (%s, %s)", part_id, video.id,
                         repr(existing_parts), repr(parts))
                del Dict["subs"][video.id][part_id]
                whacked_parts = True

    if whacked_parts:
        Dict.Save()


def store_subtitle_info(scanned_video_part_map, downloaded_subtitles, storage_type):
    """
    stores information about downloaded subtitles in plex's Dict()
    """
    if "subs" not in Dict:
        Dict["subs"] = {}

    existing_parts = []
    for video, video_subtitles in downloaded_subtitles.items():
        part = scanned_video_part_map[video]

        if video.id not in Dict["subs"]:
            Dict["subs"][video.id] = {}

        video_dict = copy.deepcopy(Dict["subs"][video.id])
        if part.id not in video_dict:
            video_dict[part.id] = {}

        existing_parts.append(part.id)

        part_dict = video_dict[part.id]
        for subtitle in video_subtitles:
            lang = Locale.Language.Match(subtitle.language.alpha2)
            if lang not in part_dict:
                part_dict[lang] = {}
            lang_dict = part_dict[lang]
            sub_key = (subtitle.provider_name, subtitle.id)
            lang_dict[sub_key] = dict(score=subtitle.score, link=subtitle.page_link, storage=storage_type,
                                      hash=Hash.MD5(subtitle.content),
                                      date_added=datetime.datetime.now())
            lang_dict["current"] = sub_key

        Dict["subs"][video.id] = video_dict

    #Dict.Save()

    #if existing_parts:
    #    whack_missing_parts(scanned_video_part_map, existing_parts=existing_parts)
    Dict.Save()


def reset_storage(key):
    """
    resets the Dict[key] storage, thanks to https://docs.google.com/document/d/1hhLjV1pI-TA5y91TiJq64BdgKwdLnFt4hWgeOqpz1NA/edit#
    We can't use the nice Plex interface for this, as it calls get multiple times before set
    #Plex[":/plugins/*/prefs"].set("com.plexapp.agents.subzero", "reset_storage", False)
    """

    Log.Debug("resetting storage")
    Dict[key] = {}
    Dict.Save()


def log_storage(key):
    if key in Dict:
        Log.Debug(pprint.pformat(Dict[key]))
