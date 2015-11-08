# coding=utf-8
from subzero.constants import TITLE, ART, ICON, PREFIX, PLUGIN_IDENTIFIER
from support.config import config
from support.helpers import pad_title, timestamp
from support.auth import refresh_plex_token
from support.missing_subtitles import getAllMissing
from support.storage import resetStorage, logStorage
from support.items import getOnDeckItems, refreshItem, getRecentItems
from support.items import getRecentlyAddedItems, getOnDeckItems, refreshItem, getAllItems
from support.background import scheduler
from support.lib import Plex, lib_unaccessible_error

# init GUI
ObjectContainer.title1 = TITLE
ObjectContainer.art = R(ART)
ObjectContainer.no_history = True
ObjectContainer.no_cache = True


@handler(PREFIX, TITLE, art=ART, thumb=ICON)
@route(PREFIX)
def fatality(randomize=None, header=None, message=None, only_refresh=False):
    """
    subzero main menu
    """
    oc = ObjectContainer(header=header, message=message, no_cache=True, no_history=True)

    if not config.plex_api_working:
        oc.add(DirectoryObject(
            key=Callback(fatality, randomize=timestamp()),
            title=pad_title("PMS API ERROR"),
            summary=lib_unaccessible_error
        ))
        return oc

    if not only_refresh:
        oc.add(DirectoryObject(
            key=Callback(OnDeckMenu),
            title=pad_title("Subtitles for 'On Deck' items"),
            summary="Shows the current on deck items and allows you to individually (force-) refresh their metadata/subtitles."
        ))
        oc.add(DirectoryObject(
            key=Callback(RecentlyAddedMenu),
            title="Show items with missing subtitles (max-age: %s)" % Prefs["scheduler.item_is_recent_age"],
            summary="Shows the items honoring the configured 'Item age to be considered recent'-setting (%s)"
                    " and allowing you to individually (force-) refresh their metadata/subtitles. "
                    "Limited to recently-added items (max. 100 per section) " % Prefs["scheduler.item_is_recent_age"]
        ))
        oc.add(DirectoryObject(
            key=Callback(SectionsMenu),
            title="Browse all items"
        ))

        task_name = "searchAllRecentlyAddedMissing"
        task = scheduler.task(task_name)

        if task.ready_for_display:
            task_state = "Running: %s/%s (%s%%)" % (len(task.items_done), len(task.items_searching), task.percentage)
        else:
            task_state = "Last scheduler run: %s; Next scheduled run: %s; Last runtime: %s" % (scheduler.last_run(task_name) or "never",
                                                                                               scheduler.next_run(task_name) or "never",
                                                                                               str(task.last_run_time).split(".")[0])

        oc.add(DirectoryObject(
            key=Callback(RefreshMissing, randomize=timestamp()),
            title="Search for missing subtitles (in recently-added items, max-age: %s)" % Prefs["scheduler.item_is_recent_age"],
            summary="Automatically run periodically by the scheduler, if configured. %s" % task_state
        ))

    oc.add(DirectoryObject(
        key=Callback(fatality, randomize=timestamp()),
        title=pad_title("Refresh"),
        summary="Refreshes the current view"
    ))

    if not only_refresh:
        oc.add(DirectoryObject(
            key=Callback(AdvancedMenu, randomize=timestamp()),
            title=pad_title("Advanced functions"),
            summary="Use at your own risk"
        ))

    return oc


@route(PREFIX + '/on_deck')
def OnDeckMenu(message=None):
    return mergedItemsMenu(title="Items On Deck", itemGetter=getOnDeckItems)


@route(PREFIX + '/recent')
def RecentlyAddedMenu(message=None):
    return recentItemsMenu(title="Recently Added Items")


def recentItemsMenu(title):
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)
    recent_items = getRecentItems()
    if recent_items:
        missing_items = reversed(sorted(getAllMissing(recent_items)))
        if missing_items:
            for added_at, item_id, title in missing_items:
                oc.add(DirectoryObject(
                    key=Callback(RefreshItemMenu, title=title, rating_key=item_id), title=title
                ))

    return oc


def mergedItemsMenu(title, itemGetter, itemGetterKwArgs=None, *args, **kwargs):
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)
    items = itemGetter(*args, **kwargs)

    for kind, title, item_id, deeper, item in items:
        oc.add(DirectoryObject(
            title=title,
            key=Callback(RefreshItemMenu, title=title, rating_key=item_id)
        ))

    return oc


def dig_tree(oc, items, menu_callback, **kwargs):
    for kind, title, key, dig_deeper, item in items:
        oc.add(DirectoryObject(
            key=Callback(menu_callback, title=title, rating_key=key, deeper=dig_deeper),
            title=title
        ))
    return oc


@route(PREFIX + '/sections')
def SectionsMenu():
    items = getAllItems("sections")

    return dig_tree(ObjectContainer(title2="Sections", no_cache=True, no_history=True), items, SectionMenu)


@route(PREFIX + '/section', deeper=bool)
def SectionMenu(rating_key, title=None, deeper=False):
    items = getAllItems(key="all", value=rating_key, base="library/sections", flat=not deeper)

    return dig_tree(ObjectContainer(title2=title, no_cache=True, no_history=True), items, MetadataMenu)


@route(PREFIX + '/section/contents', deeper=bool)
def MetadataMenu(rating_key, title=None, deeper=False):
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)

    if deeper:
        items = getAllItems(key="children", value=rating_key, base="library/metadata", flat=False)
        dig_tree(oc, items, MetadataMenu)
    else:
        return RefreshItemMenu(rating_key=rating_key, title=title)

    return oc


@route(PREFIX + '/item/{rating_key}/actions')
def RefreshItemMenu(rating_key, title=None, came_from="/recent"):
    title = unicode(title)
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)
    oc.add(DirectoryObject(
        key=Callback(RefreshItem, rating_key=rating_key),
        title="Refresh: %s" % title,
        summary="Refreshes the item, possibly picking up new subtitles on disk"
    ))
    oc.add(DirectoryObject(
        key=Callback(RefreshItem, rating_key=rating_key, force=True),
        title="Force-Refresh: %s" % title,
        summary="Issues a forced refresh, ignoring known subtitles and searching for new ones"
    ))

    return oc


@route(PREFIX + '/item/{rating_key}')
def RefreshItem(rating_key=None, came_from="/recent", force=False):
    assert rating_key
    Thread.Create(refreshItem, rating_key=rating_key, force=force)
    return fatality(randomize=timestamp(), header="%s of item %s triggered" % ("Refresh" if not force else "Forced-refresh", rating_key))


@route(PREFIX + '/missing/refresh')
def RefreshMissing(randomize=None):
    Thread.CreateTimer(1.0, lambda: scheduler.run_task("searchAllRecentlyAddedMissing"))
    return fatality(header="Refresh of recently added items with missing subtitles triggered")


@route(PREFIX + '/advanced')
def AdvancedMenu(randomize=None, header=None, message=None):
    oc = ObjectContainer(header=header or "Internal stuff, pay attention!", message=message, no_cache=True, no_history=True, title2="Advanced")

    oc.add(DirectoryObject(
        key=Callback(TriggerRestart),
        title=pad_title("Restart the plugin")
    ))
    oc.add(DirectoryObject(
        key=Callback(RefreshToken, randomize=timestamp()),
        title=pad_title("Re-request the API token from plex.tv")
    ))
    oc.add(DirectoryObject(
        key=Callback(LogStorage, key="tasks", randomize=timestamp()),
        title=pad_title("Log the plugin's scheduled tasks state storage")
    ))
    oc.add(DirectoryObject(
        key=Callback(LogStorage, key="subs", randomize=timestamp()),
        title=pad_title("Log the plugin's internal subtitle information storage")
    ))
    oc.add(DirectoryObject(
        key=Callback(ResetStorage, key="tasks", randomize=timestamp()),
        title=pad_title("Reset the plugin's scheduled tasks state storage")
    ))
    oc.add(DirectoryObject(
        key=Callback(ResetStorage, key="subs", randomize=timestamp()),
        title=pad_title("Reset the plugin's internal subtitle information storage")
    ))
    return oc


@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
    Log.Debug("Validate Prefs called.")
    config.initialize()
    scheduler.setup_tasks()
    return


@route(PREFIX + '/advanced/restart/trigger')
def TriggerRestart(randomize=None):
    Thread.CreateTimer(1.0, Restart)
    return fatality(header="Restart triggered, please wait about 5 seconds", only_refresh=True)


@route(PREFIX + '/advanced/restart/execute')
def Restart():
    Plex[":/plugins"].restart(PLUGIN_IDENTIFIER)


@route(PREFIX + '/storage/reset', sure=bool)
def ResetStorage(key, randomize=None, sure=False):
    if not sure:
        oc = ObjectContainer(no_history=True, title1="Reset subtitle storage", title2="Are you sure?")
        oc.add(DirectoryObject(
            key=Callback(ResetStorage, key=key, sure=True, randomize=timestamp()),
            title=pad_title("Are you really sure?")
        ))
        return oc

    resetStorage(key)

    if key == "tasks":
        # reinitialize the scheduler
        scheduler.init_storage()
        scheduler.setup_tasks()

    return AdvancedMenu(
        randomize=timestamp(),
        header='Success',
        message='Information Storage (%s) reset' % key
    )


@route(PREFIX + '/storage/log')
def LogStorage(key, randomize=None):
    logStorage(key)
    return AdvancedMenu(
        randomize=timestamp(),
        header='Success',
        message='Information Storage (%s) logged' % key
    )


@route(PREFIX + '/refresh_token')
def RefreshToken(randomize=None):
    result = refresh_plex_token()
    if result:
        msg = "Token successfully refreshed."
    else:
        msg = "Couldn't refresh the token, please check your credentials"

    return AdvancedMenu(header=msg)
