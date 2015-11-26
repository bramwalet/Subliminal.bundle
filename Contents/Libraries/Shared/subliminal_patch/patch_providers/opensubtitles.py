# coding=utf-8

import logging
import os

from subliminal.exceptions import ConfigurationError
from subliminal.providers.opensubtitles import OpenSubtitlesProvider, checked, get_version, __version__, Episode, Movie

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

    def list_subtitles(self, video, languages):
        """

        :param video:
        :param languages:
        :return:

         patch: query movies even if hash is known
        """
        query = season = episode = None
        if isinstance(video, Episode):
            query = video.series
            season = video.season
            episode = video.episode
        #elif ('opensubtitles' not in video.hashes or not video.size) and not video.imdb_id:
        #    query = video.name.split(os.sep)[-1]
        else:
            query = video.title

        return self.query(languages, hash=video.hashes.get('opensubtitles'), size=video.size, imdb_id=video.imdb_id,
                          query=query, season=season, episode=episode)