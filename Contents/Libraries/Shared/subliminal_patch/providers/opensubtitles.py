# coding=utf-8

import logging
import os

import dogpile
from babelfish import Language, language_converters
from dogpile.cache.api import NO_VALUE
from subliminal.exceptions import ConfigurationError
from subliminal.providers.opensubtitles import OpenSubtitlesProvider as _OpenSubtitlesProvider, checked, \
    __short_version__, \
    OpenSubtitlesSubtitle as _OpenSubtitlesSubtitle, Episode, ServerProxy, Unauthorized
from mixins import ProviderRetryMixin
from subliminal_patch.http import TimeoutSafeTransport, TimeoutTransport
from subliminal.cache import region

logger = logging.getLogger(__name__)


class OpenSubtitlesSubtitle(_OpenSubtitlesSubtitle):
    hash_verifiable = True
    hearing_impaired_verifiable = True

    def __init__(self, language, hearing_impaired, page_link, subtitle_id, matched_by, movie_kind, hash, movie_name,
                 movie_release_name, movie_year, movie_imdb_id, series_season, series_episode, query_parameters,
                 filename, encoding, fps, skip_wrong_fps=True):
        super(OpenSubtitlesSubtitle, self).__init__(language, hearing_impaired, page_link, subtitle_id,
                                                    matched_by, movie_kind, hash,
                                                    movie_name, movie_release_name, movie_year, movie_imdb_id,
                                                    series_season, series_episode, filename, encoding)
        self.query_parameters = query_parameters or {}
        self.fps = fps
        self.release_info = movie_release_name
        self.wrong_fps = False
        self.skip_wrong_fps = skip_wrong_fps

    def get_matches(self, video, hearing_impaired=False):
        matches = super(OpenSubtitlesSubtitle, self).get_matches(video)

        sub_fps = None
        try:
            sub_fps = float(self.fps)
        except ValueError:
            pass

        # video has fps info, sub also, and sub's fps is greater than 0
        if video.fps and sub_fps and (video.fps != self.fps):
            self.wrong_fps = True

            if self.skip_wrong_fps:
                logger.debug("Wrong FPS (expected: %s, got: %s, lowering score massively)", video.fps, self.fps)
                # fixme: may be too harsh
                return set()
            else:
                logger.debug("Wrong FPS (expected: %s, got: %s, continuing)", video.fps, self.fps)

        # matched by tag?
        if self.matched_by == "tag":
            # treat a tag match equally to a hash match
            logger.debug("Subtitle matched by tag, treating it as a hash-match. Tag: '%s'",
                         self.query_parameters.get("tag", None))
            matches.add("hash")

        return matches


class OpenSubtitlesProvider(ProviderRetryMixin, _OpenSubtitlesProvider):
    only_foreign = True
    subtitle_class = OpenSubtitlesSubtitle
    hash_verifiable = True
    hearing_impaired_verifiable = True
    skip_wrong_fps = True
    is_vip = False

    default_url = "https://api.opensubtitles.org/xml-rpc"
    vip_url = "https://vip-api.opensubtitles.org/xml-rpc"

    languages = {Language.fromopensubtitles(l) for l in language_converters['szopensubtitles'].codes}# | {
        #Language.fromietf("sr-latn"), Language.fromietf("sr-cyrl")}

    def __init__(self, username=None, password=None, use_tag_search=False, only_foreign=False, skip_wrong_fps=True,
                 is_vip=False):
        if username is not None and password is None or username is None and password is not None:
            raise ConfigurationError('Username and password must be specified')

        self.username = username or ''
        self.password = password or ''
        self.use_tag_search = use_tag_search
        self.only_foreign = only_foreign
        self.skip_wrong_fps = skip_wrong_fps
        self.token = None
        self.is_vip = is_vip

        if is_vip:
            self.server = self.get_server_proxy(self.vip_url)
            logger.info("Using VIP server")
        else:
            self.server = self.get_server_proxy(self.default_url)

        if use_tag_search:
            logger.info("Using tag/exact filename search")

        if only_foreign:
            logger.info("Only searching for foreign/forced subtitles")

    def get_server_proxy(self, url, timeout=10):
        transport = TimeoutSafeTransport if url.startswith("https") else TimeoutTransport
        return ServerProxy(url, transport(timeout))

    def log_in(self, server_url=None):
        if server_url:
            if self.server:
                self.server.close()

            self.server = self.get_server_proxy(server_url)

        response = self.retry(
            lambda: checked(
                self.server.LogIn(self.username, self.password, 'eng',
                                  os.environ.get("SZ_USER_AGENT", "Sub-Zero/2"))
            )
        )

        self.token = response['token']
        logger.debug('Logged in with token %r', self.token)

        region.set("os_token", self.token)

    def use_token_or_login(self, func):
        try:
            return func()
        except Unauthorized:
            self.log_in()
            return func()

    def initialize(self):
        logger.info('Logging in')

        token = region.get("os_token", expiration_time=3600)
        if token is not NO_VALUE:
            try:
                checked(self.server.NoOperation(token))
                self.token = token
                logger.info("Using previous login token: %s", self.token)
                return
            except:
                pass

        try:
            self.log_in()

        except Unauthorized:
            if self.is_vip:
                logger.info("VIP server login failed, falling back")
                self.log_in(self.default_url)
                
    def terminate(self):
        if self.server:
            self.server.close()

    def list_subtitles(self, video, languages):
        """
        :param video:
        :param languages:
        :return:

         patch: query movies even if hash is known; add tag parameter
        """

        season = episode = None
        if isinstance(video, Episode):
            query = video.series
            season = video.season
            episode = video.episode

            if video.is_special:
                season = None
                episode = None
                query = u"%s %s" % (video.series, video.title)
                logger.info("%s: Searching for special: %r", self.__class__, query)
        # elif ('opensubtitles' not in video.hashes or not video.size) and not video.imdb_id:
        #    query = video.name.split(os.sep)[-1]
        else:
            query = video.title

        return self.query(languages, hash=video.hashes.get('opensubtitles'), size=video.size, imdb_id=video.imdb_id,
                          query=query, season=season, episode=episode, tag=os.path.basename(video.name),
                          use_tag_search=self.use_tag_search, only_foreign=self.only_foreign)

    def query(self, languages, hash=None, size=None, imdb_id=None, query=None, season=None, episode=None, tag=None,
              use_tag_search=False, only_foreign=False):
        # fill the search criteria
        criteria = []
        if hash and size:
            criteria.append({'moviehash': hash, 'moviebytesize': str(size)})
        if use_tag_search and tag:
            criteria.append({'tag': tag})
        if imdb_id:
            criteria.append({'imdbid': imdb_id[2:]})
        if query and season and episode:
            criteria.append({'query': query.replace('\'', ''), 'season': season, 'episode': episode})
        elif query:
            criteria.append({'query': query.replace('\'', '')})
        if not criteria:
            raise ValueError('Not enough information')

        # add the language
        for criterion in criteria:
            criterion['sublanguageid'] = ','.join(sorted(l.opensubtitles for l in languages))

        # query the server
        logger.info('Searching subtitles %r', criteria)
        response = self.use_token_or_login(
            lambda: self.retry(lambda: checked(self.server.SearchSubtitles(self.token, criteria)))
        )

        subtitles = []

        # exit if no data
        if not response['data']:
            logger.info('No subtitles found')
            return subtitles

        # loop over subtitle items
        for subtitle_item in response['data']:
            # read the item
            language = Language.fromopensubtitles(subtitle_item['SubLanguageID'])
            hearing_impaired = bool(int(subtitle_item['SubHearingImpaired']))
            page_link = subtitle_item['SubtitlesLink']
            subtitle_id = int(subtitle_item['IDSubtitleFile'])
            matched_by = subtitle_item['MatchedBy']
            movie_kind = subtitle_item['MovieKind']
            hash = subtitle_item['MovieHash']
            movie_name = subtitle_item['MovieName']
            movie_release_name = subtitle_item['MovieReleaseName']
            movie_year = int(subtitle_item['MovieYear']) if subtitle_item['MovieYear'] else None
            movie_imdb_id = 'tt' + subtitle_item['IDMovieImdb']
            movie_fps = subtitle_item.get('MovieFPS')
            series_season = int(subtitle_item['SeriesSeason']) if subtitle_item['SeriesSeason'] else None
            series_episode = int(subtitle_item['SeriesEpisode']) if subtitle_item['SeriesEpisode'] else None
            filename = subtitle_item['SubFileName']
            encoding = subtitle_item.get('SubEncoding') or None
            foreign_parts_only = bool(int(subtitle_item.get('SubForeignPartsOnly', 0)))

            # foreign/forced subtitles only wanted
            if only_foreign and not foreign_parts_only:
                continue

            # foreign/forced not wanted
            if not only_foreign and foreign_parts_only:
                continue

            query_parameters = subtitle_item.get("QueryParameters")

            subtitle = self.subtitle_class(language, hearing_impaired, page_link, subtitle_id, matched_by,
                                           movie_kind,
                                           hash, movie_name, movie_release_name, movie_year, movie_imdb_id,
                                           series_season, series_episode, query_parameters, filename, encoding,
                                           movie_fps, skip_wrong_fps=self.skip_wrong_fps)
            logger.debug('Found subtitle %r by %s', subtitle, matched_by)
            subtitles.append(subtitle)

        return subtitles

    def download_subtitle(self, subtitle):
        return self.use_token_or_login(lambda: super(OpenSubtitlesProvider, self).download_subtitle(subtitle))
