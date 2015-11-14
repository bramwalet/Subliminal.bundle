# coding=utf-8
import types

from subzero import intent
from support.helpers import format_video
from support.ignore import ignore_list


def add_ignore_options(oc, kind, callback_menu=None, title=None, rating_key=None, add_kind=False):
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
            title="%s %s \"%s\" %s the ignore list" % (
                "Remove" if in_list else "Add", ignore_list.verbose(kind) if add_kind else "", unicode(title), "from" if in_list else "to")
        )
    )


def dig_tree(oc, items, menu_callback, menu_determination_callback=None, force_rating_key=None, fill_args=None, pass_kwargs=None):
    for kind, title, key, dig_deeper, item in items:
        add_kwargs = {}
        if fill_args:
            add_kwargs = dict((k, getattr(item, k)) for k in fill_args if item and hasattr(item, k))
        if pass_kwargs:
            add_kwargs.update(pass_kwargs)

        oc.add(DirectoryObject(
            key=Callback(menu_callback or menu_determination_callback(kind, item), title=title, rating_key=force_rating_key or key,
                         deeper=dig_deeper, **add_kwargs),
            title=title
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
    force_refresh = intent.get("force", media_id)

    Dict["current_refresh_state"] = "%sRefreshing %s" % ("Force-" if force_refresh else "", title)

