# coding=utf-8

import subliminal
import babelfish

from .patch_provider_pool import PatchedProviderPool
from .patch_video import patched_search_external_subtitles
from .patch_providers import addic7ed, podnapisi, tvsubtitles


# patch subliminal's ProviderPool 
subliminal.api.ProviderPool = PatchedProviderPool

# patch subliminal's providers
subliminal.providers.addic7ed.Addic7edProvider = addic7ed.PatchedAddic7edProvider
subliminal.providers.podnapisi.PodnapisiProvider = podnapisi.PatchedPodnapisiProvider
subliminal.providers.tvsubtitles.TVsubtitlesProvider = tvsubtitles.PatchedTVsubtitlesProvider

# add language converters
babelfish.language_converters.register('addic7ed = subliminal_patch.patch_language:PatchedAddic7edConverter')
babelfish.language_converters.register('tvsubtitles = subliminal.converters.tvsubtitles:TVsubtitlesConverter')

# patch subliminal's external subtitles search algorithm
subliminal.video.search_external_subtitles = patched_search_external_subtitles

