# coding=utf-8

import os
import subliminal
import helpers

from items import get_item
from lib import get_intent


def get_metadata_dict(item, part, add):
    data = {
        "section": item.section.title,
        "path": part.file,
        "folder": os.path.dirname(part.file),
        "filename": os.path.basename(part.file)
    }
    data.update(add)
    return data


def media_to_videos(media, kind="series"):
    """
    iterates through media and returns the associated parts (videos)
    :param media:
    :param kind:
    :return:
    """
    videos = []

    if kind == "series":
        for season in media.seasons:
            season_object = media.seasons[season]
            for episode in media.seasons[season].episodes:
                ep = media.seasons[season].episodes[episode]

                # get plex item via API for additional metadata
                plex_episode = get_item(ep.id)

                for item in media.seasons[season].episodes[episode].items:
                    for part in item.parts:
                        videos.append(
                            get_metadata_dict(plex_episode, part,
                                              {"plex_part": part, "type": "episode", "title": ep.title,
                                               "series": media.title, "id": ep.id,
                                               "series_id": media.id, "season_id": season_object.id,
                                               "episode": plex_episode.index, "season": plex_episode.season.index
                                               })
                        )
    else:
        plex_item = get_item(media.id)
        for item in media.items:
            for part in item.parts:
                videos.append(
                    get_metadata_dict(plex_item, part, {"plex_part": part, "type": "movie",
                                                        "title": media.title, "id": media.id,
                                                        "series_id": None,
                                                        "season_id": None})
                )
    return videos


IGNORE_FN = ("subzero.ignore", ".subzero.ignore", ".nosz")


def get_stream_fps(streams):
    """
    accepts a list of plex streams or a list of the plex api streams
    """
    for stream in streams:
        # video
        stream_type = getattr(stream, "type", getattr(stream, "stream_type", None))
        if stream_type == 1:
            return getattr(stream, "frameRate", getattr(stream, "frame_rate", "25.000"))
    return "25.000"


def get_media_item_ids(media, kind="series"):
    ids = []
    if kind == "movies":
        ids.append(media.id)
    else:
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                ids.append(media.seasons[season].episodes[episode].id)

    return ids


def scan_video(plex_part, ignore_all=False, hints=None):
    embedded_subtitles = not ignore_all and Prefs['subtitles.scan.embedded']
    external_subtitles = not ignore_all and Prefs['subtitles.scan.external']

    if ignore_all:
        Log.Debug("Force refresh intended.")

    Log.Debug("Scanning video: %s, subtitles=%s, embedded_subtitles=%s" % (plex_part.file, external_subtitles, embedded_subtitles))

    try:
        return subliminal.video.scan_video(plex_part.file, subtitles=external_subtitles, embedded_subtitles=embedded_subtitles,
                                           hints=hints or {}, video_fps=plex_part.fps)

    except ValueError:
        Log.Warn("File could not be guessed by subliminal")


def scan_videos(videos, kind="series"):
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

        hints = helpers.get_item_hints(video["title"], kind, series=video["series"] if kind == "series" else None)
        video["plex_part"].fps = get_stream_fps(video["plex_part"].streams)
        scanned_video = scan_video(video["plex_part"], ignore_all=force_refresh, hints=hints)
        if not scanned_video:
            continue

        scanned_video.id = video["id"]
        part_metadata = video.copy()
        del part_metadata["plex_part"]
        scanned_video.plexapi_metadata = part_metadata
        ret[scanned_video] = video["plex_part"]
    return ret