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
from storage import save_subtitles
from support.config import config
from support.items import get_recent_items, is_ignored
from support.lib import Plex
from support.plex_media import scan_videos, get_metadata_dict


class Task(object):
    name = None
    scheduler = None
    periodic = False
    running = False
    time_start = None
    data = None

    stored_attributes = ("last_run", "last_run_time")

    # task ready for being status-displayed?
    ready_for_display = False

    def __init__(self, scheduler):
        self.ready_for_display = False
        self.running = False
        self.time_start = None
        self.scheduler = scheduler
        if self.name not in Dict["tasks"]:
            Dict["tasks"][self.name] = {"last_run": None, "last_run_time": None}

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

    def signal(self, *args, **kwargs):
        raise NotImplementedError

    def prepare(self, *args, **kwargs):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class SearchAllRecentlyAddedMissing(Task):
    name = "searchAllRecentlyAddedMissing"
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
        ids = set([id for added_at, id, title, item in missing if not is_ignored(id, item=item)])
        self.items_searching = missing
        self.items_searching_ids = ids
        self.items_failed = []
        self.percentage = 0
        self.time_start = datetime.datetime.now()
        self.ready_for_display = True

    def run(self):
        self.running = True
        missing_count = len(self.items_searching)
        items_done_count = 0

        for added_at, item_id, title, item in self.items_searching:
            Log.Debug(u"Task: %s, triggering refresh for %s (%s)", self.name, title, item_id)
            refresh_item(item_id, title)
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
                    refresh_item(item_id, title)
                    search_started = datetime.datetime.now()
                    time.sleep(1)
                time.sleep(0.1)
            # we can't hammer the PMS, otherwise requests will be stalled
            time.sleep(1)

        Log.Debug("Task: %s, done. Failed items: %s", self.name, self.items_failed)
        self.running = False

    def post_run(self, task_data):
        self.ready_for_display = False
        self.last_run = datetime.datetime.now()
        if self.time_start:
            self.last_run_time = self.last_run - self.time_start
        self.time_start = None
        self.percentage = 0
        self.items_done = None
        self.items_failed = None
        self.items_searching = None
        self.items_searching_ids = None


class PlexItemMetadataMixin(object):
    def get_plex_metadata(self):
        rating_key = self.rating_key
        plex_item = list(Plex["library"].metadata(rating_key))[0]
        part_id = self.part_id
        item_type = self.item_type

        # find current part
        current_part = None
        for part in plex_item.media.parts:
            if str(part.id) == part_id:
                current_part = part

        if not current_part:
            raise ValueError("Part unknown")

        # get normalized metadata
        if item_type == "episode":
            metadata = get_metadata_dict(plex_item, current_part,
                                         {"plex_part": current_part, "type": "episode", "title": plex_item.title,
                                          "series": plex_item.show.title, "id": plex_item.rating_key,
                                          "series_id": plex_item.show.rating_key,
                                          "season_id": plex_item.season.rating_key,
                                          "season": plex_item.season.index,
                                          })
        else:
            metadata = get_metadata_dict(plex_item, current_part, {"plex_part": current_part, "type": "movie",
                                                                   "title": plex_item.title, "id": plex_item.rating_key,
                                                                   "series_id": None,
                                                                   "season_id": None,
                                                                   "section": plex_item.section.title})
        return metadata


class AvailableSubsForItem(PlexItemMetadataMixin, Task):
    name = "AvailableSubsForItem"
    rating_key = None
    item_type = None
    part_id = None
    language = None

    def prepare(self, rating_key, item_type, part_id, language, *args, **kwargs):
        self.rating_key = rating_key
        self.item_type = item_type
        self.part_id = part_id
        self.language = language

    def run(self):
        self.running = True
        item_type = self.item_type
        metadata = self.get_plex_metadata()
        language = self.language
        part_id = self.part_id

        if item_type == "episode":
            min_score = int(Prefs["subtitles.search.minimumTVScore"])
        else:
            min_score = int(Prefs["subtitles.search.minimumMovieScore"])

        scanned_parts = scan_videos([metadata], kind="series" if item_type == "episode" else "movie", ignore_all=True)
        video, plex_part = scanned_parts.items()[0]

        # fixme: woot
        subliminal.video.Episode.scores["addic7ed_boost"] = int(Prefs['provider.addic7ed.boost_by'])

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

        self.data = subtitles

    def post_run(self, task_data):
        self.running = False
        task_data[self.rating_key] = self.data


class DownloadSubtitleForItem(PlexItemMetadataMixin, Task):
    name = "DownloadSubtitleForItem"
    rating_key = None
    subtitle = None
    item_type = None
    part_id = None

    def prepare(self, rating_key, subtitle, *args, **kwargs):
        self.rating_key = rating_key
        self.subtitle = subtitle
        self.item_type = subtitle.item_type
        self.part_id = subtitle.part_id

    def run(self):
        from support.storage import whack_missing_parts

        self.running = True
        metadata = self.get_plex_metadata()
        item_type = self.item_type
        scanned_parts = scan_videos([metadata], kind="series" if item_type == "episode" else "movie", ignore_all=True)
        video, plex_part = scanned_parts.items()[0]

        # downloaded_subtitles = {subliminal.Video: [subtitle, subtitle, ...]}
        download_subtitles([self.subtitle], providers=config.providers, provider_configs=config.provider_settings)

        if self.subtitle.content:
            whack_missing_parts(scanned_parts)

            # fixme?
            save_subtitles(scanned_parts, {video: [self.subtitle]})

    def post_run(self, task_data):
        self.running = False


scheduler.register(SearchAllRecentlyAddedMissing)
scheduler.register(AvailableSubsForItem)
scheduler.register(DownloadSubtitleForItem)
