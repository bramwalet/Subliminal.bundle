# coding=utf-8

import subliminal
import babelfish
import logging

from .patch_core import scan_video

# patch subliminal's scan_video function
subliminal.scan_video = subliminal.core.scan_video = scan_video
