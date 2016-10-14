# coding=utf-8
import types
import datetime

from support.items import get_kind, get_item_thumb
from support.helpers import format_video
from support.ignore import ignore_list
from support.lib import get_intent
from subzero.constants import ICON

default_thumb = R(ICON)


def should_display_ignore(items, previous=None):
    kind = get_kind(items)
    return items and (
        (kind in ("show", "season")) or
        (kind == "episode" and previous != "season")
    )


def add_ignore_options(oc, kind, callback_menu=None, title=None, rating_key=None, add_kind=True):
    """

    :param oc: oc to add our options to
    :param kind: movie, show, episode ... - gets translated to the ignore key (sections, series, items)
    :param callback_menu: menu to inject
    :param title:
    :param rating_key:
    :return:
    """
    # try to translate kind to the ignore key
    use_kind = kind
    if kind not in ignore_list:
        use_kind = ignore_list.translate_key(kind)
    if not use_kind or use_kind not in ignore_list:
        return

    in_list = rating_key in ignore_list[use_kind]

    oc.add(DirectoryObject(
        key=Callback(callback_menu, kind=use_kind, rating_key=rating_key, title=title),
        title=u"%s %s \"%s\" %s the ignore list" % (
            "Remove" if in_list else "Add", ignore_list.verbose(kind) if add_kind else "", unicode(title), "from" if in_list else "to")
    )
    )


def dig_tree(oc, items, menu_callback, menu_determination_callback=None, force_rating_key=None, fill_args=None, pass_kwargs=None,
             thumb=default_thumb):
    for kind, title, key, dig_deeper, item in items:
        thumb = get_item_thumb(item) or thumb

        add_kwargs = {}
        if fill_args:
            add_kwargs = dict((name, getattr(item, k)) for k, name in fill_args.iteritems() if item and hasattr(item, k))
        if pass_kwargs:
            add_kwargs.update(pass_kwargs)

        oc.add(DirectoryObject(
            key=Callback(menu_callback or menu_determination_callback(kind, item), title=title,
                         rating_key=force_rating_key or key, **add_kwargs),
            title=title, thumb=thumb
        ))
    return oc


def set_refresh_menu_state(state_or_media, media_type="movies"):
    """

    :param state_or_media: string, None, or Media argument from Agent.update()
    :param media_type: movies or series
    :return:
    """
    if not state_or_media:
        # store it in last state and remove the current
        Dict["last_refresh_state"] = Dict["current_refresh_state"]
        Dict["current_refresh_state"] = None
        return

    if isinstance(state_or_media, types.StringTypes):
        Dict["current_refresh_state"] = state_or_media
        return

    media = state_or_media
    media_id = media.id
    title = None
    if media_type == "series":
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                ep = media.seasons[season].episodes[episode]
                media_id = ep.id
                title = format_video("show", ep.title, parent_title=media.title, season=int(season), episode=int(episode))
    else:
        title = format_video("movie", media.title)

    intent = get_intent()
    force_refresh = intent.get("force", media_id)

    Dict["current_refresh_state"] = u"%sRefreshing %s" % ("Force-" if force_refresh else "", unicode(title))


def enable_channel_wrapper(func):
    """
    returns the original wrapper :func: (route or handler) if applicable, else the plain to-be-wrapped function
    :param func: original wrapper
    :return: original wrapper or wrapped function
    """
    def noop(*args, **kwargs):
        def inner(*a, **k):
            """
            :param a: args
            :param k: kwargs
            :return: originally to-be-wrapped function
            """
            return a[0]

        return inner

    def wrap(*args, **kwargs):
        enforce_route = kwargs.pop("enforce_route", None)
        return (func if Prefs["enable_channel"] or enforce_route else noop)(*args, **kwargs)

    return wrap


def debounce(func):
    """
    prevent func from being called twice with the same arguments
    :param func:
    :return:
    """
    def get_lookup_key(args, kwargs):
        func_name = list(args).pop(0).__name__
        return tuple([func_name] + [(key, value) for key, value in kwargs.iteritems()])

    def wrap(*args, **kwargs):
        if "randomize" in kwargs:
            if not "menu_history" in Dict:
                Dict["menu_history"] = {}

            key = get_lookup_key([func] + list(args), kwargs)
            if key in Dict["menu_history"]:
                Log.Debug("not triggering %s twice with %s, %s" % (func, args, kwargs))
                return ObjectContainer()
            else:
                Dict["menu_history"][key] = datetime.datetime.now() + datetime.timedelta(days=1)
                Dict.Save()
        return func(*args, **kwargs)

    return wrap


class SZObjectContainer(ObjectContainer):
    def __init__(self, *args, **kwargs):
        super(SZObjectContainer, self).__init__(*args, **kwargs)
        from interface.menu import fatality
        from support.helpers import pad_title, timestamp
        self.add(DirectoryObject(
            key=Callback(fatality, force_title=" ", randomize=timestamp()),
            title=pad_title("<< Back to home"),
            summary="Current state: %s; Last state: %s" % (
                (Dict["current_refresh_state"] or "Idle") if "current_refresh_state" in Dict else "Idle",
                (Dict["last_refresh_state"] or "None") if "last_refresh_state" in Dict else "None"
            )
        ))