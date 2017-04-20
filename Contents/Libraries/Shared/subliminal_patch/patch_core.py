# coding=utf-8
import os
import logging
import socket
import traceback

import time

import operator
from collections import defaultdict

import requests
from babelfish import LanguageReverseError
from subliminal import ProviderError

from subliminal.score import compute_score as default_compute_score
from subliminal.subtitle import SUBTITLE_EXTENSIONS, get_subtitle_path
from subliminal.utils import hash_napiprojekt, hash_opensubtitles, hash_shooter, hash_thesubdb
from subliminal.video import VIDEO_EXTENSIONS, Episode, Movie, Video
from subliminal.core import guessit, Language, ProviderPool

logger = logging.getLogger(__name__)

# may be absolute or relative paths; set to selected options
CUSTOM_PATHS = []
INCLUDE_EXOTIC_SUBS = True

DOWNLOAD_TRIES = 0
DOWNLOAD_RETRY_SLEEP = 2


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
                os.path.join(*[video_path if not os.path.isabs(folder_or_subfolder) else "", folder_or_subfolder,
                               video_filename])))
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

    def download_subtitle(self, subtitle):
        """Download `subtitle`'s :attr:`~subliminal.subtitle.Subtitle.content`.
        
        patch: add retry functionality
        
        :param subtitle: subtitle to download.
        :type subtitle: :class:`~subliminal.subtitle.Subtitle`
        :return: `True` if the subtitle has been successfully downloaded, `False` otherwise.
        :rtype: bool
        """
        # check discarded providers
        if subtitle.provider_name in self.discarded_providers:
            logger.warning('Provider %r is discarded', subtitle.provider_name)
            return False

        logger.info('Downloading subtitle %r', subtitle)
        tries = 0

        # retry downloading on failure until settings' download retry limit hit
        while True:
            tries += 1
            try:
                self[subtitle.provider_name].download_subtitle(subtitle)
                break
            except (requests.Timeout, socket.timeout):
                logger.error('Provider %r timed out', subtitle.provider_name)
            except ProviderError:
                logger.error('Unexpected error in provider %r, Traceback: %s', subtitle.provider_name,
                             traceback.format_exc())
            except:
                logger.exception('Unexpected error in provider %r, Traceback: %s', subtitle.provider_name,
                                 traceback.format_exc())

            if tries == DOWNLOAD_TRIES:
                self.discarded_providers.add(subtitle.provider_name)
                logger.error('Maximum retries reached for provider %r, discarding it', subtitle.provider_name)
                return False

            # don't hammer the provider
            logger.debug('Errors while downloading subtitle, retrying provider %r in %s seconds',
                         subtitle.provider_name, DOWNLOAD_RETRY_SLEEP)
            time.sleep(DOWNLOAD_RETRY_SLEEP)

        # check subtitle validity
        if not subtitle.is_valid():
            logger.error('Invalid subtitle')
            return False

        return True

    def download_best_subtitles(self, subtitles, video, languages, min_score=0, hearing_impaired=False, only_one=False,
                                compute_score=None):
        """Download the best matching subtitles.
        
        patch: 
            - hearing_impaired is now string
            - add .score to subtitle
            - move all languages check further to the top (still necessary?)

        :param subtitles: the subtitles to use.
        :type subtitles: list of :class:`~subliminal.subtitle.Subtitle`
        :param video: video to download subtitles for.
        :type video: :class:`~subliminal.video.Video`
        :param languages: languages to download.
        :type languages: set of :class:`~babelfish.language.Language`
        :param int min_score: minimum score for a subtitle to be downloaded.
        :param bool hearing_impaired: hearing impaired preference.
        :param bool only_one: download only one subtitle, not one per language.
        :param compute_score: function that takes `subtitle` and `video` as positional arguments,
            `hearing_impaired` as keyword argument and returns the score.
        :return: downloaded subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle`

        """
        compute_score = compute_score or default_compute_score
        use_hearing_impaired = hearing_impaired in ("prefer", "force HI")

        # sort subtitles by score
        unsorted_subtitles = []

        for s in subtitles:
            # get the matches
            try:
                matches = s.get_matches(video)
            except AttributeError:
                logger.error("Match computation failed for %s: %s", s, traceback.format_exc())
                continue

            logger.debug('Found matches %r', matches)
            unsorted_subtitles.append(
                (s, compute_score(matches, s, video, hearing_impaired=use_hearing_impaired), matches))

        # sort subtitles by score
        scored_subtitles = sorted(unsorted_subtitles, key=operator.itemgetter(1), reverse=True)

        # download best subtitles, falling back on the next on error
        downloaded_subtitles = []
        for subtitle, score, matches in scored_subtitles:
            # check score
            if score < min_score:
                logger.info('Score %d is below min_score (%d)', score, min_score)
                break

            # stop when all languages are downloaded
            if set(s.language for s in downloaded_subtitles) == languages:
                logger.debug('All languages downloaded')
                break

            # check downloaded languages
            if subtitle.language in set(s.language for s in downloaded_subtitles):
                logger.debug('Skipping subtitle: %r already downloaded', subtitle.language)
                continue

            # bail out if hearing_impaired was wrong
            if "hearing_impaired" not in matches and hearing_impaired in ("force HI", "force non-HI"):
                logger.debug('Skipping subtitle: %r with score %d because hearing-impaired set to %s', subtitle,
                             score, hearing_impaired)
                continue

            # download
            if self.download_subtitle(subtitle):
                subtitle.score = score
                downloaded_subtitles.append(subtitle)

            # stop if only one subtitle is requested
            if only_one:
                logger.debug('Only one subtitle downloaded')
                break

        return downloaded_subtitles


def list_all_subtitles(videos, languages, **kwargs):
    """List all available subtitles.
    
    patch: remove video check, it has been done before

    The `videos` must pass the `languages` check of :func:`check_video`.

    All other parameters are passed onwards to the :class:`ProviderPool` constructor.

    :param videos: videos to list subtitles for.
    :type videos: set of :class:`~subliminal.video.Video`
    :param languages: languages to search for.
    :type languages: set of :class:`~babelfish.language.Language`
    :return: found subtitles per video.
    :rtype: dict of :class:`~subliminal.video.Video` to list of :class:`~subliminal.subtitle.Subtitle`

    """
    listed_subtitles = defaultdict(list)

    # return immediatly if no video passed the checks
    if not videos:
        return listed_subtitles

    # list subtitles
    with PatchedProviderPool(**kwargs) as pool:
        for video in videos:
            logger.info('Listing subtitles for %r', video)
            subtitles = pool.list_subtitles(video, languages - video.subtitle_languages)
            listed_subtitles[video].extend(subtitles)
            logger.info('Found %d subtitle(s)', len(subtitles))

    return listed_subtitles