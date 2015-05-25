# hdbits.org

import string, os, urllib, zipfile, re, copy
from babelfish import Language
from datetime import timedelta
import subliminal
import logger

OS_PLEX_USERAGENT = 'plexapp.com v9.0'

DEPENDENCY_MODULE_NAMES = ['subliminal', 'enzyme', 'guessit', 'requests']

def Start():
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = OS_PLEX_USERAGENT
    Log.Debug("START CALLED")
    logger.registerLoggingHander(DEPENDENCY_MODULE_NAMES)
    # configured cache to be in memory as per https://github.com/Diaoul/subliminal/issues/303
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
    providers = {'opensubtitles' : Prefs['provider.opensubtitles.enabled'],
                 'thesubdb' : Prefs['provider.thesubdb.enabled'],
                 'podnapisi' : Prefs['provider.podnapisi.enabled'],
                 'addic7ed' : Prefs['provider.addic7ed.enabled'],
                 'tvsubtitles' : Prefs['provider.tvsubtitles.enabled']
                 }
    return filter(lambda prov: providers[prov], providers)

def getProviderSettings():
    provider_settings = {'addic7ed': {'username': Prefs['provider.addic7ed.username'], 
                                      'password': Prefs['provider.addic7ed.password']
                                      }
                         }
    return provider_settings

def scanTvMedia(media):
    videos = {}
    for season in media.seasons:
        for episode in media.seasons[season].episodes:
            for item in media.seasons[season].episodes[episode].items:
                for part in item.parts:
                    scannedVideo = scanVideo(part)
                    videos[scannedVideo] = part
    return videos

def scanMovieMedia(media):
    videos = {}
    for item in media.items:
        for part in item.parts:
            scannedVideo = scanVideo(part)
            videos[scannedVideo] = part 
    return videos

def scanVideo(part):
    embedded_subtitles = Prefs['subtitles.scan.embedded']
    external_subtitles = Prefs['subtitles.scan.external']
    
    Log.Debug("Scanning video: %s, subtitles=%s, embedded_subtitles=%s" % (part.file, external_subtitles, embedded_subtitles))
    try:
        return subliminal.video.scan_video(part.file, subtitles=external_subtitles, embedded_subtitles=embedded_subtitles)
    except ValueError:
        Log.Warn("File could not be guessed by subliminal")

def downloadBestSubtitles(videos):
    min_score = int(Prefs['subtitles.search.minimumScore'])
    hearing_impaired = Prefs['subtitles.search.hearingImpaired']
    Log.Debug("Download best subtitles using settings: min_score: %s, hearing_impaired: %s" %(min_score, hearing_impaired))
    return subliminal.api.download_best_subtitles(videos, getLangList(), getProviders(), getProviderSettings(), min_score, hearing_impaired)

def saveSubtitles(videos, subtitles):
    if Prefs['subtitles.save.filesystem']:
        Log.Debug("Saving subtitles to filesystem")
        saveSubtitlesToFile(subtitles)
    else:
        Log.Debug("Saving subtitles as metadata")
        saveSubtitlesToMetadata(videos, subtitles)

def saveSubtitlesToFile(subtitles):
    fld_custom = Prefs["subtitles.save.subFolder.Custom"].strip() if bool(Prefs["subtitles.save.subFolder.Custom"]) else None
    if Prefs["subtitles.save.subFolder"] != "current folder" or fld_custom:
        # specific subFolder requested, create it if it doesn't exist
        for video, video_subtitles in subtitles.items():
            fld_base = os.path.split(video.name)[0]
            if fld_custom:
                if fld_custom.startswith("/"):
                    # absolute folder
                    fld = fld_custom
                else:
                    fld = os.path.join(fld_base, fld_custom)
            else:
                fld = os.path.join(fld_base, Prefs["subtitles.save.subFolder"])
            if not os.path.exists(fld):
                os.makedirs(fld)
            subliminal.api.save_subtitles({video:video_subtitles}, directory=fld)
    
    else:
        subliminal.api.save_subtitles(subtitles)

def saveSubtitlesToMetadata(videos, subtitles):
    for video, video_subtitles in subtitles.items():
        mediaPart = videos[video]
        for subtitle in video_subtitles: 
            mediaPart.subtitles[Locale.Language.Match(subtitle.language.alpha2)][subtitle.page_link] = Proxy.Media(subtitle.content, ext="srt")

class SubliminalSubtitlesAgentMovies(Agent.Movies):
    name = 'Subliminal Movie Subtitles'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.imdb']

    def search(self, results, media, lang):
        Log.Debug("MOVIE SEARCH CALLED")
        results.Append(MetadataSearchResult(id='null', score=100))

    def update(self, metadata, media, lang):
        Log.Debug("MOVIE UPDATE CALLED")
        videos = scanMovieMedia(media)
        subtitles = downloadBestSubtitles(videos.keys())
        saveSubtitles(videos, subtitles)

class SubliminalSubtitlesAgentTvShows(Agent.TV_Shows):
    
    name = 'Subliminal TV Subtitles'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.thetvdb']

    def search(self, results, media, lang):
        Log.Debug("TV SEARCH CALLED")
        results.Append(MetadataSearchResult(id='null', score=100))

    def update(self, metadata, media, lang):
        Log.Debug("TvUpdate. Lang %s" % lang)
        videos = scanTvMedia(media)
        subtitles = downloadBestSubtitles(videos.keys())
        saveSubtitles(videos, subtitles)
