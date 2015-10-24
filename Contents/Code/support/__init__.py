import sys

# thanks, https://github.com/trakt/Plex-Trakt-Scrobbler/blob/master/Trakttv.bundle/Contents/Code/core/__init__.py

import config
sys.modules["support.config"] = config

import helpers
sys.modules["support.helpers"] = helpers

import localmedia
sys.modules["subzero.localmedia"] = localmedia

import subtitlehelpers
sys.modules["support.subtitlehelpers"] = subtitlehelpers

import recent_items
sys.modules["support.recent_items"] = recent_items

import missing_subtitles
sys.modules["support.missing_subtitles"] = missing_subtitles

import background
sys.modules["support.background"] = background

import storage
sys.modules["support.storage"] = storage