# coding=utf-8

import string
import os
import urllib
import zipfile
import re
import copy
import logger
import datetime
import subliminal
import subliminal_patch
import support
import interface
from subzero.constants import OS_PLEX_USERAGENT, DEPENDENCY_MODULE_NAMES, PERSONAL_MEDIA_IDENTIFIER, PLUGIN_IDENTIFIER_SHORT, \
    PLUGIN_IDENTIFIER, PLUGIN_NAME, PREFIX
from subzero import intent
from support.lib import lib_unaccessible_error
from support.background import scheduler
from interface.menu import fatality as MainMenu, ValidatePrefs
from support.subtitlehelpers import getSubtitlesFromMetadata
from support.storage import storeSubtitleInfo
from support.config import config


def Start():
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = OS_PLEX_USERAGENT
    logger.registerLoggingHander(DEPENDENCY_MODULE_NAMES)
    # configured cache to be in memory as per https://github.com/Diaoul/subliminal/issues/303
    subliminal.region.configure('dogpile.cache.memory')

    # init defaults; perhaps not the best idea to use ValidatePrefs here, but we'll see
    ValidatePrefs()
    Log.Debug(config.full_version)

    if not config.plex_api_working:
        Log.Error(lib_unaccessible_error)
        return

    scheduler.run()


def initSubliminalPatches():
    # configure custom subtitle destination folders for scanning pre-existing subs
    dest_folder = config.subtitleDestinationFolder
    subliminal_patch.patch_video.CUSTOM_PATHS = [dest_folder] if dest_folder else []
    subliminal_patch.patch_provider_pool.DOWNLOAD_TRIES = int(Prefs['subtitles.try_downloads'])
    subliminal_patch.patch_providers.addic7ed.USE_BOOST = bool(Prefs['provider.addic7ed.boost'])


def scanTvMedia(media):
    videos = {}
    for season in media.seasons:
        for episode in media.seasons[season].episodes:
            ep = media.seasons[season].episodes[episode]
            forceRefresh = intent.get("force", ep.id)
            for item in media.seasons[season].episodes[episode].items:
                for part in item.parts:
                    scannedVideo = scanVideo(part, "episode", ignore_all=forceRefresh)
                    videos[scannedVideo] = part
    return videos


def scanMovieMedia(media):
    videos = {}
    forceRefresh = intent.get("force", media.id)
    for item in media.items:
        for part in item.parts:
            scannedVideo = scanVideo(part, "movie", ignore_all=forceRefresh)
            videos[scannedVideo] = part
    return videos


def getItemIDs(media, kind="series"):
    ids = []
    if kind == "movies":
        ids.append(media.id)
    else:
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                ids.append(media.seasons[season].episodes[episode].id)

    return ids


def scanVideo(part, video_type, ignore_all=False):
    embedded_subtitles = not ignore_all and Prefs['subtitles.scan.embedded']
    external_subtitles = not ignore_all and Prefs['subtitles.scan.external']

    if ignore_all:
        Log.Debug("Force refresh intended.")

    Log.Debug("Scanning video: %s, subtitles=%s, embedded_subtitles=%s" % (part.file, external_subtitles, embedded_subtitles))
    try:
        return subliminal.video.scan_video(part.file, subtitles=external_subtitles, embedded_subtitles=embedded_subtitles, video_type=video_type)
    except ValueError:
        Log.Warn("File could not be guessed by subliminal")


def downloadBestSubtitles(video_part_map, min_score=0):
    hearing_impaired = Prefs['subtitles.search.hearingImpaired']
    languages = config.langList
    if not languages:
        return

    missing_languages = False
    for video, part in video_part_map.iteritems():
        if not Prefs['subtitles.save.filesystem']:
            # scan for existing metadata subtitles
            meta_subs = getSubtitlesFromMetadata(part)
            for language, subList in meta_subs.iteritems():
                if subList:
                    video.subtitle_languages.add(language)
                    Log.Debug("Found metadata subtitle %s for %s", language, video)

        if not (languages - video.subtitle_languages):
            Log.Debug('All languages %r exist for %s', languages, video)
            continue
        missing_languages = True
        break

    if missing_languages:
        Log.Debug("Download best subtitles using settings: min_score: %s, hearing_impaired: %s" % (min_score, hearing_impaired))

        return subliminal.api.download_best_subtitles(video_part_map.keys(), languages, min_score, hearing_impaired, providers=config.providers,
                                                      provider_configs=config.providerSettings)
    Log.Debug("All languages for all requested videos exist. Doing nothing.")


def saveSubtitles(videos, subtitles):
    if Prefs['subtitles.save.filesystem']:
        Log.Debug("Using filesystem as subtitle storage")
        saveSubtitlesToFile(subtitles)
        storage = "filesystem"
    else:
        Log.Debug("Using metadata as subtitle storage")
        saveSubtitlesToMetadata(videos, subtitles)
        storage = "metadata"

    storeSubtitleInfo(videos, subtitles, storage)


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


def updateLocalMedia(metadata, media, media_type="movies"):
    # Look for subtitles
    if media_type == "movies":
        for item in media.items:
            for part in item.parts:
                support.localmedia.findSubtitles(part)
        return

    # Look for subtitles for each episode.
    for s in media.seasons:
        # If we've got a date based season, ignore it for now, otherwise it'll collide with S/E folders/XML and PMS
        # prefers date-based (why?)
        if int(s) < 1900 or metadata.guid.startswith(PERSONAL_MEDIA_IDENTIFIER):
            for e in media.seasons[s].episodes:
                for i in media.seasons[s].episodes[e].items:

                    # Look for subtitles.
                    for part in i.parts:
                        support.localmedia.findSubtitles(part)
        else:
            pass


class SubZeroAgent(object):
    agent_type = None
    languages = [Locale.Language.English]
    primary_provider = False

    def __init__(self, *args, **kwargs):
        super(SubZeroAgent, self).__init__(*args, **kwargs)
        self.agent_type = "movies" if isinstance(self, Agent.Movies) else "series"
        self.name = "Sub-Zero Subtitles (%s, %s)" % ("Movies" if self.agent_type == "movies" else "TV", config.getVersion())

    def search(self, results, media, lang):
        Log.Debug("Sub-Zero %s, %s search" % (config.version, self.agent_type))
        results.Append(MetadataSearchResult(id='null', score=100))

    def update(self, metadata, media, lang):
        Log.Debug("Sub-Zero %s, %s update called" % (config.version, self.agent_type))

        item_ids = []
        try:
            initSubliminalPatches()
            videos, subtitles = getattr(self, "update_%s" % self.agent_type)(metadata, media, lang)
            item_ids = getItemIDs(media, kind=self.agent_type)

            if subtitles:
                saveSubtitles(videos, subtitles)

            updateLocalMedia(metadata, media, media_type=self.agent_type)

        finally:
            # notify any running tasks about our finished update
            for item_id in item_ids:
                scheduler.signal("updated_metadata", item_id)

    def update_movies(self, metadata, media, lang):
        videos = scanMovieMedia(media)
        subtitles = downloadBestSubtitles(videos, min_score=int(Prefs["subtitles.search.minimumMovieScore"]))
        return videos, subtitles

    def update_series(self, metadata, media, lang):
        videos = scanTvMedia(media)
        subtitles = downloadBestSubtitles(videos, min_score=int(Prefs["subtitles.search.minimumTVScore"]))
        return videos, subtitles


class SubZeroSubtitlesAgentMovies(SubZeroAgent, Agent.Movies):
    contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.xbmcnfo', 'com.plexapp.agents.themoviedb']


class SubZeroSubtitlesAgentTvShows(SubZeroAgent, Agent.TV_Shows):
    contributes_to = ['com.plexapp.agents.thetvdb', 'com.plexapp.agents.thetvdbdvdorder', 'com.plexapp.agents.xbmcnfotv']
