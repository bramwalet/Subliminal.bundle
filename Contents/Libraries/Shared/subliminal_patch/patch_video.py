# coding=utf-8

import os
import logging
import traceback

from babelfish import Error as BabelfishError
from subliminal.video import SUBTITLE_EXTENSIONS, VIDEO_EXTENSIONS, Language, Video, EnzymeError, MKV, \
    guess_file_info, hash_opensubtitles, hash_thesubdb

logger = logging.getLogger(__name__)

# may be absolute or relative paths; set to selected options
CUSTOM_PATHS = []


def _search_external_subtitles(path):
    dirpath, filename = os.path.split(path)
    dirpath = dirpath or '.'
    fileroot, fileext = os.path.splitext(filename)
    subtitles = {}
    for p in os.listdir(dirpath):
        # keep only valid subtitle filenames
        if not p.startswith(fileroot) or not p.endswith(SUBTITLE_EXTENSIONS):
            continue

        # extract the potential language code
        language_code = p[len(fileroot):-len(os.path.splitext(p)[1])].replace(fileext, '').replace('_', '-')[1:]

        # default language is undefined
        language = Language('und')

        # attempt to parse
        if language_code:
            try:
                language = Language.fromietf(language_code)
            except ValueError:
                logger.error('Cannot parse language code %r', language_code)

        subtitles[p] = language

    logger.debug('Found subtitles %r', subtitles)

    return subtitles


def patched_search_external_subtitles(path):
    """
    wrap original search_external_subtitles function to search multiple paths for one given video
    # todo: cleanup and merge with _search_external_subtitles
    """
    video_path, video_filename = os.path.split(path)
    subtitles = {}
    for folder_or_subfolder in [video_path] + CUSTOM_PATHS:
        # folder_or_subfolder may be a relative path or an absolute one
        try:
            abspath = unicode(os.path.abspath(
                os.path.join(*[video_path if not os.path.isabs(folder_or_subfolder) else "", folder_or_subfolder, video_filename])))
        except Exception, e:
            logger.error("skipping path %s because of %s", repr(folder_or_subfolder), e)
            continue
        logger.debug("external subs: scanning path %s", abspath)

        if os.path.isdir(os.path.dirname(abspath)):
            subtitles.update(_search_external_subtitles(abspath))
    logger.debug("external subs: found %s", subtitles)
    return subtitles


def scan_video(path, subtitles=True, embedded_subtitles=True, hints=None, video_fps=None, dont_use_actual_file=False):
    """Scan a video and its subtitle languages from a video `path`.
    :param dont_use_actual_file: guess on filename, but don't use the actual file itself
    :param str path: existing path to the video.
    :param bool subtitles: scan for subtitles with the same name.
    :param bool embedded_subtitles: scan for embedded subtitles.
    :param hints: hints dict for guessit
    :return: the scanned video.
    :rtype: :class:`Video`

    # patch: suggest video type to guessit beforehand
    """
    hints = hints or {}
    video_type = hints.get("type")

    # check for non-existing path
    if not dont_use_actual_file and not os.path.exists(path):
        raise ValueError('Path does not exist')

    # check video extension
    if not path.endswith(VIDEO_EXTENSIONS):
        raise ValueError('%s is not a valid video extension' % os.path.splitext(path)[1])

    dirpath, filename = os.path.split(path)

    # hint guessit the filename itself and its 2 parent directories if we're an episode (most likely Series name/Season/filename), else only one
    guess_from = os.path.join(*os.path.normpath(path).split(os.path.sep)[-3 if video_type == "episode" else -2:])
    hints = hints or {}
    logger.info('Scanning video (hints: %s) %r', hints, guess_from)

    # guess
    video = Video.fromguess(path, guess_file_info(guess_from, options=hints))
    video.fps = video_fps

    # trust plex's series name
    if video_type == "episode" and hints.get("expected_series"):
        video.series = hints.get("expected_series")[0]

    # trust plex's movie name
    if video_type == "movie" and hints.get("expected_title"):
        video.title = hints.get("expected_title")[0]

    if dont_use_actual_file:
        return video

    # size and hashes
    video.size = os.path.getsize(path)
    if video.size > 10485760:
        logger.debug('Size is %d', video.size)
        video.hashes['opensubtitles'] = hash_opensubtitles(path)
        video.hashes['thesubdb'] = hash_thesubdb(path)
        logger.debug('Computed hashes %r', video.hashes)
    else:
        logger.warning('Size is lower than 10MB: hashes not computed')

    # external subtitles
    if subtitles:
        video.subtitle_languages |= set(patched_search_external_subtitles(path).values())


    # video metadata with enzyme
    try:
        if filename.endswith('.mkv'):
            with open(path, 'rb') as f:
                mkv = MKV(f)

            # main video track
            if mkv.video_tracks:
                video_track = mkv.video_tracks[0]

                # resolution
                if video_track.height in (480, 720, 1080):
                    if video_track.interlaced:
                        video.resolution = '%di' % video_track.height
                    else:
                        video.resolution = '%dp' % video_track.height
                    logger.debug('Found resolution %s with enzyme', video.resolution)

                # video codec
                if video_track.codec_id == 'V_MPEG4/ISO/AVC':
                    video.video_codec = 'h264'
                    logger.debug('Found video_codec %s with enzyme', video.video_codec)
                elif video_track.codec_id == 'V_MPEG4/ISO/SP':
                    video.video_codec = 'DivX'
                    logger.debug('Found video_codec %s with enzyme', video.video_codec)
                elif video_track.codec_id == 'V_MPEG4/ISO/ASP':
                    video.video_codec = 'XviD'
                    logger.debug('Found video_codec %s with enzyme', video.video_codec)
            else:
                logger.warning('MKV has no video track')

            # main audio track
            if mkv.audio_tracks:
                audio_track = mkv.audio_tracks[0]
                # audio codec
                if audio_track.codec_id == 'A_AC3':
                    video.audio_codec = 'AC3'
                    logger.debug('Found audio_codec %s with enzyme', video.audio_codec)
                elif audio_track.codec_id == 'A_DTS':
                    video.audio_codec = 'DTS'
                    logger.debug('Found audio_codec %s with enzyme', video.audio_codec)
                elif audio_track.codec_id == 'A_AAC':
                    video.audio_codec = 'AAC'
                    logger.debug('Found audio_codec %s with enzyme', video.audio_codec)
            else:
                logger.warning('MKV has no audio track')

            # subtitle tracks
            if mkv.subtitle_tracks:
                if embedded_subtitles:
                    embedded_subtitle_languages = set()
                    for st in mkv.subtitle_tracks:
                        if st.forced:
                            logger.debug("Ignoring forced subtitle track %r", st)
                            continue
                        if st.language:
                            try:
                                embedded_subtitle_languages.add(Language.fromalpha3b(st.language))
                            except BabelfishError:
                                logger.error('Embedded subtitle track language %r is not a valid language', st.language)
                                embedded_subtitle_languages.add(Language('und'))
                        elif st.name:
                            try:
                                embedded_subtitle_languages.add(Language.fromname(st.name))
                            except BabelfishError:
                                logger.debug('Embedded subtitle track name %r is not a valid language', st.name)
                                embedded_subtitle_languages.add(Language('und'))
                        else:
                            embedded_subtitle_languages.add(Language('und'))
                    logger.debug('Found embedded subtitle %r with enzyme', embedded_subtitle_languages)
                    video.subtitle_languages |= embedded_subtitle_languages
            else:
                logger.debug('MKV has no subtitle track')

    except EnzymeError:
        logger.error('Parsing video metadata with enzyme failed')

    except Exception:
        logger.error("Parsing video with enzyme has gone terribly wrong: %s", traceback.format_exc())

    return video
