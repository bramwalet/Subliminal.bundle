import sys
# thanks, https://github.com/trakt/Plex-Trakt-Scrobbler/blob/master/Trakttv.bundle/Contents/Code/core/__init__.py

import config

sys.modules["support.config"] = config

import helpers

sys.modules["support.helpers"] = helpers

import lib

sys.modules["support.lib"] = lib

import plex_media
sys.modules["support.plex_media"] = plex_media

import localmedia

sys.modules["subzero.localmedia"] = localmedia

import subtitlehelpers

sys.modules["support.subtitlehelpers"] = subtitlehelpers

import items

sys.modules["support.items"] = items

import missing_subtitles

sys.modules["support.missing_subtitles"] = missing_subtitles

import background

sys.modules["support.background"] = background

import tasks

sys.modules["support.tasks"] = tasks

import storage

sys.modules["support.storage"] = storage

import ignore

sys.modules["support.ignore"] = ignore
