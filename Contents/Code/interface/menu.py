# coding=utf-8

from subzero import restart
from subzero.constants import TITLE, ART, ICON, PREFIX, PLUGIN_IDENTIFIER
from support.config import config
from support.helpers import pad_title
from support.storage import resetStorage

# init GUI
ObjectContainer.title1 = TITLE
ObjectContainer.art = R(ART)


@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def fatality():
    """
    subzero main menu
    """
    oc = ObjectContainer()
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
    Thread.Create(Restart)
    return MessageContainer(
        'Success',
        'Restart triggered'
    )

@route(PREFIX + '/restart/execute')
def Restart():
    restart(PLUGIN_IDENTIFIER)

@route(PREFIX + '/storage/reset')
def ResetStorage(key):
    resetStorage(key)
    return MessageContainer(
        'Success',
        'Subtitle Information Storage reset'
    )