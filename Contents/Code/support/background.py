# coding=utf-8

import datetime
import logging
import traceback

import tasks


def parse_frequency(s):
    if s == "never":
	return None, None
    kind, num, unit = s.split()
    return int(num), unit

class DefaultScheduler(object):
    def __init__(self):
	self.thread = None
	self.running = False

	self.tasks = {}
	if not "tasks" in Dict:
	    Dict["tasks"] = {}
	self.discover_tasks()

    def discover_tasks(self):
	# discover tasks; todo: add registry
	for item in dir(tasks):
	    if item.startswith("task_"):
		task_name = item.split("task_")[1]
		self.tasks[task_name] = {"task": getattr(tasks, item), "frequency": parse_frequency(Prefs["scheduler.tasks.%s" % task_name])}

    def run(self):
	self.running = True
	self.thread = Thread.Create(self.worker)

    def stop(self):
	self.running = False

    def last_run(self, task):
	if task not in Dict["tasks"]:
	    return None
	return Dict["tasks"][task]["last_run"]

    def next_run(self, task):
	if task not in self.tasks:
	    return None
	frequency_num, frequency_key = self.tasks[task]["frequency"]
	if not frequency_num:
	    return None
	last = self.last_run(task)
	use_date = last
	if not use_date:
	    use_date = datetime.datetime.now()
	return use_date + datetime.timedelta(**{frequency_key: frequency_num})

    def worker(self):
	while 1:
	    if not self.running:
		break
	    #Log.Debug("working %s", Prefs)
	    for name, info in self.tasks.iteritems():
		now = datetime.datetime.now()

		if name not in Dict["tasks"]:
		    Dict["tasks"][name] = {"last_run": now, "running": False}
		    Dict.Save()
		    continue

		task_state = Dict["tasks"][name]
		if task_state["running"]:
		    continue
		
		frequency_num, frequency_key = info["frequency"]
		if not frequency_num:
		    continue

		if task_state["last_run"] + datetime.timedelta(**{frequency_key: frequency_num}) <= now:
		    task_state["running"] = True
		    try:
		    	info["task"]()
		    except Exception, e:
		    	Log.Error("Something went wrong when running %s: %s", name, traceback.format_exc())
		    finally:
		    	task_state["last_run"] = now
		    	task_state["running"] = False
		    	Dict.Save()
		    
	    Thread.Sleep(10.0)

scheduler = DefaultScheduler()
