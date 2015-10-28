# coding=utf-8

from subzero import intent
from subzero.constants import TITLE, ART, ICON, PREFIX, PLUGIN_IDENTIFIER
from support.config import config
from support.helpers import pad_title, encode_message, decode_message
from support.auth import refresh_plex_token
from support.storage import resetStorage
from support.items import getRecentlyAddedItems, getOnDeckItems, refreshItem
from support.missing_subtitles import searchAllRecentlyAddedMissing
from support.tasks import taskData

# init GUI
ObjectContainer.title1 = TITLE
ObjectContainer.art = R(ART)
ObjectContainer.no_history = True
ObjectContainer.no_cache = True

Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def fatality():
    """
    subzero main menu
    """
    oc = ObjectContainer(no_cache=True, no_history=True, view_group="Details")
    oc.add(DirectoryObject(
        key=Callback(OnDeckMenu),
        title="Items On Deck"
    ))
    oc.add(DirectoryObject(
        key=Callback(RecentlyAddedMenu),
        title="Recently Added Items"
    ))
    task_info = taskData("searchAllRecentlyAddedMissing")
    oc.add(DirectoryObject(
        key=Callback(RefreshMissing),
        title="Refresh items with missing subtitles",
	summary="Last refresh: %s" % task_info["last_run"] if task_info else "never"
    ))
    oc.add(DirectoryObject(
        key=Callback(AdvancedMenu),
        title="Advanced functions"
    ))

    return oc



@route(PREFIX + '/on_deck')
def OnDeckMenu(message=None):
    return mergedItemsMenu(title="Items On Deck", itemGetter=getOnDeckItems)

@route(PREFIX + '/recent')
def RecentlyAddedMenu(message=None):
    return mergedItemsMenu(title="Recently Added Items", itemGetter=getRecentlyAddedItems)

def mergedItemsMenu(title, itemGetter):
    oc = ObjectContainer(title1=title, no_cache=True, no_history=True)
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
    	title=u"Refresh: %s" % title
    ))
    oc.add(DirectoryObject(
    	key=Callback(RefreshItem, rating_key=rating_key),
    	title=u"Force-Refresh: %s" % title
    ))

    return oc


@route(PREFIX + '/item/{rating_key}')
def RefreshItem(rating_key=None, came_from="/recent", force=False):
    assert rating_key
    Thread.Create(refreshItem, rating_key=rating_key, force=force)
    return ObjectContainer(message="%s of item %s triggered" % ("Refresh" if not force else "Forced-refresh", rating_key))

@route(PREFIX + '/missing/refresh')
def RefreshMissing():
    Thread.CreateTimer(1.0, searchAllRecentlyAddedMissing)
    return ObjectContainer(message="Refresh of recently added items with missing subtitles triggered")

@route(PREFIX + '/advanced')
def AdvancedMenu():
    oc = ObjectContainer(header="Internal stuff, pay attention!", no_cache=True, no_history=True)
    
    oc.add(DirectoryObject(
        key=Callback(TriggerRestart),
        title=pad_title("Restart the plugin")
    ))
    oc.add(DirectoryObject(
        key=Callback(RefreshToken),
        title=pad_title("Re-request the API token from plex.tv")
    ))
    oc.add(DirectoryObject(
        key=Callback(ResetStorage, key="subs"),
        title=pad_title("Reset the plugin's internal subtitle information storage")
    ))
    return oc

@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
    Log.Debug("Validate Prefs called.")
    config.initialize()
    return

@route(PREFIX + '/advanced/restart/trigger')
def TriggerRestart():
    Thread.CreateTimer(1.0, Restart)
    return ObjectContainer(message="Restart triggered, please wait about 5 seconds")

@route(PREFIX + '/advanced/restart/execute')
def Restart():
    config.Plex[":/plugins"].restart(PLUGIN_IDENTIFIER)

@route(PREFIX + '/storage/reset', sure=bool)
def ResetStorage(key, sure=False):
    if not sure:
	oc = ObjectContainer(no_history=True, title1="Reset subtitle storage", title2="Are you sure?")
	oc.add(DirectoryObject(
	    key=Callback(ResetStorage, key=key, sure=True),
	    title=pad_title("Are you really sure? The internal subtitle storage is very useful!")
	))
	return oc

    resetStorage(key)
    return ObjectContainer(
        header='Success',
        message='Subtitle Information Storage reset'
    )

@route(PREFIX + '/refresh_token')
def RefreshToken():
    result = refresh_plex_token()
    if result:
	msg = "Token successfully refreshed."
    else:
	msg = "Couldn't refresh the token, please check your credentials"
    
    return ObjectContainer(message=msg)