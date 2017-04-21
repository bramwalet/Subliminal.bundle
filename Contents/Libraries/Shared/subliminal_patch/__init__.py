# coding=utf-8

import subliminal
import babelfish
import logging

# patch subliminal's subtitle and provider base
from .subtitle import PatchedSubtitle
from .providers import PatchedProvider
from .http import RetryingSession
subliminal.subtitle.Subtitle = PatchedSubtitle
subliminal.providers.Provider = PatchedProvider

# inject our requests.Session wrapper for automatic retry
subliminal.providers.addic7ed.Session = RetryingSession
subliminal.providers.podnapisi.Session = RetryingSession
subliminal.providers.tvsubtitles.Session = RetryingSession
subliminal.providers.opensubtitles.Session = RetryingSession

from subliminal.providers.addic7ed import Addic7edSubtitle, Addic7edProvider
from subliminal.providers.podnapisi import PodnapisiSubtitle, PodnapisiProvider
from subliminal.providers.tvsubtitles import TVsubtitlesSubtitle, TVsubtitlesProvider
from subliminal.providers.opensubtitles import OpenSubtitlesSubtitle, OpenSubtitlesProvider

# add our patched base classes
setattr(Addic7edSubtitle, "__bases__", (PatchedSubtitle,))
setattr(PodnapisiSubtitle, "__bases__", (PatchedSubtitle,))
setattr(TVsubtitlesSubtitle, "__bases__", (PatchedSubtitle,))
setattr(OpenSubtitlesSubtitle, "__bases__", (PatchedSubtitle,))
setattr(Addic7edProvider, "__bases__", (PatchedProvider,))
setattr(PodnapisiProvider, "__bases__", (PatchedProvider,))
setattr(TVsubtitlesProvider, "__bases__", (PatchedProvider,))
setattr(OpenSubtitlesProvider, "__bases__", (PatchedProvider,))

from .core import scan_video, search_external_subtitles, PatchedProviderPool, list_all_subtitles, save_subtitles
from .score import compute_score
from .extensions import provider_manager
from .providers import addic7ed#, podnapisi, tvsubtitles, opensubtitles

# patch subliminal's core functions
subliminal.scan_video = subliminal.core.scan_video = scan_video
subliminal.core.search_external_subtitles = search_external_subtitles
subliminal.save_subtitles = subliminal.core.save_subtitles = save_subtitles
subliminal.ProviderPool = subliminal.core.ProviderPool = PatchedProviderPool
subliminal.compute_score = subliminal.score.compute_score = compute_score

# add our own list_all_subtitles
subliminal.list_all_subtitles = subliminal.core.list_all_subtitles = list_all_subtitles
subliminal.provider_manager = subliminal.core.provider_manager = provider_manager

# patch subliminal's subtitle classes
def subtitleRepr(self):
    link = self.page_link

    # specialcasing addic7ed; eww
    if self.__class__.__name__ == "Addic7edSubtitle":
        link = u"http://www.addic7ed.com/%s" % self.download_link
    return '<%s %r [%s]>' % (self.__class__.__name__, link, self.language)


subliminal.subtitle.Subtitle.__repr__ = subtitleRepr


# add language converters
babelfish.language_converters.unregister('addic7ed = subliminal.converters.addic7ed:Addic7edConverter')
babelfish.language_converters.register('addic7ed = subliminal_patch.language:PatchedAddic7edConverter')
subliminal.refiner_manager.register('sz_metadata = subliminal_patch.refiners.metadata:refine')
