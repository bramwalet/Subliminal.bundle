# coding=utf-8

import subliminal
import babelfish
import logging

from .patch_core import scan_video, search_external_subtitles, PatchedProviderPool, list_all_subtitles
from .patch_score import compute_score
from .patch_extensions import refiner_manager

# patch subliminal's core functions
subliminal.scan_video = subliminal.core.scan_video = scan_video
subliminal.core.search_external_subtitles = search_external_subtitles
subliminal.ProviderPool = subliminal.core.ProviderPool = PatchedProviderPool
subliminal.compute_score = subliminal.score.compute_score = compute_score

# add our own list_all_subtitles
subliminal.list_all_subtitles = subliminal.core.list_all_subtitles = list_all_subtitles
subliminal.refiner_manager = subliminal.core.refiner_manager = refiner_manager
