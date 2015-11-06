# coding=utf-8

import datetime
import time
from missing_subtitles import getAllRecentlyAddedMissing, searchMissing
from background import scheduler


class Task(object):
    name = None
    scheduler = None
    running = False
    time_start = None

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

    def prepare(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class SearchAllRecentlyAddedMissing(Task):
    name = "searchAllRecentlyAddedMissing"
    items_done = None
    items_searching = None
    items_searching_ids = None
    percentage = 0

    stall_time = 30

    def __init__(self, scheduler):
        super(SearchAllRecentlyAddedMissing, self).__init__(scheduler)
        self.items_done = None
        self.items_searching = None
        self.items_searching_ids = None
        self.percentage = 0

    def signal(self, signal_name, *args, **kwargs):
        handler = getattr(self, "signal_%s" % signal_name)
        return handler(*args, **kwargs) if handler else None

    def signal_updated_metadata(self, *args, **kwargs):
        item_id = int(args[0])

        if item_id in self.items_searching_ids:
            self.items_done.append(item_id)
            return True

    def prepare(self):
        self.items_done = []
        missing = getAllRecentlyAddedMissing()
        ids = set([id for id, title in missing])
        self.items_searching = missing
        self.items_searching_ids = ids
        self.percentage = 0
        self.time_start = datetime.datetime.now()
        self.ready_for_display = True

    def run(self):
        self.running = True
        missing_count = len(self.items_searching)
        items_done_count = 0

        for item_id, title in self.items_searching:
            Log.Debug(u"Task: %s, triggering refresh for %s (%s)", self.name, title, item_id)
            searchMissing(item_id, title)
            search_started = datetime.datetime.now()
            while 1:
                if item_id in self.items_done:
                    items_done_count += 1
                    Log.Debug(u"Task: %s, item %s done", self.name, item_id)
                    self.percentage = int(items_done_count * 100 / missing_count)
                    break

                if (datetime.datetime.now() - search_started).total_seconds() > self.stall_time:
                    Log.Debug(u"Task: %s, item stalled for %s seconds: %s, retrying", self.name, self.stall_time, item_id)
                    searchMissing(item_id, title)
                    search_started = datetime.datetime.now()
                    time.sleep(1)
                time.sleep(0.5)
            time.sleep(2)
        Log.Debug("Task: %s, all items done", self.name)
        self.running = False

    def post_run(self):
        self.ready_for_display = False
        self.last_run = datetime.datetime.now()
        self.last_run_time = self.last_run - self.time_start
        self.time_start = None
        self.percentage = 0
        self.items_done = None
        self.items_searching = None
        self.items_searching_ids = None


scheduler.register(SearchAllRecentlyAddedMissing)
