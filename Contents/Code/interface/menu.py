# coding=utf-8

from subzero import restart, intent
from subzero.constants import TITLE, ART, ICON, PREFIX, PLUGIN_IDENTIFIER
from support.config import config
from support.helpers import pad_title, encode_message, decode_message
from support.storage import resetStorage
from support.items import getRecentlyAddedItems, getOnDeckItems, refreshItem

# init GUI
ObjectContainer.title1 = TITLE
ObjectContainer.art = R(ART)

@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def fatality(message=None):
    """
    subzero main menu
    """
    oc = ObjectContainer(header=decode_message(message) if message else None)
    oc.add(DirectoryObject(
        key=Callback(OnDeckMenu),
        title=pad_title("Items On Deck")
    ))
    oc.add(DirectoryObject(
        key=Callback(RecentlyAddedMenu),
        title=pad_title("Recently Added Items")
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
    oc = ObjectContainer(title1=title1, no_cache=True, header=decode_message(message) if message else None)
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

@route(PREFIX + '/advanced')
def AdvancedMenu():
    oc = ObjectContainer(header="Internal stuff, pay attention!")
    
    oc.add(DirectoryObject(
        key=Callback(TriggerRestart),
        title=pad_title("Restart the plugin")
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

@route(PREFIX + '/restart/trigger')
def TriggerRestart():
    Thread.CreateTimer(1.0, Restart)
    return Redirect(encode_message(PREFIX, "Restart triggered, please wait about 5 seconds"))

@route(PREFIX + '/restart/execute')
def Restart():
    restart(PLUGIN_IDENTIFIER)

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