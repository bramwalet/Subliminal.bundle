# coding=utf-8
import logging
import os

from babelfish.exceptions import LanguageError
from babelfish import Language
from subliminal_patch import scan_video, refine, search_external_subtitles


logger = logging.getLogger(__name__)


def parse_video(fn, video_info, hints, external_subtitles=False, embedded_subtitles=False, known_embedded=None,
                forced_only=False, video_fps=None, dry_run=False):

    logger.debug("Parsing video: %s, hints: %s", os.path.basename(fn), hints)
    video = scan_video(fn, hints=hints, dont_use_actual_file=dry_run)

    # refiners

    refine_kwargs = {
        "episode_refiners": ('tvdb', 'sz_omdb'),
        "movie_refiners": ('sz_omdb',),
        "embedded_subtitles": False,
    }

    # our own metadata refiner :)
    if "stream" in video_info:
        for key, value in video_info["stream"].iteritems():
            if hasattr(video, key) and not getattr(video, key):
                logger.info(u"Adding stream %s info: %s", key, value)
                setattr(video, key, value)

    plex_title = video_info.get("original_title") or video_info.get("title")
    if hints["type"] == "episode":
        plex_title = video_info.get("original_title") or video_info.get("series")

    if not video.year:
        video.year = video_info.get("year")

    refine(video, **refine_kwargs)

    if not video.imdb_id:
        video.imdb_id = video_info.get("imdb_id")
        if video.imdb_id:
            logger.info(u"Adding PMS imdb_id info: %s", video.imdb_id)

    if hints["type"] == "episode":
        if not video.series_tvdb_id:
            logger.info(u"Adding PMS series_tvdb_id info: %s", video_info.get("series_tvdb_id"))
            video.series_tvdb_id = video_info.get("series_tvdb_id")

        if not video.tvdb_id:
            logger.info(u"Adding PMS tvdb_id info: %s", video_info.get("tvdb_id"))
            video.tvdb_id = video_info.get("tvdb_id")

    # re-refine with plex's known data?
    refine_with_plex = False

    # episode but wasn't able to match title
    if plex_title:
        if hints["type"] == "episode" and not video.series_tvdb_id and not video.tvdb_id and not video.series_imdb_id \
                and video.series != plex_title:
            logger.info(u"Re-refining with series title: '%s' instead of '%s'", plex_title, video.series)
            video.series = plex_title
            refine_with_plex = True

        # movie
        elif hints["type"] == "movie" and not video.imdb_id and video.title != plex_title:
            # movie
            logger.info(u"Re-refining with series title: '%s' instead of '%s'", plex_title, video.title)
            video.title = plex_title.replace(" - ", " ").replace(" -", " ").replace("- ", " ")
            refine_with_plex = True

    # title not matched? try plex title hint
    if refine_with_plex:
        refine(video, **refine_kwargs)

        # did it match now?
        if (hints["type"] == "episode" and not video.series_tvdb_id and not video.tvdb_id and
                not video.series_imdb_id) or (hints["type"] == "movie" and not video.imdb_id):
            logger.warning("Couldn't find corresponding series/movie in online databases, continuing")

    # scan for external subtitles
    if external_subtitles:
        # |= is update, thanks plex
        video.subtitle_languages.update(
            set(search_external_subtitles(video.name, forced_tag=forced_only).values())
        )

    # add video fps info
    video.fps = video_fps

    # add known embedded subtitles
    if embedded_subtitles and known_embedded:
        embedded_subtitle_languages = set()
        # mp4 and stuff, check burned in
        for language in known_embedded:
            try:
                embedded_subtitle_languages.add(Language.fromalpha3b(language))
            except LanguageError:
                logger.error('Embedded subtitle track language %r is not a valid language', language)
                embedded_subtitle_languages.add(Language('und'))

            logger.debug('Found embedded subtitle %r', embedded_subtitle_languages)
            video.subtitle_languages.update(embedded_subtitle_languages)

    # guess special
    if hints["type"] == "episode":
        if video.season == 0 or video.episode == 0:
            video.is_special = True
        else:
            # check parent folder name
            if os.path.dirname(fn).split(os.path.sep)[-1].lower() in ("specials", "season 00"):
                video.is_special = True

    return video
