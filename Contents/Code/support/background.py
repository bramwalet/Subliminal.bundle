# coding=utf-8

import logging

logger = logging.getLogger(__name__)


class DefaultScheduler(object):
    def __init__(self):
	self.thread = None
	self.running = False

    def run(self):
	self.running = True
	self.thread = Thread.Create(self.worker)

    def stop(self):
	self.running = False

    def worker(self):
	while 1:
	    if not self.running:
		break
	    Log.Debug("working %s", Prefs)
	    Thread.Sleep(10.0)