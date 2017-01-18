# coding=utf-8

import subliminal
import babelfish
import logging

from .patch_core import scan_video, search_external_subtitles

# patch subliminal's core functions
subliminal.scan_video = subliminal.core.scan_video = scan_video
subliminal.core.search_external_subtitles = search_external_subtitles

