# coding=utf-8

import datetime
import time

import operator
import traceback

import subliminal
import subliminal_patch

from subliminal_patch.patch_api import list_all_subtitles, download_subtitles
from babelfish import Language
from subliminal_patch.patch_subtitle import compute_score
from missing_subtitles import items_get_all_missing_subs, refresh_item
from background import scheduler
from storage import save_subtitles, whack_missing_parts
from support.config import config
from support.items import get_recent_items, is_ignored, get_item
from support.lib import Plex
from support.helpers import track_usage, get_title_for_video_metadata, cast_bool
from support.plex_media import scan_videos, get_plex_metadata, PartUnknownException


class Task(object):
    name = None
    scheduler = None
    periodic = False
    running = False
    time_start = None
    data = None

    stored_attributes = ("last_run", "last_run_time", "running")
    default_data = {"last_run": None, "last_run_time": None, "running": False, "data": {}}

    # task ready for being status-displayed?
    ready_for_display = False

    def __init__(self, scheduler):
        self.name = self.get_class_name()
        self.ready_for_display = False
        self.running = False
        self.time_start = None
        self.scheduler = scheduler
        self.setup_defaults()

    def get_class_name(self):
        return getattr(getattr(self, "__class__"), "__name__")

    def __getattribute__(self, name):
        if name in object.__getattribute__(self, "stored_attributes"):
            return Dict["tasks"].get(self.name, {}).get(name, None)

        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name in object.__getattribute__(self, "stored_attributes"):
            Dict["tasks"][self.name][name] = value
            Dict.Save()
            return

        object.__setattr__(self, name, value)

    def setup_defaults(self):
        if self.name not in Dict["tasks"]:
            Dict["tasks"][self.name] = self.default_data.copy()
            return

        sd = Dict["tasks"][self.name]

        # forward-migration
        for key, def_value in self.default_data.iteritems():
            hasval = key in sd
            if not hasval:
                sd[key] = def_value

    def signal(self, *args, **kwargs):
        raise NotImplementedError

    def prepare(self, *args, **kwargs):
        return

    def run(self):
        self.time_start = datetime.datetime.now()

    def post_run(self, data_holder):
        self.running = False
        self.last_run = datetime.datetime.now()
        if self.time_start:
            self.last_run_time = self.last_run - self.time_start
        self.time_start = None


class SearchAllRecentlyAddedMissing(Task):
    periodic = True
    items_done = None
    items_searching = None
    items_searching_ids = None
    items_failed = None
    percentage = 0

    stall_time = 30

    def __init__(self, scheduler):
        super(SearchAllRecentlyAddedMissing, self).__init__(scheduler)
        self.items_done = None
        self.items_searching = None
        self.items_searching_ids = None
        self.items_failed = None
        self.percentage = 0

    def signal(self, signal_name, *args, **kwargs):
        handler = getattr(self, "signal_%s" % signal_name)
        return handler(*args, **kwargs) if handler else None

    def signal_updated_metadata(self, *args, **kwargs):
        item_id = int(args[0])

        if item_id in self.items_searching_ids:
            self.items_done.append(item_id)
            return True

    def prepare(self, *args, **kwargs):
        self.items_done = []
        recent_items = get_recent_items()
        missing = items_get_all_missing_subs(recent_items)
        ids = set([id for added_at, id, title, item, missing_languages in missing if not is_ignored(id, item=item)])
        self.items_searching = missing
        self.items_searching_ids = ids
        self.items_failed = []
        self.percentage = 0
        self.ready_for_display = True

    def run(self):
        super(SearchAllRecentlyAddedMissing, self).run()
        self.running = True
        missing_count = len(self.items_searching)
        items_done_count = 0

        for added_at, item_id, title, item, missing_languages in self.items_searching:
            Log.Debug(u"Task: %s, triggering refresh for %s (%s)", self.name, title, item_id)
            refresh_item(item_id)
            search_started = datetime.datetime.now()
            tries = 1
            while 1:
                if item_id in self.items_done:
                    items_done_count += 1
                    Log.Debug(u"Task: %s, item %s done", self.name, item_id)
                    self.percentage = int(items_done_count * 100 / missing_count)
                    break

                # item considered stalled after self.stall_time seconds passed after last refresh
                if (datetime.datetime.now() - search_started).total_seconds() > self.stall_time:
                    if tries > 3:
                        self.items_failed.append(item_id)
                        Log.Debug(u"Task: %s, item stalled for %s times: %s, skipping", self.name, tries, item_id)
                        break

                    Log.Debug(u"Task: %s, item stalled for %s seconds: %s, retrying", self.name, self.stall_time,
                              item_id)
                    tries += 1
                    refresh_item(item_id)
                    search_started = datetime.datetime.now()
                    time.sleep(1)
                time.sleep(0.1)
            # we can't hammer the PMS, otherwise requests will be stalled
            time.sleep(1)

        Log.Debug("Task: %s, done. Failed items: %s", self.name, self.items_failed)
        self.running = False

    def post_run(self, task_data):
        super(SearchAllRecentlyAddedMissing, self).post_run(task_data)
        self.ready_for_display = False
        self.percentage = 0
        self.items_done = None
        self.items_failed = None
        self.items_searching = None
        self.items_searching_ids = None


class SubtitleListingMixin(object):
    def list_subtitles(self, rating_key, item_type, part_id, language):
        metadata = get_plex_metadata(rating_key, part_id, item_type)

        if item_type == "episode":
            min_score = 66
        else:
            min_score = 23

        scanned_parts = scan_videos([metadata], kind="series" if item_type == "episode" else "movie", ignore_all=True)
        if not scanned_parts:
            Log.Error("Couldn't list available subtitles for %s", rating_key)
            return

        video, plex_part = scanned_parts.items()[0]
        config.init_subliminal_patches()

        available_subs = list_all_subtitles(scanned_parts, {Language.fromietf(language)},
                                            providers=config.providers,
                                            provider_configs=config.provider_settings)

        use_hearing_impaired = Prefs['subtitles.search.hearingImpaired'] in ("prefer", "force HI")

        # sort subtitles by score
        unsorted_subtitles = []
        for s in available_subs[video]:
            Log.Debug("Starting score computation for %s", s)
            try:
                matches = s.get_matches(video, hearing_impaired=use_hearing_impaired)
            except AttributeError:
                Log.Error("Match computation failed for %s: %s", s, traceback.format_exc())
                continue

            unsorted_subtitles.append((s, compute_score(matches, video), matches))
        scored_subtitles = sorted(unsorted_subtitles, key=operator.itemgetter(1), reverse=True)

        subtitles = []
        for subtitle, score, matches in scored_subtitles:
            # check score
            if score < min_score:
                Log.Info('Score %d is below min_score (%d)', score, min_score)
                continue
            subtitle.score = score
            subtitle.matches = matches
            subtitle.part_id = part_id
            subtitle.item_type = item_type
            subtitles.append(subtitle)
        return subtitles


class DownloadSubtitleMixin(object):
    def download_subtitle(self, subtitle, rating_key, mode="m"):
        from interface.menu_helpers import set_refresh_menu_state

        item_type = subtitle.item_type
        part_id = subtitle.part_id
        metadata = get_plex_metadata(rating_key, part_id, item_type)
        scanned_parts = scan_videos([metadata], kind="series" if item_type == "episode" else "movie", ignore_all=True)
        video, plex_part = scanned_parts.items()[0]

        # downloaded_subtitles = {subliminal.Video: [subtitle, subtitle, ...]}
        download_subtitles([subtitle], providers=config.providers, provider_configs=config.provider_settings)

        if subtitle.content:
            try:
                whack_missing_parts(scanned_parts)
                save_subtitles(scanned_parts, {video: [subtitle]}, mode=mode)
                Log.Debug("Manually downloaded subtitle for: %s", rating_key)
                refresh_item(rating_key)
                track_usage("Subtitle", "manual", "download", 1)
            except:
                Log.Error("Something went wrong when downloading specific subtitle: %s", traceback.format_exc())
            finally:
                set_refresh_menu_state(None)

                # store item in history
                from support.history import get_history
                item_title = get_title_for_video_metadata(metadata, add_section_title=False)
                history = get_history()
                history.add(item_title, video.id, section_title=video.plexapi_metadata["section"], subtitle=subtitle,
                            mode=mode)


class AvailableSubsForItem(SubtitleListingMixin, Task):
    item_type = None
    part_id = None
    language = None
    rating_key = None

    def prepare(self, *args, **kwargs):
        self.item_type = kwargs.get("item_type")
        self.part_id = kwargs.get("part_id")
        self.language = kwargs.get("language")
        self.rating_key = kwargs.get("rating_key")

    def setup_defaults(self):
        super(AvailableSubsForItem, self).setup_defaults()

        # reset any previous data
        Dict["tasks"][self.name]["data"] = {}

    def run(self):
        super(AvailableSubsForItem, self).run()
        self.running = True
        track_usage("Subtitle", "manual", "list", 1)
        self.data = self.list_subtitles(self.rating_key, self.item_type, self.part_id, self.language)

    def post_run(self, task_data):
        super(AvailableSubsForItem, self).post_run(task_data)
        if self.rating_key not in task_data:
            task_data[self.rating_key] = {}

        task_data[self.rating_key][self.language] = self.data


class DownloadSubtitleForItem(DownloadSubtitleMixin, Task):
    subtitle = None
    rating_key = None

    def prepare(self, *args, **kwargs):
        self.subtitle = kwargs["subtitle"]
        self.rating_key = kwargs["rating_key"]

    def run(self):
        super(DownloadSubtitleForItem, self).run()
        self.running = True
        self.download_subtitle(self.subtitle, self.rating_key)
        self.running = False


class MissingSubtitles(Task):
    rating_key = None
    item_type = None
    part_id = None
    language = None

    def run(self):
        super(MissingSubtitles, self).run()
        self.running = True
        self.data = []
        recent_items = get_recent_items()
        if recent_items:
            self.data = items_get_all_missing_subs(recent_items)

    def post_run(self, task_data):
        super(MissingSubtitles, self).post_run(task_data)
        task_data["missing_subtitles"] = self.data


class FindBetterSubtitles(DownloadSubtitleMixin, SubtitleListingMixin, Task):
    periodic = True

    # TV: episode, format, series, year, season, video_codec, release_group, hearing_impaired
    series_cutoff = 132

    # movies: format, title, release_group, year, video_codec, resolution, hearing_impaired
    movies_cutoff = 61

    def run(self):
        super(FindBetterSubtitles, self).run()
        self.running = True
        better_found = 0
        try:
            max_search_days = int(Prefs["scheduler.tasks.FindBetterSubtitles.max_days_after_added"].strip())
        except ValueError:
            Log.Error("Please only put numbers into the FindBetterSubtitles.max_days_after_added setting. Exiting")
            return
        else:
            if max_search_days > 30:
                Log.Error("FindBetterSubtitles.max_days_after_added is too big. Max is 30 days.")
                return

        now = datetime.datetime.now()

        for video_id, parts in Dict["subs"].iteritems():
            video_id = str(video_id)
            try:
                plex_item = get_item(video_id)
            except:
                Log.Error("Couldn't get item info for %s", video_id)
                continue
            cutoff = self.series_cutoff if plex_item.type == "episode" else self.movies_cutoff
            added_date = datetime.datetime.fromtimestamp(plex_item.added_at)

            # don't search for better subtitles until at least 30 minutes have passed
            if added_date + datetime.timedelta(minutes=30) > now:
                Log.Debug("Item %s too new, skipping", video_id)
                continue

            # added_date <= max_search_days?
            if added_date + datetime.timedelta(days=max_search_days) <= now:
                continue

            ditch_parts = []

            # look through all stored subtitle data
            for part_id, languages in parts.iteritems():
                part_id = str(part_id)

                # all languages
                for language, current_subs in languages.iteritems():
                    current_key = current_subs.get("current")
                    current = current_subs.get(current_key)

                    # currently got subtitle?
                    if not current:
                        continue
                    current_score = int(current["score"])
                    current_mode = current.get("mode", "a")

                    # late cutoff met? skip
                    if current_score >= cutoff:
                        Log.Debug(u"Skipping finding better subs, cutoff met (current: %s, cutoff: %s): %s",
                                  current_score, cutoff, current["title"])
                        continue

                    # got manual subtitle but don't want to touch those?
                    if current_mode == "m" and \
                            not cast_bool(Prefs["scheduler.tasks.FindBetterSubtitles.overwrite_manually_selected"]):
                        Log.Debug(u"Skipping finding better subs, had manual: %s", current["title"])
                        continue

                    try:
                        subs = self.list_subtitles(video_id, plex_item.type, part_id, language)
                    except PartUnknownException:
                        Log.Info("Part %s unknown/gone; ditching subtitle info", part_id)
                        ditch_parts.append(part_id)
                        continue

                    if subs:
                        # subs are already sorted by score
                        sub = subs[0]
                        if sub.score > current_score:
                            Log.Debug("Better subtitle found for %s, downloading", video_id)
                            self.download_subtitle(sub, video_id, mode="b")
                            better_found += 1

            if ditch_parts:
                for part_id in ditch_parts:
                    try:
                        del parts[part_id]
                    except KeyError:
                        pass

        if better_found:
            Log.Debug("Task: %s, done. Better subtitles found for %s items", self.name, better_found)
        self.running = False


scheduler.register(SearchAllRecentlyAddedMissing)
scheduler.register(AvailableSubsForItem)
scheduler.register(DownloadSubtitleForItem)
scheduler.register(MissingSubtitles)
scheduler.register(FindBetterSubtitles)
