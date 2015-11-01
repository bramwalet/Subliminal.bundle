# coding=utf-8

from subzero import intent
from subzero.constants import TITLE, ART, ICON, PREFIX, PLUGIN_IDENTIFIER
from support.config import config
from support.helpers import pad_title, encode_message, decode_message, timestamp
from support.auth import refresh_plex_token
from support.storage import resetStorage
from support.items import getRecentlyAddedItems, getOnDeckItems, refreshItem
from support.missing_subtitles import getAllRecentlyAddedMissing, searchMissing
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
    	    title="Subtitles for 'Recently Added' items (max-age: %s)" % Prefs["scheduler.item_is_recent_age"],
	    summary="Shows the recently added items, honoring the configured 'Item age to be considered recent'-setting (%s) and allowing you to individually (force-) refresh their metadata/subtitles." % Prefs["scheduler.item_is_recent_age"]
	))

	task_name = "searchAllRecentlyAddedMissing"
	task = scheduler.task(task_name)

        if task.ready_for_display:
	    task_state = "Running: %s/%s (%s%%)" % (len(task.items_done), len(task.items_searching), task.percentage)
        else:
	    task_state = "Last scheduler run: %s; Next scheduled run: %s; Last runtime: %s" % (scheduler.last_run(task_name) or "never",
											   scheduler.next_run(task_name) or "never", str(task.last_run_time).split(".")[0])

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
    return mergedItemsMenu(title="Recently Added Items", itemGetter=getRecentlyAddedItems)

def mergedItemsMenu(title, itemGetter):
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)
    items = itemGetter()

    for kind, title, item in items:
	menu_title = title
	oc.add(DirectoryObject(
    	    key=Callback(RefreshItemMenu, title=menu_title, rating_key=item.rating_key),
    	    title=menu_title
	))

    return oc

@route(PREFIX + '/item/{rating_key}/actions')
def RefreshItemMenu(rating_key, title=None, came_from="/recent"):
    oc = ObjectContainer(title1=title, no_cache=True, no_history=True)
    oc.add(DirectoryObject(
    	key=Callback(RefreshItem, rating_key=rating_key),
    	title=u"Refresh: %s" % title,
	summary="Refreshes the item, possibly picking up new subtitles on disk"
    ))
    oc.add(DirectoryObject(
    	key=Callback(RefreshItem, rating_key=rating_key, force=True),
    	title=u"Force-Refresh: %s" % title,
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
    return AdvancedMenu(
	randomize=timestamp(),
        header='Success',
        message='Subtitle Information Storage reset'
    )

@route(PREFIX + '/refresh_token')
def RefreshToken(randomize=None):
    result = refresh_plex_token()
    if result:
	msg = "Token successfully refreshed."
    else:
	msg = "Couldn't refresh the token, please check your credentials"
    
    return AdvancedMenu(header=msg)
