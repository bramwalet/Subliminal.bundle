# coding=utf-8
import sys
import datetime

from subzero.sandbox import restore_builtins

module = sys.modules['__main__']
restore_builtins(module, {})

globals = getattr(module, "__builtins__")["globals"]
for key, value in getattr(module, "__builtins__").iteritems():
    if key != "globals":
        globals()[key] = value

import logger

sys.modules["logger"] = logger

import support

import interface
sys.modules["interface"] = interface

from subzero.constants import OS_PLEX_USERAGENT, PERSONAL_MEDIA_IDENTIFIER
from interface.menu import *
from support.plex_media import media_to_videos, get_media_item_ids
from support.scanning import scan_videos
from support.storage import save_subtitles, store_subtitle_info, get_subtitle_storage
from support.items import is_ignored
from support.config import config
from support.lib import get_intent
from support.helpers import track_usage, get_title_for_video_metadata, get_identifier, cast_bool
from support.history import get_history
from support.data import dispatch_migrate
from support.activities import activity
from support.download import download_best_subtitles


def Start():
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = OS_PLEX_USERAGENT

    config.init_cache()

    # clear expired intents
    intent = get_intent()
    intent.cleanup()

    # clear expired menu history items
    now = datetime.datetime.now()
    if "menu_history" in Dict:
        for key, timeout in Dict["menu_history"].copy().items():
            if now > timeout:
                try:
                    del Dict["menu_history"][key]
                except:
                    pass

    # run migrations
    if "subs" in Dict or "history" in Dict:
        Thread.Create(dispatch_migrate)

    # clear old task data
    scheduler.clear_task_data()

    # init defaults; perhaps not the best idea to use ValidatePrefs here, but we'll see
    ValidatePrefs()
    Log.Debug(config.full_version)

    if not config.permissions_ok:
        Log.Error("Insufficient permissions on library folders:")
        for title, path in config.missing_permissions:
            Log.Error("Insufficient permissions on library %s, folder: %s" % (title, path))

    # run task scheduler
    scheduler.run()

    # bind activities
    if config.enable_channel:
        Thread.Create(activity.start)

    if "anon_id" not in Dict:
        Dict["anon_id"] = get_identifier()

    # track usage
    if cast_bool(Prefs["track_usage"]):
        if "first_use" not in Dict:
            Dict["first_use"] = datetime.datetime.utcnow()
            Dict.Save()
            track_usage("General", "plugin", "first_start", config.version)
        track_usage("General", "plugin", "start", config.version)


def update_local_media(metadata, media, media_type="movies"):
    # Look for subtitles
    if media_type == "movies":
        for item in media.items:
            for part in item.parts:
                support.localmedia.find_subtitles(part)
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
                        support.localmedia.find_subtitles(part)
        else:
            pass


def agent_extract_embedded(videos):
    try:
        subtitle_storage = get_subtitle_storage()

        for video in videos:
            item = video["item"]
            stored_subs = subtitle_storage.load_or_new(item)

            for part in get_all_parts(item):
                for requested_language in config.lang_list:
                    embedded_subs = stored_subs.get_by_provider(part.id, requested_language, "embedded")
                    current = stored_subs.get_any(part.id, requested_language)
                    if not embedded_subs:
                        stream_data = get_embedded_subtitle_streams(part, requested_language=requested_language,
                                                                    get_forced=config.forced_only)

                        if stream_data:
                            stream = stream_data[0]["stream"]

                            extract_embedded_sub(rating_key=item.rating_key, part_id=part.id,
                                                 stream_index=str(stream.index),
                                                 language=str(requested_language), with_mods=True, refresh=False,
                                                 set_current=not current)
                    else:
                        Log.Debug("Skipping embedded subtitle extraction for %s, already got %r from %s",
                                  item.rating_key, requested_language, embedded_subs[0].id)
    except:
        Log.Error("Something went wrong when auto-extracting subtitles, continuing: %s", traceback.format_exc())


class SubZeroAgent(object):
    agent_type = None
    agent_type_verbose = None
    languages = [Locale.Language.English]
    primary_provider = False
    score_prefs_key = None
    debounce = 10

    def __init__(self, *args, **kwargs):
        super(SubZeroAgent, self).__init__(*args, **kwargs)
        self.agent_type = "movies" if isinstance(self, Agent.Movies) else "series"
        self.name = "Sub-Zero Subtitles (%s, %s)" % (self.agent_type_verbose, config.get_version())

    def search(self, results, media, lang):
        Log.Debug("Sub-Zero %s, %s search" % (config.version, self.agent_type))
        results.Append(MetadataSearchResult(id='null', score=100))

    def store_blank_subtitle_metadata(self, video_part_map):
        store_subtitle_info(video_part_map, dict((k, []) for k in video_part_map.keys()), None, mode="a")

    def update(self, metadata, media, lang):
        if not config.enable_agent:
            Log.Debug("Skipping Sub-Zero agent(s)")
            return

        Log.Debug("Sub-Zero %s, %s update called" % (config.version, self.agent_type))
        intent = get_intent()

        if not media:
            Log.Error("Called with empty media, something is really wrong with your setup!")
            return

        item_ids = []
        try:
            config.init_subliminal_patches()
            videos = media_to_videos(media, kind=self.agent_type)

            # find local media
            update_local_media(metadata, media, media_type=self.agent_type)

            # media ignored?
            use_any_parts = False
            for video in videos:
                if is_ignored(video["id"]):
                    Log.Debug(u"Ignoring %s" % video)
                    continue
                use_any_parts = True

            if not use_any_parts:
                Log.Debug(u"Nothing to do.")
                return

            try:
                use_score = int(Prefs[self.score_prefs_key].strip())
            except ValueError:
                Log.Error("Please only put numbers into the scores setting. Exiting")
                return

            set_refresh_menu_state(media, media_type=self.agent_type)

            # scanned_video_part_map = {subliminal.Video: plex_part, ...}
            providers = config.get_providers(media_type=self.agent_type)
            scanned_video_part_map = scan_videos(videos, providers=providers)

            # auto extract embedded
            if config.embedded_auto_extract:
                agent_extract_embedded(videos)

            # clear missing subtitles menu data
            if not scheduler.is_task_running("MissingSubtitles"):
                scheduler.clear_task_data("MissingSubtitles")

            downloaded_subtitles = None

            # debounce for self.debounce seconds
            now = datetime.datetime.now()
            if "last_call" in Dict:
                last_call = Dict["last_call"]
                if last_call + datetime.timedelta(seconds=self.debounce) > now:
                    wait = self.debounce - (now - last_call).seconds
                    if wait >= 1:
                        Log.Debug("Waiting %s seconds until continuing", wait)
                        Thread.Sleep(wait)

            # downloaded_subtitles = {subliminal.Video: [subtitle, subtitle, ...]}
            try:
                downloaded_subtitles = download_best_subtitles(scanned_video_part_map, min_score=use_score,
                                                               throttle_time=self.debounce, providers=providers)
            except:
                Log.Exception("Something went wrong when downloading subtitles")

            if downloaded_subtitles is not None:
                Dict["last_call"] = datetime.datetime.now()

            item_ids = get_media_item_ids(media, kind=self.agent_type)

            downloaded_any = False
            if downloaded_subtitles:
                downloaded_any = any(downloaded_subtitles.values())

            if downloaded_any:
                save_successful = False
                try:
                    save_successful = save_subtitles(scanned_video_part_map, downloaded_subtitles,
                                                     mods=config.default_mods)
                except:
                    Log.Exception("Something went wrong when saving subtitles")

                track_usage("Subtitle", "refreshed", "download", 1)

                # store SZ meta info even if download wasn't successful
                if not save_successful:
                    self.store_blank_subtitle_metadata(scanned_video_part_map)

                else:
                    for video, video_subtitles in downloaded_subtitles.items():
                        # store item(s) in history
                        for subtitle in video_subtitles:
                            item_title = get_title_for_video_metadata(video.plexapi_metadata, add_section_title=False)
                            history = get_history()
                            history.add(item_title, video.id, section_title=video.plexapi_metadata["section"],
                                        subtitle=subtitle)
                            history.destroy()
            else:
                # store SZ meta info even if we've downloaded none
                self.store_blank_subtitle_metadata(scanned_video_part_map)

            update_local_media(metadata, media, media_type=self.agent_type)

        finally:
            # update the menu state
            set_refresh_menu_state(None)

            # notify any running tasks about our finished update
            for item_id in item_ids:
                #scheduler.signal("updated_metadata", item_id)

                # resolve existing intent for that id
                intent.resolve("force", item_id)

            Dict.Save()

            # fsync cache
            if config.new_style_cache:
                config.sync_cache()


class SubZeroSubtitlesAgentMovies(SubZeroAgent, Agent.Movies):
    contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.xbmcnfo', 'com.plexapp.agents.themoviedb', 'com.plexapp.agents.hama']
    score_prefs_key = "subtitles.search.minimumMovieScore2"
    agent_type_verbose = "Movies"


class SubZeroSubtitlesAgentTvShows(SubZeroAgent, Agent.TV_Shows):
    contributes_to = ['com.plexapp.agents.thetvdb', 'com.plexapp.agents.themoviedb',
                      'com.plexapp.agents.thetvdbdvdorder', 'com.plexapp.agents.xbmcnfotv', 'com.plexapp.agents.hama']
    score_prefs_key = "subtitles.search.minimumTVScore2"
    agent_type_verbose = "TV"
