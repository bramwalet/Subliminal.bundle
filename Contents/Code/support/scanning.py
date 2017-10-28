# coding=utf-8

import helpers
from support.lib import Plex, get_intent
from support.plex_media import get_stream_fps
from support.storage import get_subtitle_storage
from support.config import config

from subzero.video import parse_video


def scan_video(pms_video_info, ignore_all=False, hints=None, rating_key=None, no_refining=False):
    """
    returnes a subliminal/guessit-refined parsed video
    :param pms_video_info:
    :param ignore_all:
    :param hints:
    :param rating_key:
    :return:
    """
    embedded_subtitles = not ignore_all and Prefs['subtitles.scan.embedded']
    external_subtitles = not ignore_all and Prefs['subtitles.scan.external']

    plex_part = pms_video_info["plex_part"]

    if ignore_all:
        Log.Debug("Force refresh intended.")

    Log.Debug("Scanning video: %s, external_subtitles=%s, embedded_subtitles=%s" % (
        plex_part.file, external_subtitles, embedded_subtitles))

    known_embedded = []
    parts = []
    for media in list(Plex["library"].metadata(rating_key))[0].media:
        parts += media.parts

    plexpy_part = None
    for part in parts:
        if int(part.id) == int(plex_part.id):
            plexpy_part = part

    # embedded subtitles
    if plexpy_part:
        for stream in plexpy_part.streams:
            # subtitle stream
            if stream.stream_type == 3:
                if (config.forced_only and getattr(stream, "forced")) or \
                        (not config.forced_only and not getattr(stream, "forced")):

                    # embedded subtitle
                    # fixme: tap into external subtitles here instead of scanning for ourselves later?
                    if not stream.stream_key:
                        if config.exotic_ext or stream.codec in ("srt", "ass", "ssa"):
                            lang_code = stream.language_code

                            # treat unknown language as lang1?
                            if not lang_code and config.treat_und_as_first:
                                lang_code = list(config.lang_list)[0].alpha3
                            known_embedded.append(lang_code)
    else:
        Log.Warn("Part %s missing of %s, not able to scan internal streams", plex_part.id, rating_key)

    subtitle_storage = get_subtitle_storage()
    stored_subs = subtitle_storage.load(rating_key)
    subtitle_storage.destroy()

    try:
        # get basic video info scan (filename)
        video = parse_video(plex_part.file, pms_video_info, hints, external_subtitles=external_subtitles,
                            embedded_subtitles=embedded_subtitles, known_embedded=known_embedded,
                            forced_only=config.forced_only, no_refining=no_refining, ignore_all=ignore_all,
                            stored_subs=stored_subs)

        # add video fps info
        video.fps = plex_part.fps
        return video

    except ValueError:
        Log.Warn("File could not be guessed by subliminal: %s" % plex_part.file)


def scan_videos(videos, kind="series", ignore_all=False, no_refining=False):
    """
    receives a list of videos containing dictionaries returned by media_to_videos
    :param videos:
    :param kind: series or movies
    :return: dictionary of subliminal.video.scan_video, key=subliminal scanned video, value=plex file part
    """
    ret = {}
    for video in videos:
        intent = get_intent()
        force_refresh = intent.get("force", video["id"], video["series_id"], video["season_id"])
        Log.Debug("Determining force-refresh (video: %s, series: %s, season: %s), result: %s"
                  % (video["id"], video["series_id"], video["season_id"], force_refresh))

        hints = helpers.get_item_hints(video)
        video["plex_part"].fps = get_stream_fps(video["plex_part"].streams)
        scanned_video = scan_video(video, ignore_all=force_refresh or ignore_all, hints=hints,
                                   rating_key=video["id"], no_refining=no_refining)

        if not scanned_video:
            continue

        scanned_video.id = video["id"]
        part_metadata = video.copy()
        del part_metadata["plex_part"]
        scanned_video.plexapi_metadata = part_metadata
        ret[scanned_video] = video["plex_part"]
    return ret