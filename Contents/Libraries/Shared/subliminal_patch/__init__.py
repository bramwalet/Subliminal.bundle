# coding=utf-8

import importlib
import subliminal

# patch subliminal's subtitle and provider base
from .subtitle import PatchedSubtitle
from .providers import Provider
from .http import RetryingSession
subliminal.subtitle.Subtitle = PatchedSubtitle

# add our patched base classes
for name in ("Addic7ed", "Podnapisi", "TVsubtitles", "OpenSubtitles", "LegendasTV", "NapiProjekt", "Shooter",
             "SubsCenter"):
    mod = importlib.import_module("subliminal.providers.%s" % name.lower())
    setattr(getattr(mod, "%sSubtitle" % name), "__bases__", (PatchedSubtitle,))
    setattr(getattr(mod, "%sProvider" % name), "__bases__", (Provider,))

    # inject our requests.Session wrapper for automatic retry
    setattr(mod, "Session", RetryingSession)

from .core import scan_video, search_external_subtitles, list_all_subtitles, save_subtitles, refine
from .score import compute_score
from .video import Video

# patch subliminal's core functions
subliminal.scan_video = subliminal.core.scan_video = scan_video
subliminal.core.search_external_subtitles = search_external_subtitles
subliminal.save_subtitles = subliminal.core.save_subtitles = save_subtitles
subliminal.refine = subliminal.core.refine = refine
subliminal.video.Video = subliminal.Video = Video
subliminal.video.Episode.__bases__ = (Video,)
subliminal.video.Movie.__bases__ = (Video,)

# add our own list_all_subtitles
subliminal.list_all_subtitles = subliminal.core.list_all_subtitles = list_all_subtitles
