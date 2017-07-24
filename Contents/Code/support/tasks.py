# coding=utf-8

import datetime
import time
import operator
import traceback

from subliminal_patch.score import compute_score
from subliminal_patch.core import download_subtitles
from subliminal import list_subtitles as list_all_subtitles
from babelfish import Language

from missing_subtitles import items_get_all_missing_subs, refresh_item
from scheduler import scheduler
from storage import save_subtitles, get_subtitle_storage
from support.config import config
from support.items import get_recent_items, get_item, is_ignored
from support.helpers import track_usage, get_title_for_video_metadata, cast_bool, PartUnknownException
from support.plex_media import scan_videos, get_plex_metadata
from download import download_best_subtitles


PROVIDER_SLACK = 30
DL_PROVIDER_SLACK = 30


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

    def __init__(self):
        self.name = self.get_class_name()
        self.ready_for_display = False
        self.time_start = None
        self.setup_defaults()

        self.running = False

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
        Log.Info(u"Task: running: %s", self.name)
        self.time_start = datetime.datetime.now()

    def post_run(self, data_holder):
        self.running = False
        self.last_run = datetime.datetime.now()
        if self.time_start and self.last_run:
            self.last_run_time = self.last_run - self.time_start
        self.time_start = None
        Log.Info(u"Task: ran: %s", self.name)


class SubtitleListingMixin(object):
    def list_subtitles(self, rating_key, item_type, part_id, language, skip_wrong_fps=True, metadata=None,
                       scanned_parts=None):

        if not metadata:
            metadata = get_plex_metadata(rating_key, part_id, item_type)

        if not metadata:
            return

        if not scanned_parts:
            scanned_parts = scan_videos([metadata], kind="series" if item_type == "episode" else "movie", ignore_all=True)
            if not scanned_parts:
                Log.Error(u"%s: Couldn't list available subtitles for %s", self.name, rating_key)
                return

        video, plex_part = scanned_parts.items()[0]
        config.init_subliminal_patches()

        provider_settings = config.provider_settings.copy()
        if not skip_wrong_fps:
            provider_settings = config.provider_settings.copy()
            provider_settings["opensubtitles"]["skip_wrong_fps"] = False

        if item_type == "episode":
            min_score = 240
            if video.is_special:
                min_score = 180
        else:
            min_score = 60

        available_subs = list_all_subtitles(scanned_parts, {Language.fromietf(language)},
                                            providers=config.providers,
                                            provider_configs=provider_settings,
                                            pool_class=config.provider_pool)

        use_hearing_impaired = Prefs['subtitles.search.hearingImpaired'] in ("prefer", "force HI")

        # sort subtitles by score
        unsorted_subtitles = []
        for s in available_subs[video]:
            Log.Debug(u"%s: Starting score computation for %s", self.name, s)
            try:
                matches = s.get_matches(video)
            except AttributeError:
                Log.Error(u"%s: Match computation failed for %s: %s", self.name, s, traceback.format_exc())
                continue

            unsorted_subtitles.append(
                (s, compute_score(matches, s, video, hearing_impaired=use_hearing_impaired), matches))
        scored_subtitles = sorted(unsorted_subtitles, key=operator.itemgetter(1), reverse=True)

        subtitles = []
        for subtitle, score, matches in scored_subtitles:
            # check score
            if score < min_score:
                Log.Info(u'%s: Score %d is below min_score (%d)', self.name, score, min_score)
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
        download_subtitles([subtitle], providers=config.providers, provider_configs=config.provider_settings,
                           pool_class=config.provider_pool)
        download_successful = False

        if subtitle.content:
            try:
                save_subtitles(scanned_parts, {video: [subtitle]}, mode=mode, mods=config.default_mods)
                Log.Debug(u"%s: Manually downloaded subtitle for: %s", self.name, rating_key)
                download_successful = True
                refresh_item(rating_key)
                track_usage("Subtitle", "manual", "download", 1)
            except:
                Log.Error(u"%s: Something went wrong when downloading specific subtitle: %s",
                          self.name, traceback.format_exc())
            finally:
                set_refresh_menu_state(None)

                if download_successful:
                    # store item in history
                    from support.history import get_history
                    item_title = get_title_for_video_metadata(metadata, add_section_title=False)
                    history = get_history()
                    history.add(item_title, video.id, section_title=video.plexapi_metadata["section"],
                                subtitle=subtitle,
                                mode=mode)
        else:
            set_refresh_menu_state(u"%s: Subtitle download failed (%s)", self.name, rating_key)
        return download_successful


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
        subs = self.list_subtitles(self.rating_key, self.item_type, self.part_id, self.language, skip_wrong_fps=False)
        if not subs:
            self.data = "found_none"
            return

        # we can't have nasty unpicklable stuff like ZipFile, BytesIO etc in self.data
        self.data = [s.make_picklable() for s in subs]

    def post_run(self, task_data):
        super(AvailableSubsForItem, self).post_run(task_data)
        # clean old data
        for key in task_data.keys():
            if key != self.rating_key:
                del task_data[key]
        task_data.update({self.rating_key: {self.language: self.data}})


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


class SearchAllRecentlyAddedMissing(Task):
    periodic = True

    items_done = None
    items_searching = None
    percentage = 0

    def __init__(self):
        super(SearchAllRecentlyAddedMissing, self).__init__()
        self.items_done = None
        self.items_searching = None
        self.percentage = 0

    def signal_updated_metadata(self, *args, **kwargs):
        return True

    def prepare(self):
        self.items_done = 0
        self.items_searching = 0
        self.percentage = 0
        self.ready_for_display = True

    def run(self):
        super(SearchAllRecentlyAddedMissing, self).run()

        self.running = True
        self.prepare()

        from support.history import get_history
        history = get_history()

        now = datetime.datetime.now()
        min_score_series = int(Prefs["subtitles.search.minimumTVScore2"].strip())
        min_score_movies = int(Prefs["subtitles.search.minimumMovieScore2"].strip())

        is_recent_str = Prefs["scheduler.item_is_recent_age"]
        num, ident = is_recent_str.split()

        max_search_days = 0
        if ident == "days":
            max_search_days = int(num)
        elif ident == "weeks":
            max_search_days = int(num) * 7

        subtitle_storage = get_subtitle_storage()
        recent_sub_fns = subtitle_storage.get_recent_files(age_days=max_search_days)
        viable_items = {}

        # determine viable items
        for fn in recent_sub_fns:
            # added_date <= max_search_days?
            stored_subs = subtitle_storage.load(filename=fn)
            if not stored_subs:
                continue

            if stored_subs.added_at + datetime.timedelta(days=max_search_days) <= now:
                continue

            viable_items[fn] = stored_subs

        subtitle_storage.destroy()

        self.items_searching = len(viable_items)

        download_count = 0
        videos_with_downloads = 0

        config.init_subliminal_patches()

        Log.Info(u"%s: Searching for subtitles for %s items", self.name, self.items_searching)

        # search for subtitles in viable items
        for fn, stored_subs in viable_items.iteritems():
            video_id = stored_subs.video_id

            if stored_subs.item_type == "episode":
                min_score = min_score_series
            else:
                min_score = min_score_movies

            parts = []
            plex_item = get_item(video_id)

            if not plex_item:
                Log.Info(u"%s: Item %s unknown, skipping", self.name, video_id)
                continue

            if is_ignored(video_id, item=plex_item):
                continue

            for media in plex_item.media:
                parts += media.parts

            downloads_per_video = 0
            hit_providers = False
            for part in parts:
                part_id = part.id

                try:
                    metadata = get_plex_metadata(video_id, part_id, stored_subs.item_type)
                except PartUnknownException:
                    Log.Info(u"%s: Part %s:%s unknown, skipping", self.name, video_id, part_id)
                    continue

                if not metadata:
                    Log.Info(u"%s: Part %s:%s unknown, skipping", self.name, video_id, part_id)
                    continue

                Log.Debug(u"%s: Looking for missing subtitles: %s:%s", self.name, video_id, part_id)
                scanned_parts = scan_videos([metadata], kind="series"
                                            if stored_subs.item_type == "episode" else "movie")

                downloaded_subtitles = download_best_subtitles(scanned_parts, min_score=min_score)
                hit_providers = downloaded_subtitles is not None
                download_successful = False

                if downloaded_subtitles:
                    downloaded_any = any(downloaded_subtitles.values())
                    if not downloaded_any:
                        continue

                    try:
                        save_subtitles(scanned_parts, downloaded_subtitles, mode="a", mods=config.default_mods)
                        Log.Debug(u"%s: Downloaded subtitle for item with missing subs: %s", self.name, video_id)
                        download_successful = True
                        refresh_item(video_id)
                        track_usage("Subtitle", "manual", "download", 1)
                    except:
                        Log.Error(u"%s: Something went wrong when downloading specific subtitle: %s", self.name,
                                  traceback.format_exc())
                    finally:
                        item_title = get_title_for_video_metadata(metadata, add_section_title=False)
                        if download_successful:
                            # store item in history
                            for video, video_subtitles in downloaded_subtitles.items():
                                if not video_subtitles:
                                    continue

                                for subtitle in video_subtitles:
                                    downloads_per_video += 1
                                    history.add(item_title, video.id, section_title=metadata["section"],
                                                subtitle=subtitle,
                                                mode="a")

                    Log.Debug(u"%s: Waiting %s seconds before continuing", self.name, PROVIDER_SLACK)
                    time.sleep(PROVIDER_SLACK)

            download_count += downloads_per_video

            if downloads_per_video:
                videos_with_downloads += 1

            self.items_done = self.items_done + 1
            self.percentage = int(self.items_done * 100 / self.items_searching)

            if downloads_per_video:
                Log.Debug(u"%s: Subtitles have been downloaded, "
                          u"waiting %s seconds before continuing", self.name, DL_PROVIDER_SLACK)
                time.sleep(DL_PROVIDER_SLACK)
            else:
                if hit_providers:
                    Log.Debug(u"%s: Waiting %s seconds before continuing", self.name, PROVIDER_SLACK)
                    time.sleep(PROVIDER_SLACK)

        if download_count:
            Log.Debug(u"%s: done. Missing subtitles found for %s/%s items (%s subs downloaded)", self.name,
                      videos_with_downloads, self.items_searching, download_count)
        else:
            Log.Debug(u"%s: done. No subtitles found for %s items", self.name, self.items_searching)

    def post_run(self, task_data):
        super(SearchAllRecentlyAddedMissing, self).post_run(task_data)
        self.ready_for_display = False
        self.percentage = 0
        self.items_done = None
        self.items_searching = None


class FindBetterSubtitles(DownloadSubtitleMixin, SubtitleListingMixin, Task):
    periodic = True

    # TV: episode, format, series, year, season, video_codec, release_group, hearing_impaired, resolution
    series_cutoff = 357

    # movies: format, title, release_group, year, video_codec, resolution, hearing_impaired
    movies_cutoff = 117

    def signal_updated_metadata(self, *args, **kwargs):
        return True

    def run(self):
        super(FindBetterSubtitles, self).run()
        self.running = True
        better_found = 0
        try:
            max_search_days = int(Prefs["scheduler.tasks.FindBetterSubtitles.max_days_after_added"].strip())
        except ValueError:
            Log.Error(u"Please only put numbers into the FindBetterSubtitles.max_days_after_added setting. Exiting")
            return
        else:
            if max_search_days > 30:
                Log.Error(u"%s: FindBetterSubtitles.max_days_after_added is too big. Max is 30 days.", self.name)
                return

        now = datetime.datetime.now()
        min_score_series = int(Prefs["subtitles.search.minimumTVScore2"].strip())
        min_score_movies = int(Prefs["subtitles.search.minimumMovieScore2"].strip())
        overwrite_manually_modified = cast_bool(
            Prefs["scheduler.tasks.FindBetterSubtitles.overwrite_manually_modified"])
        overwrite_manually_selected = cast_bool(
            Prefs["scheduler.tasks.FindBetterSubtitles.overwrite_manually_selected"])

        subtitle_storage = get_subtitle_storage()
        recent_subs = subtitle_storage.load_recent_files(age_days=max_search_days)
        viable_item_count = 0

        for fn, stored_subs in recent_subs.iteritems():
            video_id = stored_subs.video_id

            if stored_subs.item_type == "episode":
                cutoff = self.series_cutoff
                min_score = min_score_series
            else:
                cutoff = self.movies_cutoff
                min_score = min_score_movies

            # don't search for better subtitles until at least 30 minutes have passed
            if stored_subs.added_at + datetime.timedelta(minutes=30) > now:
                Log.Debug(u"%s: Item %s too new, skipping", self.name, video_id)
                continue

            # added_date <= max_search_days?
            if stored_subs.added_at + datetime.timedelta(days=max_search_days) <= now:
                continue

            viable_item_count += 1
            ditch_parts = []

            # look through all stored subtitle data
            for part_id, languages in stored_subs.parts.iteritems():
                part_id = str(part_id)

                # all languages
                for language, current_subs in languages.iteritems():
                    current_key = current_subs.get("current")
                    current = current_subs.get(current_key)

                    # currently got subtitle?
                    if not current:
                        continue
                    current_score = current.score
                    current_mode = current.mode

                    # late cutoff met? skip
                    if current_score >= cutoff:
                        Log.Debug(u"%s: Skipping finding better subs, "
                                  u"cutoff met (current: %s, cutoff: %s): %s (%s)",
                                  self.name, current_score, cutoff, stored_subs.title, video_id)
                        continue

                    # got manual subtitle but don't want to touch those?
                    if current_mode == "m" and not overwrite_manually_selected:
                        Log.Debug(u"%s: Skipping finding better subs, "
                                  u"had manual: %s (%s)", self.name, stored_subs.title, video_id)
                        continue

                    # subtitle modifications different from default
                    if not overwrite_manually_modified and current.mods \
                            and set(current.mods).difference(set(config.default_mods)):
                        Log.Debug(u"%s: Skipping finding better subs, it has manual modifications: %s (%s)",
                                  self.name, stored_subs.title, video_id)
                        continue

                    try:
                        subs = self.list_subtitles(video_id, stored_subs.item_type, part_id, language)
                    except PartUnknownException:
                        Log.Info(u"%s: Part %s unknown/gone; ditching subtitle info", self.name, part_id)
                        ditch_parts.append(part_id)
                        continue

                    hit_providers = subs is not None

                    if subs:
                        # subs are already sorted by score
                        better_downloaded = False
                        better_tried_download = 0
                        better_visited = 0
                        for sub in subs:
                            if sub.score > current_score and sub.score > min_score:
                                Log.Debug(u"%s: Better subtitle found for %s, downloading", self.name, video_id)
                                better_tried_download += 1
                                ret = self.download_subtitle(sub, video_id, mode="b")
                                if ret:
                                    better_found += 1
                                    better_downloaded = True
                                    break
                                else:
                                    Log.Debug(u"%s: Couldn't download/save subtitle. "
                                              u"Continuing to the next one", self.name)
                                    Log.Debug(u"%s: Waiting %s seconds before continuing",
                                              self.name, DL_PROVIDER_SLACK)
                                    time.sleep(DL_PROVIDER_SLACK)
                            better_visited += 1

                        if better_tried_download and not better_downloaded:
                            Log.Debug(u"%s: Tried downloading better subtitle for %s, "
                                      u"but every try failed.", self.name, video_id)

                        elif better_downloaded:
                            Log.Debug(u"%s: Better subtitle downloaded for %s", self.name, video_id)

                        if better_tried_download or better_downloaded:
                            Log.Debug(u"%s: Waiting %s seconds before continuing", self.name, DL_PROVIDER_SLACK)
                            time.sleep(DL_PROVIDER_SLACK)

                        elif better_visited:
                            Log.Debug(u"%s: Waiting %s seconds before continuing", self.name, PROVIDER_SLACK)
                            time.sleep(PROVIDER_SLACK)

                    elif hit_providers:
                        # hit the providers but didn't try downloading? wait.
                        Log.Debug(u"%s: Waiting %s seconds before continuing", self.name, PROVIDER_SLACK)
                        time.sleep(PROVIDER_SLACK)

            if ditch_parts:
                for part_id in ditch_parts:
                    try:
                        del stored_subs.parts[part_id]
                    except KeyError:
                        pass
                subtitle_storage.save(stored_subs)

            time.sleep(1)

        subtitle_storage.destroy()

        if better_found:
            Log.Debug(u"%s: done. Better subtitles found for %s/%s items", self.name, better_found,
                      viable_item_count)
        else:
            Log.Debug(u"%s: done. No better subtitles found for %s items", self.name, viable_item_count)


class SubtitleStorageMaintenance(Task):
    periodic = True
    frequency = "every 7 days"

    def run(self):
        super(SubtitleStorageMaintenance, self).run()
        self.running = True
        Log.Info(u"%s: Running subtitle storage maintenance", self.name)
        storage = get_subtitle_storage()
        deleted_items = storage.delete_missing(wanted_languages=set(str(l) for l in config.lang_list))
        if deleted_items:
            Log.Info(u"%s: Subtitle information for %d non-existant videos have been cleaned up",
                     self.name, len(deleted_items))
            Log.Debug(u"%s: Videos: %s", self.name, deleted_items)
        else:
            Log.Info(u"%s: Nothing to do", self.name)

        storage.destroy()


class MenuHistoryMaintenance(Task):
    periodic = True
    frequency = "every 7 days"

    def run(self):
        super(MenuHistoryMaintenance, self).run()
        self.running = True
        Log.Info(u"%s: Running menu history maintenance", self.name)
        now = datetime.datetime.now()
        if "menu_history" in Dict:
            for key, timeout in Dict["menu_history"].copy().items():
                if now > timeout:
                    try:
                        del Dict["menu_history"][key]
                    except:
                        pass


class MigrateSubtitleStorage(Task):
    periodic = False
    frequency = None

    def run(self):
        super(MigrateSubtitleStorage, self).run()
        self.running = True
        Log.Info(u"%s: Running subtitle storage migration", self.name)
        storage = get_subtitle_storage()
        for fn in storage.get_all_files():
            if fn.endswith(".json.gz"):
                continue
            Log.Debug(u"%s: Migrating %s", self.name, fn)
            storage.load(None, fn)

        storage.destroy()


scheduler.register(SearchAllRecentlyAddedMissing)
scheduler.register(AvailableSubsForItem)
scheduler.register(DownloadSubtitleForItem)
scheduler.register(MissingSubtitles)
scheduler.register(FindBetterSubtitles)
scheduler.register(SubtitleStorageMaintenance)
scheduler.register(MigrateSubtitleStorage)
scheduler.register(MenuHistoryMaintenance)
