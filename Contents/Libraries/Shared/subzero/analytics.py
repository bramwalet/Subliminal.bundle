# coding=utf-8

from pyga.requests import Event, Page, Tracker, Session, Visitor


def track_event(category=None, action=None, label=None, value=None, noninteraction=True):
    tracker = Tracker('UA-86466078-1', 'none')
    visitor = Visitor()
    session = Session()
    event = Event(category=category, action=action, label=label, value=value, noninteraction=noninteraction)
    path = u"/" + u"/".join([category, action, label])
    page = Page(path.lower())

    tracker.track_event(event, session, visitor)
    tracker.track_pageview(page, session, visitor)
