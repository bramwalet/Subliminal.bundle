# coding=utf-8

import io
import logging
import os
from random import randint
from zipfile import ZipFile

from babelfish import language_converters
from guessit import guessit
from requests import Session
from subliminal import Episode
from subliminal.utils import sanitize_release_group
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.converters.subscene import language_ids, supported_languages
from subscene_api.subscene import search, Subtitle as APISubtitle
from subzero.language import Language


language_converters.register('subscene = subliminal_patch.converters.subscene:SubsceneConverter')
logger = logging.getLogger(__name__)


class SubsceneSubtitle(Subtitle):
    provider_name = 'subscene'
    hearing_impaired_verifiable = True
    is_pack = False
    page_link = None

    def __init__(self, language, release_info, hearing_impaired=False, page_link=None, encoding=None, mods=None):
        super(SubsceneSubtitle, self).__init__(language, hearing_impaired=hearing_impaired, page_link=page_link,
                                               encoding=encoding, mods=mods)
        self.release_info = release_info

    @classmethod
    def from_api(cls, s):
        return cls(Language.fromsubscene(s.language.strip()), s.title, hearing_impaired=s.hearing_impaired,
                   page_link=s.url)

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        matches = set()

        if self.release_info.strip() == get_video_filename(video):
            logger.debug("Using hash match as the release name is the same")
            return {"hash"}

        # episode
        if isinstance(video, Episode):
            guess = guessit(self.release_info, {'type': 'episode'})
            matches |= guess_matches(video, guess)
            if "season" in matches and "episode" not in guess:
                # pack
                matches.add("episode")
                self.is_pack = True

        # movie
        else:
            guess = guessit(self.release_info, {'type': 'movie'})
            matches |= guess_matches(video, guess)

        if "release_group" not in matches:
            if sanitize_release_group(video.release_group) in sanitize_release_group(guess["release_group"]):
                matches.add("release_group")

        return matches

    def get_download_link(self, session):
        return APISubtitle.get_zipped_url(self.page_link, session)


def get_video_filename(video):
    return os.path.splitext(os.path.basename(video.name))[0]


class SubsceneProvider(Provider, ProviderSubtitleArchiveMixin):
    """
    This currently only searches for the filename on SubScene. It doesn't open every found subtitle page to avoid
    massive hammering, thus it can't determine whether a subtitle is only-foreign or not.
    """
    subtitle_class = SubsceneSubtitle
    languages = supported_languages
    session = None
    skip_wrong_fps = False
    hearing_impaired_verifiable = True

    def initialize(self):
        logger.info("Creating session")
        self.session = Session()
        from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    def terminate(self):
        logger.info("Closing session")
        self.session.close()

    def _create_filters(self, languages):
        self.filters = dict(ForeignOnly="False", HearingImpaired="2")

        self.filters["LanguageFilter"] = ",".join((str(language_ids[l.alpha3]) for l in languages
                                                   if l.alpha3 in language_ids))

        logger.debug("Filter created: '%s'" % self.filters)

    def _enable_filters(self):
        self.session.cookies.update(self.filters)
        logger.debug("Filters applied")

    def list_subtitles(self, video, languages):
        if not video.original_name:
            logger.info("Skipping search because we don't know the original release name")
            return []

        self._create_filters(languages)
        self._enable_filters()
        return [s for s in self.query(video) if s.language in languages]

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.get_download_link(self.session), timeout=10)
        r.raise_for_status()

        # open the archive
        archive_stream = io.BytesIO(r.content)
        archive = ZipFile(archive_stream)

        subtitle.content = self.get_subtitle_from_archive(subtitle, archive)

    def query(self, video):
        film = search(get_video_filename(video), session=self.session)

        subtitles = []
        if film:
            if film.subtitles:
                for s in film.subtitles:
                    subtitle = SubsceneSubtitle.from_api(s)
                    subtitles.append(subtitle)
                    logger.debug('Found subtitle %r', subtitle)

        logger.info("%s subtitles found" % len(subtitles))
        return subtitles
