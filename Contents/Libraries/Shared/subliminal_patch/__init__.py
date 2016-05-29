# coding=utf-8

import subliminal
import babelfish
import logging

# patch subliminal's subtitle encoding detection
from .patch_subtitle import PatchedSubtitle
subliminal.subtitle.Subtitle = PatchedSubtitle
from subliminal.providers.addic7ed import Addic7edSubtitle
from subliminal.providers.podnapisi import PodnapisiSubtitle
from subliminal.providers.tvsubtitles import TVsubtitlesSubtitle
from subliminal.providers.opensubtitles import OpenSubtitlesSubtitle
setattr(Addic7edSubtitle, "__bases__", (PatchedSubtitle,))
setattr(PodnapisiSubtitle, "__bases__", (PatchedSubtitle,))
setattr(TVsubtitlesSubtitle, "__bases__", (PatchedSubtitle,))
setattr(OpenSubtitlesSubtitle, "__bases__", (PatchedSubtitle,))

from .patch_provider_pool import PatchedProviderPool
from .patch_video import patched_search_external_subtitles, scan_video
from .patch_providers import addic7ed, podnapisi, tvsubtitles, opensubtitles
from .patch_api import save_subtitles

# patch subliminal's ProviderPool
subliminal.api.ProviderPool = PatchedProviderPool

# patch subliminal's save_subtitles function
subliminal.api.save_subtitles = save_subtitles

# patch subliminal's subtitle classes
def subtitleRepr(self):
    link = self.page_link

    # specialcasing addic7ed; eww
    if self.__class__.__name__ == "Addic7edSubtitle":
        link = u"http://www.addic7ed.com/%s" % self.download_link
    return '<%s %r [%s]>' % (self.__class__.__name__, link, self.language)


subliminal.subtitle.Subtitle.__repr__ = subtitleRepr

# patch subliminal's providers
subliminal.providers.addic7ed.Addic7edProvider = addic7ed.PatchedAddic7edProvider
subliminal.providers.podnapisi.PodnapisiProvider = podnapisi.PatchedPodnapisiProvider
subliminal.providers.tvsubtitles.TVsubtitlesProvider = tvsubtitles.PatchedTVsubtitlesProvider
subliminal.providers.opensubtitles.OpenSubtitlesProvider = opensubtitles.PatchedOpenSubtitlesProvider

# add language converters
babelfish.language_converters.register('addic7ed = subliminal_patch.patch_language:PatchedAddic7edConverter')
babelfish.language_converters.register('tvsubtitles = subliminal.converters.tvsubtitles:TVsubtitlesConverter')

# patch subliminal's external subtitles search algorithm
subliminal.video.search_external_subtitles = patched_search_external_subtitles

# patch subliminal's scan_video function
subliminal.video.scan_video = scan_video

subliminal.video.Episode.scores["boost"] = 40

subliminal.video.Episode.scores["title"] = 0
