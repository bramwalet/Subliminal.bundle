# coding=utf-8

import logging
from subliminal.providers.opensubtitles import OpenSubtitlesProvider, checked, get_version, __version__

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