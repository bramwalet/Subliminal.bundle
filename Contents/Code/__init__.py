# hdbits.org

import string, os, urllib, zipfile, re, copy
from babelfish import Language
from datetime import timedelta
import subliminal
import logger

OS_PLEX_USERAGENT = 'plexapp.com v9.0'

DEPENDENCY_MODULE_NAMES = ['subliminal', 'enzyme', 'guessit', 'requests']

SUPPORTED_PROVIDERS = ['opensubtitles', 'thesubdb', 'podnapisi', 'addic7ed', 'tvsubtitles']

ENABLED_PROVIDERS = {'opensubtitles' : Prefs['provider.opensubtitles'],
                     'thesubdb' : Prefs['provider.thesubdb'],
                     'podnapisi' : Prefs['provider.podnapisi'],
                     'addic7ed' : Prefs['provider.addic7ed'],
                     'tvsubtitles' : Prefs['provider.tvsubtitles']
                     }
# dict((key,value) for key, value in a.iteritems() if key == 1)
SUPPORTED_PROVIDER_SETTINGS = {'addic7ed': { 
                                            'username': Prefs['provider.addic7ed.username'], 
                                            'password': Prefs['provider.addic7ed.password']
                                            }
                               }

def Start():
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = OS_PLEX_USERAGENT
    Log.Debug("START CALLED")
    logger.registerLoggingHander(DEPENDENCY_MODULE_NAMES)
    subliminal.cache_region.configure('dogpile.cache.memory')

def ValidatePrefs():
    Log.Debug("Validate Prefs called.")
    return 

# Prepare a list of languages we want subs for
def getLangList():
    langList = {Language.fromietf(Prefs["langPref1"])}
    if(Prefs["langPref2"] != "None"):
        langList.update({Language.fromietf(Prefs["langPref2"])})
        
    return langList

def getProviders():
    enabledProviders = []
    for supportedProvider in SUPPORTED_PROVIDERS:
        if Prefs["provider." + supportedProvider]:
            Log.Debug("Provider %s is enabled" % supportedProvider)
            enabledProviders.append(supportedProvider)
    return enabledProviders

def getProviderSettings():
    return SUPPORTED_PROVIDER_SETTINGS

class SubliminalSubtitlesAgentMovies(Agent.Movies):
    name = 'Subliminal Movie Subtitles'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.imdb']

    def search(self, results, media, lang):
        Log.Debug("MOVIE SEARCH CALLED")
        results.Append(MetadataSearchResult(id='null', score=100))


    def update(self, metadata, media, lang):
        videos = []
        Log.Debug("MOVIE UPDATE CALLED")
        for item in media.items:
            for part in item.parts:
                Log.Debug("Append: %s" % part.file)
                try:
                    scannedVideo = subliminal.video.scan_video(part.file, subtitles=True, embedded_subtitles=True)
                except ValueError:
                    Log.Warn("File could not be guessed by subliminal")
                    continue
                
                videos.append(scannedVideo)

        subtitles = subliminal.api.download_best_subtitles(videos, getLangList(), getProviders(), getProviderSettings())
        subliminal.api.save_subtitles(subtitles)

class SubliminalSubtitlesAgentTvShows(Agent.TV_Shows):
    
    name = 'Subliminal TV Subtitles'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.thetvdb']

    def search(self, results, media, lang):
        Log.Debug("TV SEARCH CALLED")
        results.Append(MetadataSearchResult(id='null', score=100))
        
    def update(self, metadata, media, lang):
        videos = []
        Log.Debug("TvUpdate. Lang %s" % lang)
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                for item in media.seasons[season].episodes[episode].items:
                    for part in item.parts:
                        Log.Debug("Append: %s" % part.file)
                        try:
                            scannedVideo = subliminal.video.scan_video(part.file, subtitles=True, embedded_subtitles=True)
                        except ValueError:
                            Log.Warn("File could not be guessed by subliminal")
                            continue
                        
                        videos.append(scannedVideo)

        subtitles = subliminal.api.download_best_subtitles(videos, getLangList(), getProviders(), getProviderSettings())
        subliminal.api.save_subtitles(subtitles)
