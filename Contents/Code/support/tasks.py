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

        # dispatch all searches
        searchMissing(self.items_searching)

        while 1:
            if set(self.items_done).intersection(self.items_searching_ids) == self.items_searching_ids:
                Log.Debug("Task: %s, all items done", self.name)
                break
            self.percentage = int(round(len(self.items_done) * 100 / missing_count))
            time.sleep(0.1)

    def post_run(self):
        self.ready_for_display = False
        self.last_run = datetime.datetime.now()
        self.last_run_time = self.last_run - self.time_start
        self.time_start = None
        self.percentage = 0
        self.items_done = None
        self.items_searching = None
        self.running = False


scheduler.register(SearchAllRecentlyAddedMissing)
