# coding=utf-8

import datetime
import logging
import traceback


def parse_frequency(s):
    if s == "never" or s == None:
        return None, None
    kind, num, unit = s.split()
    return int(num), unit


class DefaultScheduler(object):
    thread = None
    running = False
    registry = None

    def __init__(self):
        self.thread = None
        self.running = False
        self.registry = []

        self.tasks = {}
        self.init_storage()

    def init_storage(self):
        if "tasks" not in Dict:
            Dict["tasks"] = {}
            Dict.Save()

    def get_task_data(self, name):
        if name not in Dict["tasks"]:
            raise NotImplementedError("Task missing! %s" % name)

        if "data" in Dict["tasks"][name]:
            return Dict["tasks"][name]["data"]

    def clear_task_data(self, name):
        if name not in Dict["tasks"]:
            raise NotImplementedError("Task missing! %s" % name)

        Dict["tasks"][name]["data"] = {}
        Dict.Save()
        Log.Debug("Task data cleared: %s", name)

    def register(self, task):
        self.registry.append(task)

    def setup_tasks(self):
        # discover tasks;
        self.tasks = {}
        for cls in self.registry:
            task = cls(self)
            try:
                task_frequency = Prefs["scheduler.tasks.%s" % task.name]
            except KeyError:
                task_frequency = None

            self.tasks[task.name] = {"task": task, "frequency": parse_frequency(task_frequency)}

    def run(self):
        self.running = True
        self.thread = Thread.Create(self.worker)

    def stop(self):
        self.running = False

    def task(self, name):
        if name not in self.tasks:
            return None
        return self.tasks[name]["task"]

    def is_task_running(self, name):
        task = self.task(name)
        if task:
            return task.running

    def last_run(self, task):
        if task not in self.tasks:
            return None
        return self.tasks[task]["task"].last_run

    def next_run(self, task):
        if task not in self.tasks or not self.tasks[task]["task"].periodic:
            return None
        frequency_num, frequency_key = self.tasks[task]["frequency"]
        if not frequency_num:
            return None
        last = self.tasks[task]["task"].last_run
        use_date = last
        now = datetime.datetime.now()
        if not use_date:
            use_date = now
        return max(use_date + datetime.timedelta(**{frequency_key: frequency_num}), now)

    def run_task(self, name, *args, **kwargs):
        task = self.tasks[name]["task"]
        if task.running:
            Log.Debug("Scheduler: Not running %s, as it's currently running.", name)
            return False

        Log.Debug("Scheduler: Running task %s", name)
        try:
            task.prepare(*args, **kwargs)
            task.run()
        except Exception, e:
            Log.Error("Scheduler: Something went wrong when running %s: %s", name, traceback.format_exc())
        finally:
            task.post_run(Dict["tasks"][name]["data"])

    def dispatch_task(self, *args, **kwargs):
        Thread.Create(self.run_task, True, *args, **kwargs)
        Log.Debug("Dispatching single task: %s, %s", args, kwargs)

    def signal(self, name, *args, **kwargs):
        for task_name, info in self.tasks.iteritems():
            task = info["task"]
            if not task.periodic:
                continue

            if task.running:
                Log.Debug("Scheduler: Sending signal %s to task %s (%s, %s)", name, task_name, args, kwargs)
                status = task.signal(name, *args, **kwargs)
                if status:
                    Log.Debug("Scheduler: Signal accepted by %s", task_name)
                else:
                    Log.Debug("Scheduler: Signal not accepted by %s", task_name)
                continue
            Log.Debug("Scheduler: Not sending signal %s to task %s, because: not running", name, task_name)

    def worker(self):
        Thread.Sleep(10.0)
        while 1:
            if not self.running:
                break

            for name, info in self.tasks.iteritems():
                now = datetime.datetime.now()
                task = info["task"]

                if name not in Dict["tasks"] or not task.periodic:
                    continue

                if task.running:
                    continue

                frequency_num, frequency_key = info["frequency"]
                if not frequency_num:
                    continue

                if not task.last_run or task.last_run + datetime.timedelta(**{frequency_key: frequency_num}) <= now:
                    self.run_task(name)

            Thread.Sleep(10.0)


scheduler = DefaultScheduler()
