# coding=utf-8
import os
import subprocess
import traceback

from support.helpers import quote_args, mswindows, get_title_for_video_metadata, cast_bool, \
    audio_streams_match_languages
from support.i18n import _
from support.items import get_item_kind_from_item, refresh_item, get_all_items, get_item, MI_KEY
from support.storage import get_subtitle_storage, save_subtitles
from support.config import config
from support.history import get_history
from support.plex_media import get_all_parts, get_embedded_subtitle_streams, get_part, get_plex_metadata, \
    update_stream_info, is_stream_forced
from support.scanning import scan_videos
from subzero.language import Language
from subliminal_patch.subtitle import ModifiedSubtitle


def agent_extract_embedded(video_part_map, set_as_existing=False):
    try:
        subtitle_storage = get_subtitle_storage()

        to_extract = []
        item_count = 0

        threads = []

        for scanned_video, part_info in video_part_map.iteritems():
            plexapi_item = scanned_video.plexapi_metadata["item"]
            stored_subs = subtitle_storage.load_or_new(plexapi_item)
            valid_langs_in_media = \
                audio_streams_match_languages(scanned_video, config.get_lang_list(ordered=True))

            if not config.lang_list.difference(valid_langs_in_media):
                Log.Debug("Skipping embedded subtitle extraction for %s, audio streams are in correct language(s)",
                          plexapi_item.rating_key)
                continue

            for plexapi_part in get_all_parts(plexapi_item):
                item_count = item_count + 1
                used_one_unknown_stream = False
                used_one_known_stream = False
                for requested_language in config.lang_list:
                    skip_unknown = used_one_unknown_stream or used_one_known_stream
                    embedded_subs = stored_subs.get_by_provider(plexapi_part.id, requested_language, "embedded")
                    current = stored_subs.get_any(plexapi_part.id, requested_language) or \
                        requested_language in scanned_video.external_subtitle_languages

                    if not embedded_subs:
                        stream_data = get_embedded_subtitle_streams(plexapi_part, requested_language=requested_language,
                                                                    skip_unknown=skip_unknown)

                        if stream_data and stream_data[0]["language"]:
                            stream = stream_data[0]["stream"]
                            if stream_data[0]["is_unknown"]:
                                used_one_unknown_stream = True
                            else:
                                used_one_known_stream = True

                            to_extract.append(({scanned_video: part_info}, plexapi_part, str(stream.index),
                                               str(requested_language), not current))

                            if not cast_bool(Prefs["subtitles.search_after_autoextract"]) or set_as_existing:
                                scanned_video.subtitle_languages.update({requested_language})
                    else:
                        Log.Debug("Skipping embedded subtitle extraction for %s, already got %r from %s",
                                  plexapi_item.rating_key, requested_language, embedded_subs[0].id)
        if to_extract:
            Log.Info("Triggering extraction of %d embedded subtitles of %d items", len(to_extract), item_count)
            threads.append(Thread.Create(multi_extract_embedded, stream_list=to_extract, refresh=True, with_mods=True,
                                         single_thread=not config.advanced.auto_extract_multithread))
            return threads
    except:
        Log.Error("Something went wrong when auto-extracting subtitles, continuing: %s", traceback.format_exc())


def multi_extract_embedded(stream_list, refresh=False, with_mods=False, single_thread=True, extract_mode="a",
                           history_storage=None):
    def execute():
        for video_part_map, plexapi_part, stream_index, language, set_current in stream_list:
            plexapi_item = video_part_map.keys()[0].plexapi_metadata["item"]

            extract_embedded_sub(rating_key=plexapi_item.rating_key, part_id=plexapi_part.id,
                                 plex_item=plexapi_item, part=plexapi_part, scanned_videos=video_part_map,
                                 stream_index=stream_index, set_current=set_current,
                                 language=language, with_mods=with_mods, refresh=refresh, extract_mode=extract_mode,
                                 history_storage=history_storage)

    if single_thread:
        with Thread.Lock(key="extract_embedded"):
            execute()
    else:
        execute()


def season_extract_embedded(rating_key, requested_language, with_mods=False, force=False):
    # get stored subtitle info for item id
    subtitle_storage = get_subtitle_storage()

    try:
        for data in get_all_items(key="children", value=rating_key, base="library/metadata"):
            item = get_item(data[MI_KEY])
            if item:
                stored_subs = subtitle_storage.load_or_new(item)
                for part in get_all_parts(item):
                    embedded_subs = stored_subs.get_by_provider(part.id, requested_language, "embedded")
                    current = stored_subs.get_any(part.id, requested_language)
                    if not embedded_subs or force:
                        stream_data = get_embedded_subtitle_streams(part, requested_language=requested_language)
                        if stream_data:
                            stream = stream_data[0]["stream"]

                            set_current = not current or force
                            refresh = not current

                            extract_embedded_sub(rating_key=item.rating_key, part_id=part.id,
                                                 stream_index=str(stream.index), set_current=set_current,
                                                 refresh=refresh, language=requested_language, with_mods=with_mods,
                                                 extract_mode="m")
    finally:
        subtitle_storage.destroy()


def extract_embedded_sub(**kwargs):
    rating_key = kwargs["rating_key"]
    part_id = kwargs.pop("part_id")
    stream_index = kwargs.pop("stream_index")
    with_mods = kwargs.pop("with_mods", False)
    language = Language.fromietf(kwargs.pop("language"))
    refresh = kwargs.pop("refresh", True)
    set_current = kwargs.pop("set_current", True)

    plex_item = kwargs.pop("plex_item", get_item(rating_key))
    item_type = get_item_kind_from_item(plex_item)
    part = kwargs.pop("part", get_part(plex_item, part_id))
    scanned_videos = kwargs.pop("scanned_videos", None)
    extract_mode = kwargs.pop("extract_mode", "a")

    any_successful = False

    from interface.menu_helpers import set_refresh_menu_state

    if part:
        if not scanned_videos:
            metadata = get_plex_metadata(rating_key, part_id, item_type, plex_item=plex_item)
            scanned_videos = scan_videos([metadata], ignore_all=True, skip_hashing=True)

        update_stream_info(part)
        for stream in part.streams:
            # subtitle stream
            if str(stream.index) == stream_index:
                is_forced = is_stream_forced(stream)
                bn = os.path.basename(part.file)

                set_refresh_menu_state(_(u"Extracting subtitle %(stream_index)s of %(filename)s",
                                         stream_index=stream_index,
                                         filename=bn))
                Log.Info(u"Extracting stream %s (%s) of %s", stream_index, str(language), bn)

                out_codec = stream.codec if stream.codec != "mov_text" else "srt"

                args = [
                    config.plex_transcoder, "-i", part.file, "-map", "0:%s" % stream_index, "-f", out_codec, "-"
                ]

                cmdline = quote_args(args)
                Log.Debug(u"Calling: %s", cmdline)
                if mswindows:
                    Log.Debug("MSWindows: Fixing encoding")
                    cmdline = cmdline.encode("mbcs")

                output = None
                try:
                    output = subprocess.check_output(cmdline, stderr=subprocess.PIPE, shell=True)
                except:
                    Log.Error("Extraction failed: %s", traceback.format_exc())

                if output:
                    subtitle = ModifiedSubtitle(language, mods=config.default_mods if with_mods else None)
                    subtitle.content = output
                    subtitle.provider_name = "embedded"
                    subtitle.id = "stream_%s" % stream_index
                    subtitle.score = 0
                    subtitle.set_encoding("utf-8")

                    # fixme: speedup video; only video.name is needed
                    video = scanned_videos.keys()[0]
                    save_successful = save_subtitles(scanned_videos, {video: [subtitle]}, mode="m",
                                                     set_current=set_current)
                    set_refresh_menu_state(None)

                    if save_successful and refresh:
                        refresh_item(rating_key)

                    # add item to history
                    item_title = get_title_for_video_metadata(video.plexapi_metadata,
                                                              add_section_title=False, add_episode_title=True)

                    history = get_history()
                    history.add(item_title, video.id, section_title=video.plexapi_metadata["section"],
                                thumb=video.plexapi_metadata["super_thumb"],
                                subtitle=subtitle, mode=extract_mode)
                    history.destroy()

                    any_successful = True

    return any_successful