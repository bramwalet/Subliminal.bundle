# addic7ed
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; ProviderPool(providers=['addic7ed'], provider_configs={'addic7ed': {'use_random_agents': True}})['addic7ed'].query('Game of Thrones', 2)"

# opensubtitles
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; ProviderPool(providers=['opensubtitles'], )['opensubtitles'].query([Language('eng')], query='Game of Thrones', season=2, episode=1, tag='Game.of.Thrones.S06E01.The.Red.Woman.720p.WEB-DL.DD5.1.H.264-NTB.mkv', use_tag_search=True)"

# podnapisi
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; ProviderPool(providers=['podnapisi'], )['podnapisi'].query([Language('eng')], 'Game of Thrones', season=2, episode=1)"

# tvsubtitles
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; ProviderPool(providers=['tvsubtitles'], )['tvsubtitles'].query('Game of Thrones', 2, 1)"

# napiprojekt:list
python -c "import logging; logging.basicConfig(level=logging.DEBUG); logging.getLogger('rebulk').setLevel(logging.WARNING); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; from subliminal.core import scan_video; print ProviderPool(providers=['napiprojekt'], )['napiprojekt'].list_subtitles(scan_video('FULL_PATH'), languages=[Language('pol')])"

# napiprojekt:download
python -c "import logging; logging.basicConfig(level=logging.DEBUG); logging.getLogger('rebulk').setLevel(logging.WARNING); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal_patch.core import PatchedProviderPool; from subliminal import download_best_subtitles; from babelfish import Language; from subliminal.core import scan_video; subs = download_best_subtitles([scan_video('FULL_PATH')], languages={Language('eng')}, providers=['napiprojekt'], ); print subs.values()[0][0].is_valid()"


# shooter:list
python -c "import logging; logging.basicConfig(level=logging.DEBUG); logging.getLogger('rebulk').setLevel(logging.WARNING); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; from subliminal.core import scan_video; print ProviderPool(providers=['shooter'], )['shooter'].list_subtitles(scan_video('FULL_PATH'), languages=[Language('zho')])"

# subscenter:list
python -c "import logging; logging.basicConfig(level=logging.DEBUG); logging.getLogger('rebulk').setLevel(logging.WARNING); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; from subliminal.core import scan_video; print ProviderPool(providers=['subscenter'], )['subscenter'].list_subtitles(scan_video('FULL_PATH'), languages=[Language('heb')])"


# refining
python -c "import logging; logging.basicConfig(level=logging.DEBUG); logging.getLogger('rebulk').setLevel(logging.WARNING); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subzero.video import parse_video; print parse_video('FILE_NAME', hints={'type': 'episode'}, dry_run=True)"