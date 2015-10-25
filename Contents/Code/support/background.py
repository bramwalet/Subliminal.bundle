# coding=utf-8

import datetime
import logging

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

    def worker(self):
	while 1:
	    if not self.running:
		break
	    #Log.Debug("working %s", Prefs)
	    for name, info in self.tasks.iteritems():
		now = datetime.datetime.now()

		if name not in Dict["tasks"]:
		    Dict["tasks"][name] = {"last_run": now, "running": False}
		    continue

		task_state = Dict["tasks"][name]
		if task_state["running"]:
		    continue
		
		frequency_num, frequency_key = info["frequency"]

		if task_state["last_run"] + datetime.timedelta(**{frequency_key: frequency_num}) <= now:
		    task_state["running"] = True
		    info["task"]()
		    task_state["last_run"] = now
		    task_state["running"] = False
		    Dict.Save()
		    
	    Thread.Sleep(10.0)