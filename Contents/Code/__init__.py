#hdbits.org

import string, os, urllib, zipfile, re, copy
from babelfish import Language
from datetime import timedelta
import subliminal
import logger

OS_PLEX_USERAGENT = 'plexapp.com v9.0'
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','ssa','aqt','jss','ass','idx']

langPrefs2Podnapisi = {'sq':'29','ar':'12','be':'50','bs':'10','bg':'33','ca':'53','zh':'17','cs':'7','da':'24','nl':'23','en':'2','et':'20','fi':'31','fr':'8','de':'5','el':'16','he':'22','hi':'42','hu':'15','is':'6','id':'54','it':'9','ja':'11','ko':'4','lv':'21','lt':'19','mk':'35','ms':'55','no':'3','pl':'26','pt':'32','ro':'13','ru':'27','sr':'36','sk':'37','sl':'1','es':'28','sv':'25','th':'44','tr':'30','uk':'46','vi':'51','hr':'38'}

mediaCopies = {}

DEPENDENCY_MODULE_NAMES = ['subliminal', 'enzyme', 'guessit', 'requests']

def Start():
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = OS_PLEX_USERAGENT
    Log.Debug("START  CALLED")
    logger.registerLoggingHander(DEPENDENCY_MODULE_NAMES)

def ValidatePrefs():
    Log.Debug("Validate Prefs called.")
    return 

#Prepare a list of languages we want subs for
def getLangList():
    langList = [Prefs["langPref1"]]
    if(Prefs["langPref2"] != "None"):
        langList.append(Prefs["langPref2"])
    return langList

class SubInfo():
    def __init__(self, lang, url, sub, name):
        self.lang = lang
        self.url = url
        self.sub = sub
        self.name = name
        self.ext = string.split(self.name, '.')[-1]

class SubliminalSubtitlesAgentMovies(Agent.Movies):
    name = 'Subliminal Movie Subtitles'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.imdb']

    def search(self, results, media, lang):
        Log.Debug("MOVIE SEARCH CALLED")
        

    def update(self, metadata, media, lang):
        Log.Debug("MOVIE UPDATE CALLED")


class SubliminalSubtitlesAgentTvShows(Agent.TV_Shows):
    
    providers = ['opensubtitles']
    name = 'Subliminal TV Subtitles'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.thetvdb']

    def search(self, results, media, lang):
        Log.Debug("TV SEARCH CALLED")
        results.Append(MetadataSearchResult(id = 'null', score = 100))

        
    def update(self, metadata, media, lang):
        videos= []
        Log.Debug("TvUpdate. Lang %s" % lang)
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                for item in media.seasons[season].episodes[episode].items:
                    for part in item.parts:
                        Log.Debug("Append: %s" % part.file)
                        try:
                            scannedVideo = subliminal.video.scan_video(part.file)
                        except ValueError:
                            Log.Warn("File could not be guessed by subliminal")
                            continue
                        
                        videos.append(scannedVideo)
                     
        result = subliminal.api.list_subtitles(videos,{Language('eng')}, self.providers)
        Log.Debug(result)
        