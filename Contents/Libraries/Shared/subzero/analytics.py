# coding=utf-8

from pyga.requests import Event, Page, Tracker, Session, Visitor, Config


def track_event(category=None, action=None, label=None, value=None, uuid=None, first_use=None, add=None,
                noninteraction=True):
    anonymousConfig = Config()
    anonymousConfig.anonimize_ip_address = True

    tracker = Tracker('UA-86466078-1', 'none', conf=anonymousConfig)
    visitor = Visitor()

    if uuid:
        # convert a random uuid to an even more insignificant integer
        visitor.unique_id = uuid.int & (1 << 32)-1

    if add:
        # add visitor's ip address (will be anonymized)
        visitor.ip_address = add

    if first_use:
        visitor.first_visit_time = first_use

    session = Session()
    event = Event(category=category, action=action, label=label, value=value, noninteraction=noninteraction)
    path = u"/" + u"/".join([category, action, label])
    page = Page(path.lower())

    tracker.track_event(event, session, visitor)
    tracker.track_pageview(page, session, visitor)
