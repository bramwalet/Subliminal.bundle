# coding=utf-8

from subzero import intent
from subzero.constants import TITLE, ART, ICON, PREFIX, PLUGIN_IDENTIFIER
from support.config import config
from support.helpers import pad_title, encode_message, decode_message
from support.auth import refresh_plex_token
from support.storage import resetStorage
from support.items import getRecentlyAddedItems, getOnDeckItems, refreshItem
from support.missing_subtitles import searchAllRecentlyAddedMissing

# init GUI
ObjectContainer.title1 = TITLE
ObjectContainer.art = R(ART)
ObjectContainer.no_history = True
ObjectContainer.no_cache = True

@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def fatality(message=None):
    """
    subzero main menu
    """
    oc = ObjectContainer(header=decode_message(message) if message else None, no_cache=True, no_history=True)
    oc.add(DirectoryObject(
        key=Callback(OnDeckMenu),
        title=pad_title("Items On Deck")
    ))
    oc.add(DirectoryObject(
        key=Callback(RecentlyAddedMenu),
        title=pad_title("Recently Added Items")
    ))
    oc.add(DirectoryObject(
        key=Callback(RefreshMissing),
        title=pad_title("Refresh items with missing subtitles")
    ))
    oc.add(DirectoryObject(
        key=Callback(AdvancedMenu),
        title=pad_title("Advanced functions")
    ))

    return oc



@route(PREFIX + '/on_deck')
def OnDeckMenu(message=None):
    return mergedItemsMenu(title1="Items On Deck", itemGetter=getOnDeckItems, forward_came_from="/on_deck", message=message)

@route(PREFIX + '/recent')
def RecentlyAddedMenu(message=None):
    return mergedItemsMenu(title1="Recently Added Items", itemGetter=getRecentlyAddedItems, forward_came_from="/recent", message=message)

def mergedItemsMenu(title1, itemGetter, forward_came_from=None, message=None):
    oc = ObjectContainer(title1=title1, no_cache=True, no_history=True, header=decode_message(message) if message else None)
    items = itemGetter()

    for kind, title, item in items:
	menu_title = pad_title(title)
	oc.add(DirectoryObject(
    	    key=Callback(RefreshItemMenu, title=menu_title, rating_key=item.rating_key, came_from=forward_came_from),
    	    title=menu_title
	))

    return oc

@route(PREFIX + '/item/{rating_key}/actions')
def RefreshItemMenu(rating_key, title=None, came_from="/recent"):
    oc = ObjectContainer(title1=title, no_cache=True, no_history=True)
    oc.add(DirectoryObject(
    	key=Callback(RefreshItem, rating_key=rating_key, came_from=came_from),
    	title=u"Refresh: %s" % title
    ))
    oc.add(DirectoryObject(
    	key=Callback(RefreshItem, rating_key=rating_key, came_from=came_from, force=True),
    	title=u"Force-Refresh: %s" % title
    ))

    return oc


@route(PREFIX + '/item/{rating_key}')
def RefreshItem(rating_key=None, came_from="/recent", force=False):
    assert rating_key
    Thread.Create(refreshItem, rating_key=rating_key, force=force)
    return Redirect(encode_message(PREFIX + came_from, "%s of item %s triggered" % ("Refresh" if not force else "Forced-refresh", rating_key)))

@route(PREFIX + '/missing/refresh')
def RefreshMissing():
    Thread.CreateTimer(1.0, searchAllRecentlyAddedMissing)
    return Redirect(encode_message(PREFIX, "Refresh of recently added items with missing subtitles triggered"))

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
    return Redirect(encode_message(PREFIX, "Restart triggered, please wait about 5 seconds"))

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
    return MessageContainer(
        'Success',
        'Subtitle Information Storage reset'
    )

@route(PREFIX + '/refresh_token')
def RefreshToken():
    result = refresh_plex_token()
    if result:
	msg = "Token successfully refreshed."
    else:
	msg = "Couldn't refresh the token, please check your credentials"
    
    return Redirect(encode_message(PREFIX, msg))