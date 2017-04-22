# addic7ed
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; ProviderPool(providers=['addic7ed'], provider_configs={'addic7ed': {'use_random_agents': True}})['addic7ed'].query('Game of Thrones', 2)"

# opensubtitles
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; ProviderPool(providers=['opensubtitles'], )['opensubtitles'].query([Language('eng')], query='Game of Thrones', season=2, episode=1, tag='Game.of.Thrones.S06E01.The.Red.Woman.720p.WEB-DL.DD5.1.H.264-NTB.mkv', use_tag_search=True)"

# podnapisi
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; ProviderPool(providers=['podnapisi'], )['podnapisi'].query([Language('eng')], 'Game of Thrones', season=2, episode=1)"

# tvsubtitles
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import subliminal_patch, subliminal; subliminal.region.configure('dogpile.cache.memory'); from subliminal import ProviderPool; from babelfish import Language; ProviderPool(providers=['tvsubtitles'], )['tvsubtitles'].query('Game of Thrones', 2, 1)"