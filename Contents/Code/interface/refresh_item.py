# coding=utf-8

from subzero.constants import PREFIX
from menu_helpers import debounce, set_refresh_menu_state, route
from support.items import refresh_item
from support.helpers import timestamp


@route(PREFIX + '/item/{rating_key}')
@debounce
def RefreshItem(rating_key=None, came_from="/recent", item_title=None, force=False, refresh_kind=None,
                previous_rating_key=None, timeout=8000, randomize=None, trigger=True):
    assert rating_key
    from interface.main import fatality
    header = " "
    if trigger:
        set_refresh_menu_state(u"Triggering %sRefresh for %s" % ("Force-" if force else "", item_title))
        Thread.Create(refresh_item, rating_key=rating_key, force=force, refresh_kind=refresh_kind,
                      parent_rating_key=previous_rating_key, timeout=int(timeout))

        header = u"%s of item %s triggered" % ("Refresh" if not force else "Forced-refresh", rating_key)
    return fatality(randomize=timestamp(), header=header, replace_parent=True)
