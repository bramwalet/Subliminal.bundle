# coding=utf-8
import string
import os
import urllib
import zipfile
import re
import copy
import subliminal
import subliminal_patch
import subzero
import logger

from babelfish import Language
from datetime import timedelta

OS_PLEX_USERAGENT = 'plexapp.com v9.0'

DEPENDENCY_MODULE_NAMES = ['subliminal', 'subliminal_patch', 'enzyme', 'guessit', 'requests']

def Start():
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = OS_PLEX_USERAGENT
    Log.Debug("START CALLED")
    logger.registerLoggingHander(DEPENDENCY_MODULE_NAMES)
    # configured cache to be in memory as per https://github.com/Diaoul/subliminal/issues/303
    subliminal.region.configure('dogpile.cache.memory')

def ValidatePrefs():
    Log.Debug("Validate Prefs called.")
    return 

# Prepare a list of languages we want subs for
def getLangList():
    langList = {Language.fromietf(Prefs["langPref1"])}
    langCustom = Prefs["langPrefCustom"].strip()

    if Prefs["langPref2"] != "None":
        langList.update({Language.fromietf(Prefs["langPref2"])})

    if Prefs["langPref3"] != "None":
        langList.update({Language.fromietf(Prefs["langPref3"])})

    if len(langCustom) and langCustom != "None":
	for lang in langCustom.split(u","):
	    lang = lang.strip()
	    try:
		real_lang = Language.fromietf(lang)
	    except:
		try:
		    real_lang = Language.fromname(lang)
		except:
		    continue
	    langList.update({real_lang})
        
    return langList

def getSubtitleDestinationFolder():
    if not Prefs["subtitles.save.filesystem"]:
	return

    fld_custom = Prefs["subtitles.save.subFolder.Custom"].strip() if bool(Prefs["subtitles.save.subFolder.Custom"]) else None
    return fld_custom or (Prefs["subtitles.save.subFolder"] if Prefs["subtitles.save.subFolder"] != "current folder" else None)

def initSubliminalPatches():
    # configure custom subtitle destination folders for scanning pre-existing subs
    dest_folder = getSubtitleDestinationFolder()
    subliminal_patch.patch_video.CUSTOM_PATHS = [dest_folder] if dest_folder else []
    subliminal_patch.patch_provider_pool.DOWNLOAD_TRIES = int(Prefs['subtitles.try_downloads'])
    subliminal_patch.patch_providers.addic7ed.USE_BOOST = bool(Prefs['provider.addic7ed.boost'])

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
                                      'password': Prefs['provider.addic7ed.password'],
				      'use_random_agents': Prefs['provider.addic7ed.use_random_agents'],
                                      },
			 'opensubtitles': {'username': Prefs['provider.opensubtitles.username'], 
                                      'password': Prefs['provider.opensubtitles.password'],
				      },
                        }

    return provider_settings

def scanTvMedia(media):
    videos = {}
    for season in media.seasons:
        for episode in media.seasons[season].episodes:
            for item in media.seasons[season].episodes[episode].items:
                for part in item.parts:
                    scannedVideo = scanVideo(part, "episode")
                    videos[scannedVideo] = part
    return videos

def scanMovieMedia(media):
    videos = {}
    for item in media.items:
        for part in item.parts:
            scannedVideo = scanVideo(part, "movie")
            videos[scannedVideo] = part 
    return videos

def scanVideo(part, video_type):
    embedded_subtitles = Prefs['subtitles.scan.embedded']
    external_subtitles = Prefs['subtitles.scan.external']
    
    Log.Debug("Scanning video: %s, subtitles=%s, embedded_subtitles=%s" % (part.file, external_subtitles, embedded_subtitles))
    try:
        return subliminal.video.scan_video(part.file, subtitles=external_subtitles, embedded_subtitles=embedded_subtitles, video_type=video_type)
    except ValueError:
        Log.Warn("File could not be guessed by subliminal")

def downloadBestSubtitles(videos, min_score=0):
    hearing_impaired = Prefs['subtitles.search.hearingImpaired']
    languages = getLangList()
    if not languages: 
	return

    missing_languages = False
    for video in videos:
	if not (languages - video.subtitle_languages):
    	    Log.Debug('All languages %r exist for %s', languages, video)
	    continue
	missing_languages = True
	break

    if missing_languages:
	Log.Debug("Download best subtitles using settings: min_score: %s, hearing_impaired: %s" %(min_score, hearing_impaired))
    
	return subliminal.api.download_best_subtitles(videos, languages, min_score, hearing_impaired, providers=getProviders(), provider_configs=getProviderSettings(), only_one=Prefs['subtitles.only_one'])
    Log.Debug("All languages for all requested videos exist. Doing nothing.")

def saveSubtitles(videos, subtitles):
    if Prefs['subtitles.save.filesystem']:
        Log.Debug("Using filesystem as subtitle storage")
        saveSubtitlesToFile(subtitles)
    else:
        Log.Debug("Using metadata as subtitle storage")
        saveSubtitlesToMetadata(videos, subtitles)

def saveSubtitlesToFile(subtitles):
    fld_custom = Prefs["subtitles.save.subFolder.Custom"].strip() if bool(Prefs["subtitles.save.subFolder.Custom"]) else None
    
    for video, video_subtitles in subtitles.items():
	if not video_subtitles:
	    continue

	fld = None
	if fld_custom or Prefs["subtitles.save.subFolder"] != "current folder":
    	    # specific subFolder requested, create it if it doesn't exist
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
        subliminal.api.save_subtitles(video, video_subtitles, directory=fld)

def saveSubtitlesToMetadata(videos, subtitles):
    for video, video_subtitles in subtitles.items():
        mediaPart = videos[video]
        for subtitle in video_subtitles: 
            mediaPart.subtitles[Locale.Language.Match(subtitle.language.alpha2)][subtitle.page_link] = Proxy.Media(subtitle.content, ext="srt")

def updateLocalMedia(media):
    # Look for subtitles
    for item in media.items:
        for part in item.parts:
	    subzero.localmedia.findSubtitles(part)

class SubZeroSubtitlesAgentMovies(Agent.Movies):
    name = 'Sub-Zero Subtitles (Movies)'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.imdb']

    def search(self, results, media, lang):
        Log.Debug("MOVIE SEARCH CALLED")
        results.Append(MetadataSearchResult(id='null', score=100))

    def update(self, metadata, media, lang):
        Log.Debug("MOVIE UPDATE CALLED")
	initSubliminalPatches()
        videos = scanMovieMedia(media)
        subtitles = downloadBestSubtitles(videos.keys(), min_score=int(Prefs["subtitles.search.minimumMovieScore"]))
	if subtitles:
    	    saveSubtitles(videos, subtitles)

	updateLocalMedia(media)

class SubZeroSubtitlesAgentTvShows(Agent.TV_Shows):
    
    name = 'Sub-Zero Subtitles (TV)'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.thetvdb', 'com.plexapp.agents.thetvdbdvdorder']

    def search(self, results, media, lang):
        Log.Debug("TV SEARCH CALLED")
        results.Append(MetadataSearchResult(id='null', score=100))

    def update(self, metadata, media, lang):
        Log.Debug("TvUpdate. Lang %s" % lang)
	initSubliminalPatches()
        videos = scanTvMedia(media)
        subtitles = downloadBestSubtitles(videos.keys(), min_score=int(Prefs["subtitles.search.minimumTVScore"]))
	if subtitles:
    	    saveSubtitles(videos, subtitles)

	updateLocalMedia(media)
