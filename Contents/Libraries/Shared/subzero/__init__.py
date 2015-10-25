# coding=utf-8

from plex import Plex

OS_PLEX_USERAGENT = 'plexapp.com v9.0'

DEPENDENCY_MODULE_NAMES = ['subliminal', 'subliminal_patch', 'enzyme', 'guessit', 'requests']
PERSONAL_MEDIA_IDENTIFIER = "com.plexapp.agents.none"
PREFIX = "/video/subzero"

def restart(prefix):
    return Plex[":/plugins"].restart(prefix)

class TempKeyValue(dict):
    
    def __getattr__(self, name):
        if name in self:
            return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]

temp = TempKeyValue()

