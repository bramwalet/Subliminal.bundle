import sys

# thanks, https://github.com/trakt/Plex-Trakt-Scrobbler/blob/master/Trakttv.bundle/Contents/Code/core/__init__.py

import config
sys.modules["subzero.config"] = config

import helpers
sys.modules["subzero.helpers"] = helpers

import localmedia
sys.modules["subzero.localmedia"] = localmedia

import subtitlehelpers
sys.modules["subzero.subtitlehelpers"] = subtitlehelpers

