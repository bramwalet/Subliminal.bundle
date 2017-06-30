# coding=utf-8

import os
from urllib2 import URLError

import helpers
from config import config
from items import get_item
from lib import get_intent, Plex
from subzero.video import parse_video

def get_metadata_dict(item, part, add):
    data = {
        "item": item,
        "section": item.section.title,
        "path": part.file,
        "folder": os.path.dirname(part.file),
        "filename": os.path.basename(part.file)
    }
    data.update(add)
    return data


imdb_guid_identifier = "com.plexapp.agents.imdb://"
tvdb_guid_identifier = "com.plexapp.agents.thetvdb://"


def get_plexapi_stream_info(plex_item, part_id=None):
    d = {"stream": {}}
    data = d["stream"]

    # find current part
    current_part = None
    current_media = None
    for media in plex_item.media:
        for part in media.parts:
            if not part_id or str(part.id) == part_id:
                current_part = part
                current_media = media
                break
        if current_part:
            break

    if not current_part:
        return d

    data["video_codec"] = current_media.video_codec
    data["audio_codec"] = current_media.audio_codec.upper()

    if data["audio_codec"] == "DCA":
        data["audio_codec"] = "DTS"

    if current_media.audio_channels == 8:
        data["audio_channels"] = "7.1"

    elif current_media.audio_channels == 6:
        data["audio_channels"] = "5.1"
    else:
        data["audio_channels"] = "%s.0" % str(current_media.audio_channels)

    # iter streams
    for stream in current_part.streams:
        if stream.stream_type == 1:
            # video stream
            data["resolution"] = "%s%s" % (current_media.video_resolution,
                                           "i" if stream.scan_type != "progressive" else "p")
            break

    return d


def media_to_videos(media, kind="series"):
    """
    iterates through media and returns the associated parts (videos)
    :param media:
    :param kind:
    :return:
    """
    videos = []

    # this is a Show or a Movie object
    plex_item = get_item(media.id)
    year = plex_item.year
    original_title = plex_item.title_original

    if kind == "series":
        for season in media.seasons:
            season_object = media.seasons[season]
            for episode in media.seasons[season].episodes:
                ep = media.seasons[season].episodes[episode]

                tvdb_id = None
                series_tvdb_id = None
                if tvdb_guid_identifier in ep.guid:
                    tvdb_id = ep.guid[len(tvdb_guid_identifier):].split("?")[0]
                    series_tvdb_id = tvdb_id.split("/")[0]

                # get plex item via API for additional metadata
                plex_episode = get_item(ep.id)
                stream_info = get_plexapi_stream_info(plex_episode)

                for item in media.seasons[season].episodes[episode].items:
                    for part in item.parts:
                        videos.append(
                            get_metadata_dict(plex_episode, part,
                                              dict(stream_info, **{"plex_part": part, "type": "episode",
                                                                    "title": ep.title,
                                                                    "series": media.title, "id": ep.id, "year": year,
                                                                    "series_id": media.id,
                                                                    "season_id": season_object.id,
                                                                    "imdb_id": None, "series_tvdb_id": series_tvdb_id,
                                                                    "tvdb_id": tvdb_id,
                                                                    "original_title": original_title,
                                                                    "episode": plex_episode.index,
                                                                    "season": plex_episode.season.index,
                                                                    "section": plex_episode.section.title
                                                                    })
                                              )
                        )
    else:
        stream_info = get_plexapi_stream_info(plex_item)
        imdb_id = None
        if imdb_guid_identifier in media.guid:
            imdb_id = media.guid[len(imdb_guid_identifier):].split("?")[0]
        for item in media.items:
            for part in item.parts:
                videos.append(
                    get_metadata_dict(plex_item, part, dict(stream_info, **{"plex_part": part, "type": "movie",
                                                                             "title": media.title, "id": media.id,
                                                                             "series_id": None, "year": year,
                                                                             "season_id": None, "imdb_id": imdb_id,
                                                                             "original_title": original_title,
                                                                             "series_tvdb_id": None, "tvdb_id": None,
                                                                             "section": plex_item.section.title})
                                      )
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
                    if not stream.stream_key:
                        if config.exotic_ext or stream.codec in ("srt", "ass", "ssa"):
                            lang_code = stream.language_code

                            # treat unknown language as lang1?
                            if not lang_code and config.treat_und_as_first:
                                lang_code = list(config.lang_list)[0].alpha3
                            known_embedded.append(lang_code)
    else:
        Log.Warn("Part %s missing of %s, not able to scan internal streams", plex_part.id, rating_key)

    try:
        # get basic video info scan (filename)
        video = parse_video(plex_part.file, pms_video_info, hints, external_subtitles=external_subtitles,
                            embedded_subtitles=embedded_subtitles, known_embedded=known_embedded,
                            forced_only=config.forced_only, no_refining=no_refining)

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


def get_plex_metadata(rating_key, part_id, item_type, plex_item=None):
    """
    uses the Plex 3rd party API accessor to get metadata information

    :param rating_key: movie or episode
    :param part_id:
    :param item_type:
    :return:
    """

    if not plex_item:
        plex_item = get_item(rating_key)

    if not plex_item:
        return

    # find current part
    current_part = None
    for media in plex_item.media:
        for part in media.parts:
            if str(part.id) == str(part_id):
                current_part = part

    if not current_part:
        raise helpers.PartUnknownException("Part unknown")

    stream_info = get_plexapi_stream_info(plex_item, part_id)

    # get normalized metadata
    # fixme: duplicated logic of media_to_videos
    if item_type == "episode":
        show = list(Plex["library"].metadata(plex_item.show.rating_key))[0]
        year = show.year
        tvdb_id = None
        series_tvdb_id = None
        original_title = show.title_original
        if tvdb_guid_identifier in plex_item.guid:
            tvdb_id = plex_item.guid[len(tvdb_guid_identifier):].split("?")[0]
            series_tvdb_id = tvdb_id.split("/")[0]
        metadata = get_metadata_dict(plex_item, current_part,
                                     dict(stream_info,
                                          **{"plex_part": current_part, "type": "episode", "title": plex_item.title,
                                             "series": plex_item.show.title, "id": plex_item.rating_key,
                                             "series_id": plex_item.show.rating_key,
                                             "season_id": plex_item.season.rating_key,
                                             "imdb_id": None,
                                             "year": year,
                                             "tvdb_id": tvdb_id,
                                             "series_tvdb_id": series_tvdb_id,
                                             "original_title": original_title,
                                             "season": plex_item.season.index,
                                             "episode": plex_item.index
                                             })
                                     )
    else:
        imdb_id = None
        original_title = plex_item.title_original
        if imdb_guid_identifier in plex_item.guid:
            imdb_id = plex_item.guid[len(imdb_guid_identifier):].split("?")[0]
        metadata = get_metadata_dict(plex_item, current_part,
                                     dict(stream_info, **{"plex_part": current_part, "type": "movie",
                                                           "title": plex_item.title, "id": plex_item.rating_key,
                                                           "series_id": None,
                                                           "season_id": None,
                                                           "imdb_id": imdb_id,
                                                           "year": plex_item.year,
                                                           "tvdb_id": None,
                                                           "series_tvdb_id": None,
                                                           "original_title": original_title,
                                                           "season": None,
                                                           "episode": None,
                                                           "section": plex_item.section.title})
                                     )
    return metadata


class PMSMediaProxy(object):
    """
    Proxy object for getting data from a mediatree items "internally" via the PMS

    note: this could be useful later on: Media.TV_Show(getattr(Metadata, "_access_point"), id=XXXXXX)
    """

    def __init__(self, media_id):
        self.mediatree = Media.TreeForDatabaseID(media_id)

    def get_part(self, part_id=None):
        """
        walk the mediatree until the given part was found; if no part was given, return the first one
        :param part_id:
        :return:
        """
        m = self.mediatree
        while 1:
            if m.items:
                media_item = m.items[0]
                if not part_id:
                    return media_item.parts[0] if media_item.parts else None

                for part in media_item.parts:
                    if str(part.id) == str(part_id):
                        return part
                break

            if not m.children:
                break

            m = m.children[0]

    def get_all_parts(self):
        """
        walk the mediatree until the given part was found; if no part was given, return the first one
        :param part_id:
        :return:
        """
        m = self.mediatree
        parts = []
        while 1:
            if m.items:
                media_item = m.items[0]
                for part in media_item.parts:
                    parts.append(part)
                break

            if not m.children:
                break

            m = m.children[0]
        return parts
