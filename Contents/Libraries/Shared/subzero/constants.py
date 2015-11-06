# coding=utf-8

OS_PLEX_USERAGENT = 'plexapp.com v9.0'

DEPENDENCY_MODULE_NAMES = ['subliminal', 'subliminal_patch', 'enzyme', 'guessit', 'requests']
PERSONAL_MEDIA_IDENTIFIER = "com.plexapp.agents.none"
PLUGIN_IDENTIFIER_SHORT = "subzero"
PLUGIN_IDENTIFIER = "com.plexapp.agents.%s" % PLUGIN_IDENTIFIER_SHORT
PLUGIN_NAME = "Sub-Zero"
PREFIX = "/video/%s" % PLUGIN_IDENTIFIER_SHORT

TITLE = "%s Subtitles" % PLUGIN_NAME
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'
