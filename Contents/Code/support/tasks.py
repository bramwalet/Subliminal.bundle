# coding=utf-8

import datetime
import time

from missing_subtitles import getAllRecentlyAddedMissing, searchMissing
from background import scheduler

class Task(object):
    name = None
    scheduler = None

    stored_attributes = ("last_run", "running", "last_run_time")

    # task ready for being status-displayed?
    ready_for_display = False

    def __init__(self, scheduler):
	self.ready_for_display = False
	self.scheduler = scheduler
	if not self.name in Dict["tasks"]:
	    Dict["tasks"][self.name] = {"last_run": None, "running": False, "last_run_time": None}

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
    percentage = 0
    
    def __init__(self, scheduler):
	super(SearchAllRecentlyAddedMissing, self).__init__(scheduler)
	self.items_done = None
	self.items_searching = None
	self.percentage = 0

    def signal(self, signal_name, *args, **kwargs):
	if signal_name == "updated_metadata" and self.items_done is not None:
	    item_id = int(args[0])
    	    self.items_done.append(item_id)

    def run(self):
	self.running = True
	self.items_done = []
	missing = getAllRecentlyAddedMissing()
	ids = set([id for id, title in missing])
	self.items_searching = ids
	self.ready_for_display = True

	missing_count = len(ids)
	
	# dispatch all searches
	time_start = datetime.datetime.now()
	searchMissing(missing)

	while 1:
	    if set(self.items_done).intersection(ids) == ids:
		Log.Debug("Task: %s, all items done", self.name)
		break
	    self.percentage = int(round(len(self.items_done) * 100 / missing_count))
	    time.sleep(0.1)

	self.last_run_time = datetime.datetime.now() - time_start
	self.percentage = 0
	self.ready_for_display = False
	self.items_done = None
	self.items_searching = None
	self.running = False
	


scheduler.register(SearchAllRecentlyAddedMissing)
