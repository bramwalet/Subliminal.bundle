# coding=utf-8

import logging
import os

from babelfish import Language
from subliminal.exceptions import ConfigurationError
from subliminal.providers.opensubtitles import OpenSubtitlesProvider, checked, get_version, __version__, OpenSubtitlesSubtitle, Episode

logger = logging.getLogger(__name__)


class PatchedOpenSubtitlesSubtitle(OpenSubtitlesSubtitle):
    def __init__(self, language, hearing_impaired, page_link, subtitle_id, matched_by, movie_kind, hash, movie_name,
                 movie_release_name, movie_year, movie_imdb_id, series_season, series_episode, query_parameters, fps):
        super(PatchedOpenSubtitlesSubtitle, self).__init__(language, hearing_impaired, page_link, subtitle_id, matched_by, movie_kind, hash,
                                                           movie_name,
                                                           movie_release_name, movie_year, movie_imdb_id, series_season, series_episode)
        self.query_parameters = query_parameters or {}
        self.fps = fps

    def get_matches(self, video, hearing_impaired=False):
        matches = super(PatchedOpenSubtitlesSubtitle, self).get_matches(video, hearing_impaired=hearing_impaired)

        sub_fps = None
        try:
            sub_fps = float(self.fps)
        except ValueError:
            pass

        # video has fps info, sub also, and sub's fps is greater than 0
        if video.fps and sub_fps and (video.fps != self.fps):
            logger.debug("Wrong FPS (expected: %s, got: %s, lowering score massively)", video.fps, self.fps)
            # fixme: may be too harsh
            return set()

        # matched by tag?
        if self.matched_by == "tag":
            # treat a tag match equally to a hash match
            logger.debug("Subtitle matched by tag, treating it as a hash-match. Tag: '%s'", self.query_parameters.get("tag", None))
            matches.add("hash")
        return matches


class PatchedOpenSubtitlesProvider(OpenSubtitlesProvider):
    def __init__(self, username=None, password=None, use_tag_search=False):
        if username is not None and password is None or username is None and password is not None:
            raise ConfigurationError('Username and password must be specified')

        self.username = username or ''
        self.password = password or ''
        self.use_tag_search = use_tag_search

        if use_tag_search:
            logger.info("Using tag/exact filename search")

        super(PatchedOpenSubtitlesProvider, self).__init__()

    def initialize(self):
        logger.info('Logging in')
        response = checked(self.server.LogIn(self.username, self.password, 'eng', 'subliminal v%s' % get_version(__version__)))
        self.token = response['token']
        logger.debug('Logged in with token %r', self.token)

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
        # elif ('opensubtitles' not in video.hashes or not video.size) and not video.imdb_id:
        #    query = video.name.split(os.sep)[-1]
        else:
            query = video.title

        return self.query(languages, hash=video.hashes.get('opensubtitles'), size=video.size, imdb_id=video.imdb_id,
                          query=query, season=season, episode=episode, tag=os.path.basename(video.name), use_tag_search=self.use_tag_search)

    def query(self, languages, hash=None, size=None, imdb_id=None, query=None, season=None, episode=None, tag=None, use_tag_search=False):
        # fill the search criteria
        criteria = []
        if hash and size:
            criteria.append({'moviehash': hash, 'moviebytesize': str(size)})
        if use_tag_search and tag:
            criteria.append({'tag': tag})
        if imdb_id:
            criteria.append({'imdbid': imdb_id})
        if query and season and episode:
            criteria.append({'query': query, 'season': season, 'episode': episode})
        elif query:
            criteria.append({'query': query})
        if not criteria:
            raise ValueError('Not enough information')

        # add the language
        for criterion in criteria:
            criterion['sublanguageid'] = ','.join(sorted(l.opensubtitles for l in languages))

        # query the server
        logger.info('Searching subtitles %r', criteria)
        response = checked(self.server.SearchSubtitles(self.token, criteria))
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
            movie_imdb_id = int(subtitle_item['IDMovieImdb'])
            movie_fps = subtitle_item.get('MovieFPS')
            series_season = int(subtitle_item['SeriesSeason']) if subtitle_item['SeriesSeason'] else None
            series_episode = int(subtitle_item['SeriesEpisode']) if subtitle_item['SeriesEpisode'] else None
            query_parameters = subtitle_item.get("QueryParameters")

            subtitle = PatchedOpenSubtitlesSubtitle(language, hearing_impaired, page_link, subtitle_id, matched_by, movie_kind,
                                                    hash, movie_name, movie_release_name, movie_year, movie_imdb_id,
                                                    series_season, series_episode, query_parameters, fps=movie_fps)
            logger.debug('Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        return subtitles
