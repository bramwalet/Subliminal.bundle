# coding=utf-8
import types
import datetime

from func import enable_channel_wrapper, route_wrapper
from support.i18n import is_localized_string, _
from support.items import get_item_thumb
from support.helpers import get_video_display_title, pad_title
from support.ignore import get_decision_list
from support.lib import get_intent
from support.config import config
from subzero.constants import ICON_SUB, ICON
from support.scheduler import scheduler

default_thumb = R(ICON_SUB)
main_icon = ICON if not config.is_development else "icon-dev.jpg"

# noinspection PyUnboundLocalVariable
route = route_wrapper
# noinspection PyUnboundLocalVariable
handler = enable_channel_wrapper(handler)


def add_incl_excl_options(oc, kind, callback_menu=None, title=None, rating_key=None, add_kind=True):
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
    ref_list = get_decision_list()
    if kind not in ref_list:
        use_kind = ref_list.translate_key(kind)
    if not use_kind or use_kind not in ref_list:
        return

    in_list = rating_key in ref_list[use_kind]
    include = ref_list.store == "include"

    if include:
        t = u"Enable Sub-Zero for %(kind)s \"%(title)s\""
        if in_list:
            t = u"Disable Sub-Zero for %(kind)s \"%(title)s\""
    else:
        t = u"Ignore %(kind)s \"%(title)s\""
        if in_list:
            t = u"Un-ignore %(kind)s \"%(title)s\""

    oc.add(DirectoryObject(
        key=Callback(callback_menu, kind=use_kind, sure=False, todo="not_set", rating_key=str(rating_key), title=title),
        title=_(t,
                kind=ref_list.verbose(kind) if add_kind else "",
                title=unicode(title))
    )
    )


def dig_tree(oc, items, menu_callback, menu_determination_callback=None, force_rating_key=None, fill_args=None,
             pass_kwargs=None, thumb=default_thumb):
    for kind, title, key, dig_deeper, item in items:
        thumb = get_item_thumb(item) or thumb

        add_kwargs = {}
        if fill_args:
            add_kwargs = dict((name, getattr(item, k)) for k, name in fill_args.iteritems() if item and hasattr(item, k))
        if pass_kwargs:
            add_kwargs.update(pass_kwargs)

        # force details view for show/season
        summary = " " if kind in ("show", "season") else None

        oc.add(DirectoryObject(
            key=Callback(menu_callback or menu_determination_callback(kind, item, pass_kwargs=pass_kwargs), title=title,
                         rating_key=force_rating_key or key, **add_kwargs),
            title=pad_title(title) if kind in ("show", "season") else title, thumb=thumb, summary=summary
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
        Dict.Save()
        return

    if isinstance(state_or_media, types.StringTypes) or is_localized_string(state_or_media):
        Dict["current_refresh_state"] = unicode(state_or_media)
        Dict.Save()
        return

    media = state_or_media
    media_id = media.id
    title = None
    if media_type == "series":
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                ep = media.seasons[season].episodes[episode]
                media_id = ep.id
                title = get_video_display_title(_("show"), ep.title, parent_title=media.title, season=int(season), episode=int(episode))
    else:
        title = get_video_display_title(_("movie"), media.title)

    intent = get_intent()
    force_refresh = intent.get("force", media_id)

    t = u"Refreshing %(title)s"
    if force_refresh:
        t = u"Force-refreshing %(title)s"

    Dict["current_refresh_state"] = unicode(_(t,
                                              title=unicode(title)))
    Dict.Save()


def get_item_task_data(task_name, rating_key, language):
    task_data = scheduler.get_task_data(task_name)
    search_results = task_data.get(rating_key, {}) if task_data else {}
    return search_results.get(language)


def debounce(func):
    """
    prevent func from being called twice with the same arguments
    :param func:
    :return:
    """

    func.debounce = True

    return func


class SZObjectContainer(ObjectContainer):
    def __init__(self, *args, **kwargs):
        skip_pin_lock = kwargs.pop("skip_pin_lock", False)

        super(SZObjectContainer, self).__init__(*args, **kwargs)

        if (config.lock_menu or config.lock_advanced_menu) and not config.pin_correct and not skip_pin_lock:
            config.locked = True

    def add(self, *args, **kwargs):
        # disable self.add if we're in lockdown
        container = args[0]
        current_menu_target = container.key.split("?")[0]
        is_pin_menu = current_menu_target.endswith("/pin")

        if config.locked and config.lock_menu and not is_pin_menu:
            return
        return super(SZObjectContainer, self).add(*args, **kwargs)


OriginalObjectContainer = ObjectContainer
ObjectContainer = SZObjectContainer


class SubFolderObjectContainer(ObjectContainer):
    def __init__(self, *args, **kwargs):
        super(SubFolderObjectContainer, self).__init__(*args, **kwargs)
        from interface.menu import fatality
        from support.helpers import pad_title, timestamp
        self.add(DirectoryObject(
            key=Callback(fatality, force_title=" ", randomize=timestamp()),
            title=pad_title(_("<< Back to home")),
            summary=_("Current state: %s; Last state: %s",
                (Dict["current_refresh_state"] or _("Idle")) if "current_refresh_state" in Dict else _("Idle"),
                (Dict["last_refresh_state"] or _("None")) if "last_refresh_state" in Dict else _("None")
            )
        ))


ObjectClass = getattr(getattr(Redirect, "_object_class"), "__bases__")[0]


class ZipObject(ObjectClass):
    def __init__(self, data):
        ObjectClass.__init__(self, "")
        self.zipdata = data
        self.SetHeader("Content-Type", "application/zip")

    def Content(self):
        self.SetHeader("Content-Disposition",
                       'attachment; filename="' + datetime.datetime.now().strftime("Logs_%y%m%d_%H-%M-%S.zip")
                       + '"')
        return self.zipdata
