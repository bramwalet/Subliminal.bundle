# coding=utf-8

import logging, sys

logging.basicConfig(level=logging.DEBUG)

import subliminal_patch
import subliminal

subliminal.region.configure('dogpile.cache.memory')
from subliminal.video import scan_video

from subliminal.subtitle import compute_score
from babelfish import Language
from subliminal.api import download_best_subtitles

v = scan_video('Series/Midsomer Murders/S4/Midsomer.Murders.S04E02.Destroying_Angel.avi', dont_use_actual_file=True)

#pool = ProviderPool()
#subs = pool.list_subtitles(v, set([Language.fromietf('nl')]))

#[pool.download_subtitle(sub) for sub in subs];"

download_best_subtitles([v], set([Language.fromietf('nl')]), providers=["opensubtitles"])