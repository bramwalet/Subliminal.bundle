# coding=utf-8

import datetime

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

    def __getattribute__(self, name):
	if name in object.__getattribute__(self, "stored_attributes"):
	    return Dict["tasks"][self.name].get(name, None)

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
    

    def signal(self, signal_name, *args, **kwargs):
	if signal_name == "updated_metadata":
	    item_id = int(args[0])
    	    self.items_done.append(item_id)

    def run(self):
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
	    if ids == set(self.items_done):
		Log.Debug("Task: %s, all items done", self.name)
		break
	    self.percentage = int(round(len(self.items_done) * 100 / missing_count))
	    Thread.Sleep(1.0)

	self.last_run_time = datetime.datetime.now() - time_start
	self.percentage = 0
	self.ready_for_display = False


scheduler.register(SearchAllRecentlyAddedMissing)