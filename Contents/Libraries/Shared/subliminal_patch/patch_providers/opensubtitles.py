# coding=utf-8

import logging

from subliminal.exceptions import ConfigurationError
from subliminal.providers.opensubtitles import OpenSubtitlesProvider, checked, get_version, __version__, OpenSubtitlesSubtitle

logger = logging.getLogger(__name__)


class PatchedOpenSubtitlesProvider(OpenSubtitlesProvider):
    def __init__(self, username=None, password=None):
        if username is not None and password is None or username is None and password is not None:
            raise ConfigurationError('Username and password must be specified')

        self.username = username or ''
        self.password = password or ''

        super(PatchedOpenSubtitlesProvider, self).__init__()

    def initialize(self):
        logger.info('Logging in')
        response = checked(self.server.LogIn(self.username, self.password, 'eng', 'subliminal v%s' % get_version(__version__)))
        self.token = response['token']
        logger.debug('Logged in with token %r', self.token)

    def query(self, languages, hash=None, size=None, imdb_id=None, query=None, season=None, episode=None, tag=None):
        # fill the search criteria
        criteria = []
        if hash and size:
            criteria.append({'moviehash': hash, 'moviebytesize': str(size)})
        if imdb_id:
            criteria.append({'imdbid': imdb_id})
        if tag:
            criteria.append({'tag': tag})
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
            series_season = int(subtitle_item['SeriesSeason']) if subtitle_item['SeriesSeason'] else None
            series_episode = int(subtitle_item['SeriesEpisode']) if subtitle_item['SeriesEpisode'] else None

            subtitle = OpenSubtitlesSubtitle(language, hearing_impaired, page_link, subtitle_id, matched_by, movie_kind,
                                             hash, movie_name, movie_release_name, movie_year, movie_imdb_id,
                                             series_season, series_episode)
            logger.debug('Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        return subtitles