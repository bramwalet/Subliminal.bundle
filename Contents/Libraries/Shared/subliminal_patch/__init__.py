# coding=utf-8

from .patch_provider_pool import PatchedProviderPool
from .patch_providers import PatchedAddic7edProvider
from .patch_video import patched_search_external_subtitles
import subliminal
import babelfish

# patch subliminal's ProviderPool 
subliminal.api.ProviderPool = PatchedProviderPool

# patch subliminal's Addic7edProvider
subliminal.providers.addic7ed.Addic7edProvider = PatchedAddic7edProvider

# add language converters
babelfish.language_converters.register('addic7ed = subliminal_patch.patch_language:PatchedAddic7edConverter')
babelfish.language_converters.register('tvsubtitles = subliminal.converters.tvsubtitles:TVsubtitlesConverter')

# patch subliminal's external subtitles search algorithm
subliminal.video.search_external_subtitles = patched_search_external_subtitles