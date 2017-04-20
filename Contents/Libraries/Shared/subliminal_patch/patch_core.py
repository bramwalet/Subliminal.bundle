# coding=utf-8
import os
import logging
import traceback

from babelfish import LanguageReverseError

from subliminal.score import compute_score as default_compute_score
from subliminal.subtitle import SUBTITLE_EXTENSIONS, get_subtitle_path
from subliminal.utils import hash_napiprojekt, hash_opensubtitles, hash_shooter, hash_thesubdb
from subliminal.video import VIDEO_EXTENSIONS, Episode, Movie, Video
from subliminal.core import guessit, Language, ProviderPool

logger = logging.getLogger(__name__)

# may be absolute or relative paths; set to selected options
CUSTOM_PATHS = []
INCLUDE_EXOTIC_SUBS = True


def scan_video(path, dont_use_actual_file=False):
    """Scan a video from a `path`.

    :param str path: existing path to the video.
    :return: the scanned video.
    :rtype: :class:`~subliminal.video.Video`

    """
    # check for non-existing path
    if not dont_use_actual_file and not os.path.exists(path):
        raise ValueError('Path does not exist')

    # check video extension
    if not path.endswith(VIDEO_EXTENSIONS):
        raise ValueError('%r is not a valid video extension' % os.path.splitext(path)[1])

    dirpath, filename = os.path.split(path)
    logger.info('Scanning video %r in %r', filename, dirpath)

    # guess
    video = Video.fromguess(path, guessit(path, options={}))

    if dont_use_actual_file:
        return video

    # size and hashes
    video.size = os.path.getsize(path)
    if video.size > 10485760:
        logger.debug('Size is %d', video.size)
        video.hashes['opensubtitles'] = hash_opensubtitles(path)
        video.hashes['shooter'] = hash_shooter(path)
        video.hashes['thesubdb'] = hash_thesubdb(path)
        video.hashes['napiprojekt'] = hash_napiprojekt(path)
        logger.debug('Computed hashes %r', video.hashes)
    else:
        logger.warning('Size is lower than 10MB: hashes not computed')

    return video


def _search_external_subtitles(path, forced_tag=False):
    dirpath, filename = os.path.split(path)
    dirpath = dirpath or '.'
    fileroot, fileext = os.path.splitext(filename)
    subtitles = {}
    for p in os.listdir(dirpath):
        # keep only valid subtitle filenames
        if not p.startswith(fileroot) or not p.endswith(SUBTITLE_EXTENSIONS):
            continue

        p_root, p_ext = os.path.splitext(p)
        if not INCLUDE_EXOTIC_SUBS and p_ext not in (".srt", ".ass", ".ssa"):
            continue

        # extract potential forced/normal/default tag
        # fixme: duplicate from subtitlehelpers
        split_tag = p_root.rsplit('.', 1)
        adv_tag = None
        if len(split_tag) > 1:
            adv_tag = split_tag[1].lower()
            if adv_tag in ['forced', 'normal', 'default']:
                p_root = split_tag[0]

        # forced wanted but NIL
        if forced_tag and adv_tag != "forced":
            continue

        # extract the potential language code
        language_code = p_root[len(fileroot):].replace('_', '-')[1:]

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


def search_external_subtitles(path, forced_tag=False):
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
            subtitles.update(_search_external_subtitles(abspath, forced_tag=forced_tag))
    logger.debug("external subs: found %s", subtitles)
    return subtitles


class PatchedProviderPool(ProviderPool):
    def list_subtitles(self, video, languages):
        """List subtitles.
        
        patch: handle LanguageReverseError

        :param video: video to list subtitles for.
        :type video: :class:`~subliminal.video.Video`
        :param languages: languages to search for.
        :type languages: set of :class:`~babelfish.language.Language`
        :return: found subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle`

        """
        subtitles = []

        for name in self.providers:
            # check discarded providers
            if name in self.discarded_providers:
                logger.debug('Skipping discarded provider %r', name)
                continue

            # list subtitles
            try:
                provider_subtitles = self.list_subtitles_provider(name, video, languages)
            except LanguageReverseError:
                logger.exception("Unexpected language reverse error in %s, skipping. Error: %s", name,
                                 traceback.format_exc())
                continue

            if provider_subtitles is None:
                logger.info('Discarding provider %s', name)
                self.discarded_providers.add(name)
                continue

            # add the subtitles
            subtitles.extend(provider_subtitles)

        return subtitles