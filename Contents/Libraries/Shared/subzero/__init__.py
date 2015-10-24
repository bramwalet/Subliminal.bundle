# coding=utf-8

from plex import Plex

OS_PLEX_USERAGENT = 'plexapp.com v9.0'

DEPENDENCY_MODULE_NAMES = ['subliminal', 'subliminal_patch', 'enzyme', 'guessit', 'requests']
PERSONAL_MEDIA_IDENTIFIER = "com.plexapp.agents.none"
PREFIX = "/video/subzero"

def restart(prefix):
    return Plex[":/plugins"].restart(prefix)

