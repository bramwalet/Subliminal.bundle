# coding=utf-8
import os
import sys

# just some slight modifications to support sum and iter again
from subzero.sandbox import restore_builtins

module = sys.modules['__main__']
restore_builtins(module, {})

globals = getattr(module, "__builtins__")["globals"]
for key, value in getattr(module, "__builtins__").iteritems():
    if key != "globals":
        globals()[key] = value

import logger
sys.modules["logger"] = logger

from subzero import intent
import subliminal
import subliminal_patch
import support

import interface
sys.modules["interface"] = interface

from subzero.constants import OS_PLEX_USERAGENT, PERSONAL_MEDIA_IDENTIFIER
from subzero import intent
from interface.menu import *
from support.subtitlehelpers import getSubtitlesFromMetadata
from support.storage import storeSubtitleInfo
from support.config import config


def Start():
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = OS_PLEX_USERAGENT

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


def flattenToParts(media, kind="series"):
    """
    iterates through media and returns the associated parts (videos)
    :param media:
    :param kind:
    :return:
    """
    parts = []
    if kind == "series":
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                ep = media.seasons[season].episodes[episode]
                for item in media.seasons[season].episodes[episode].items:
                    for part in item.parts:
                        parts.append({"video": part, "type": "episode", "title": ep.title, "series": media.title, "id": ep.id})
    else:
        for item in media.items:
            for part in item.parts:
                parts.append({"video": part, "type": "movie", "title": media.title, "id": media.id})
    return parts


IGNORE_FN = ("subzero.ignore", ".subzero.ignore", ".nosz")


def parseMediaToParts(media, kind="series"):
    """
    returns a list of parts to be used later on; ignores folders with an existing "subzero.ignore" file
    :param media:
    :param kind:
    :return:
    """
    parts = flattenToParts(media, kind=kind)
    if not Prefs["subtitles.ignore_fs"]:
        return parts

    use_parts = []
    check_ignore_paths = [".", "../"]
    if kind == "series":
        check_ignore_paths.append("../../")

    for part in parts:
        base_folder, fn = os.path.split(part["video"].file)

        ignore = False
        for rel_path in check_ignore_paths:
            fld = os.path.abspath(os.path.join(base_folder, rel_path))
            for ifn in IGNORE_FN:
                if os.path.isfile(os.path.join(fld, ifn)):
                    Log.Info(u'Ignoring "%s" because "%s" exists in "%s"', fn, ifn, fld)
                    ignore = True
                    break
            if ignore:
                break

        if not ignore:
            use_parts.append(part)
    return use_parts


def getFPS(streams):
    for stream in streams:
        # video
        if stream.type == 1:
            return stream.frameRate
    return "25.000"


def scanParts(parts, kind="series"):
    """
    receives a list of parts containing dictionaries returned by flattenToParts
    :param parts:
    :param kind: series or movies
    :return: dictionary of scanned videos of subliminal.video.scan_video
    """
    ret = {}
    for part in parts:
        force_refresh = intent.get("force", part["id"])
        hints = {"expected_title": [part["title"]]}
        hints.update({"type": "episode", "expected_series": [part["series"]]} if kind == "series" else {"type": "movie"})
        part["video"].fps = getFPS(part["video"].streams)
        scanned_video = scanVideo(part["video"], ignore_all=force_refresh, hints=hints)
        if not scanned_video:
            continue

        scanned_video.id = part["id"]
        ret[scanned_video] = part["video"]
    return ret


def getItemIDs(media, kind="series"):
    ids = []
    if kind == "movies":
        ids.append(media.id)
    else:
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                ids.append(media.seasons[season].episodes[episode].id)

    return ids


def scanVideo(part, ignore_all=False, hints=None):
    embedded_subtitles = not ignore_all and Prefs['subtitles.scan.embedded']
    external_subtitles = not ignore_all and Prefs['subtitles.scan.external']

    if ignore_all:
        Log.Debug("Force refresh intended.")

    Log.Debug("Scanning video: %s, subtitles=%s, embedded_subtitles=%s" % (part.file, external_subtitles, embedded_subtitles))

    try:
        return subliminal.video.scan_video(part.file, subtitles=external_subtitles, embedded_subtitles=embedded_subtitles, hints=hints or {},
                                           video_fps=part.fps)

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
    agent_type_verbose = None
    languages = [Locale.Language.English]
    primary_provider = False
    score_prefs_key = None

    def __init__(self, *args, **kwargs):
        super(SubZeroAgent, self).__init__(*args, **kwargs)
        self.agent_type = "movies" if isinstance(self, Agent.Movies) else "series"
        self.name = "Sub-Zero Subtitles (%s, %s)" % (self.agent_type_verbose, config.getVersion())

    def search(self, results, media, lang):
        Log.Debug("Sub-Zero %s, %s search" % (config.version, self.agent_type))
        results.Append(MetadataSearchResult(id='null', score=100))

    def update(self, metadata, media, lang):
        Log.Debug("Sub-Zero %s, %s update called" % (config.version, self.agent_type))

        if not media:
            Log.Error("Called with empty media, something is really wrong with your setup!")
            return

        set_refresh_menu_state(media, media_type=self.agent_type)

        item_ids = []
        try:
            initSubliminalPatches()
            parts = parseMediaToParts(media, kind=self.agent_type)
            use_score = Prefs[self.score_prefs_key]
            scanned_parts = scanParts(parts, kind=self.agent_type)
            subtitles = downloadBestSubtitles(scanned_parts, min_score=int(use_score))
            item_ids = getItemIDs(media, kind=self.agent_type)

            if subtitles:
                saveSubtitles(scanned_parts, subtitles)

            updateLocalMedia(metadata, media, media_type=self.agent_type)

        finally:
            # update the menu state
            set_refresh_menu_state(None)

            # notify any running tasks about our finished update
            for item_id in item_ids:
                scheduler.signal("updated_metadata", item_id)

                # resolve existing intent for that id
                intent.resolve("force", item_id)


class SubZeroSubtitlesAgentMovies(SubZeroAgent, Agent.Movies):
    contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.xbmcnfo', 'com.plexapp.agents.themoviedb', 'com.plexapp.agents.hama']
    score_prefs_key = "subtitles.search.minimumMovieScore"
    agent_type_verbose = "Movies"


class SubZeroSubtitlesAgentTvShows(SubZeroAgent, Agent.TV_Shows):
    contributes_to = ['com.plexapp.agents.thetvdb', 'com.plexapp.agents.thetvdbdvdorder', 'com.plexapp.agents.xbmcnfotv', 'com.plexapp.agents.hama']
    score_prefs_key = "subtitles.search.minimumTVScore"
    agent_type_verbose = "TV"
