# coding=utf-8
import datetime
import StringIO
import glob
import os
import urlparse

from zipfile import ZipFile, ZIP_DEFLATED

from subzero.lib.io import FileIO
from subzero.constants import PREFIX, PLUGIN_IDENTIFIER
from menu_helpers import SubFolderObjectContainer, debounce, set_refresh_menu_state, ZipObject
from main import fatality
from support.helpers import timestamp, pad_title
from support.config import config
from support.lib import Plex
from support.storage import reset_storage, log_storage
from support.scheduler import scheduler


@route(PREFIX + '/advanced')
def AdvancedMenu(randomize=None, header=None, message=None):
    oc = SubFolderObjectContainer(header=header or "Internal stuff, pay attention!", message=message, no_cache=True,
                                  no_history=True,
                                  replace_parent=False, title2="Advanced")

    if config.lock_advanced_menu and not config.pin_correct:
        oc.add(DirectoryObject(
            key=Callback(PinMenu, randomize=timestamp(), success_go_to="advanced"),
            title=pad_title("Enter PIN"),
            summary="The owner has restricted the access to this menu. Please enter the correct pin",
        ))
        return oc

    oc.add(DirectoryObject(
        key=Callback(TriggerRestart, randomize=timestamp()),
        title=pad_title("Restart the plugin"),
    ))
    oc.add(DirectoryObject(
        key=Callback(GetLogsLink),
        title="Get my logs (copy the appearing link and open it in your browser, please)",
        summary="Copy the appearing link and open it in your browser, please",
    ))
    oc.add(DirectoryObject(
        key=Callback(TriggerBetterSubtitles, randomize=timestamp()),
        title=pad_title("Trigger find better subtitles"),
    ))
    oc.add(DirectoryObject(
        key=Callback(TriggerStorageMaintenance, randomize=timestamp()),
        title=pad_title("Trigger subtitle storage maintenance"),
    ))
    oc.add(DirectoryObject(
        key=Callback(LogStorage, key="tasks", randomize=timestamp()),
        title=pad_title("Log the plugin's scheduled tasks state storage"),
    ))
    oc.add(DirectoryObject(
        key=Callback(LogStorage, key="ignore", randomize=timestamp()),
        title=pad_title("Log the plugin's internal ignorelist storage"),
    ))
    oc.add(DirectoryObject(
        key=Callback(ResetStorage, key="tasks", randomize=timestamp()),
        title=pad_title("Reset the plugin's scheduled tasks state storage"),
    ))
    oc.add(DirectoryObject(
        key=Callback(ResetStorage, key="ignore", randomize=timestamp()),
        title=pad_title("Reset the plugin's internal ignorelist storage"),
    ))
    oc.add(DirectoryObject(
        key=Callback(InvalidateCache, randomize=timestamp()),
        title=pad_title("Invalidate Sub-Zero metadata caches (subliminal)"),
    ))
    return oc


def DispatchRestart():
    Thread.CreateTimer(1.0, Restart)


@route(PREFIX + '/advanced/restart/trigger')
@debounce
def TriggerRestart(randomize=None):
    set_refresh_menu_state("Restarting the plugin")
    DispatchRestart()
    return fatality(header="Restart triggered, please wait about 5 seconds", force_title=" ", only_refresh=True,
                    replace_parent=True,
                    no_history=True, randomize=timestamp())


@route(PREFIX + '/advanced/restart/execute')
def Restart():
    Plex[":/plugins"].restart(PLUGIN_IDENTIFIER)


@route(PREFIX + '/storage/reset', sure=bool)
def ResetStorage(key, randomize=None, sure=False):
    if not sure:
        oc = SubFolderObjectContainer(no_history=True, title1="Reset subtitle storage", title2="Are you sure?")
        oc.add(DirectoryObject(
            key=Callback(ResetStorage, key=key, sure=True, randomize=timestamp()),
            title=pad_title("Are you really sure?"),

        ))
        return oc

    reset_storage(key)

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
    log_storage(key)
    return AdvancedMenu(
        randomize=timestamp(),
        header='Success',
        message='Information Storage (%s) logged' % key
    )


@route(PREFIX + '/triggerbetter')
def TriggerBetterSubtitles(randomize=None):
    scheduler.dispatch_task("FindBetterSubtitles")
    return AdvancedMenu(
        randomize=timestamp(),
        header='Success',
        message='FindBetterSubtitles triggered'
    )


@route(PREFIX + '/triggermaintenance')
def TriggerStorageMaintenance(randomize=None):
    scheduler.dispatch_task("SubtitleStorageMaintenance")
    return AdvancedMenu(
        randomize=timestamp(),
        header='Success',
        message='SubtitleStorageMaintenance triggered'
    )


@route(PREFIX + '/get_logs_link')
def GetLogsLink():
    if not config.universal_plex_token:
        oc = ObjectContainer(title2="Download Logs", no_cache=True, no_history=True,
                             header="Sorry, feature unavailable",
                             message="Universal Plex token not available on Windows at the moment")
        return oc

    # try getting the link base via the request in context, first, otherwise use the public ip
    req_headers = Core.sandbox.context.request.headers
    get_external_ip = True
    link_base = ""

    if "Origin" in req_headers:
        link_base = req_headers["Origin"]
        Log.Debug("Using origin-based link_base")
        get_external_ip = False

    elif "Referer" in req_headers:
        parsed = urlparse.urlparse(req_headers["Referer"])
        link_base = "%s://%s:%s" % (parsed.scheme, parsed.hostname, parsed.port)
        Log.Debug("Using referer-based link_base")
        get_external_ip = False

    if get_external_ip or "plex.tv" in link_base:
        ip = Core.networking.http_request("http://www.plexapp.com/ip.php", cacheTime=7200).content.strip()
        link_base = "https://%s:32400" % ip
        Log.Debug("Using ip-based fallback link_base")

    logs_link = "%s%s?X-Plex-Token=%s" % (link_base, PREFIX + '/logs', config.universal_plex_token)
    oc = ObjectContainer(title2="Download Logs", no_cache=True, no_history=True,
                         header="Copy this link and open this in your browser, please",
                         message=logs_link)
    return oc


@route(PREFIX + '/logs')
def DownloadLogs():
    buff = StringIO.StringIO()
    zip_archive = ZipFile(buff, mode='w', compression=ZIP_DEFLATED)

    logs = sorted(glob.glob(config.plugin_log_path + '*')) + [config.server_log_path]
    for path in logs:
        data = StringIO.StringIO()
        data.write(FileIO.read(path))
        zip_archive.writestr(os.path.basename(path), data.getvalue())

    zip_archive.close()

    return ZipObject(buff.getvalue())


@route(PREFIX + '/invalidatecache')
def InvalidateCache(randomize=None):
    from subliminal.cache import region
    region.invalidate()
    return AdvancedMenu(
        randomize=timestamp(),
        header='Success',
        message='Cache invalidated'
    )


@route(PREFIX + '/pin')
def PinMenu(pin="", randomize=None, success_go_to="channel"):
    oc = ObjectContainer(title2="Enter PIN number %s" % (len(pin) + 1), no_cache=True, no_history=True,
                         skip_pin_lock=True)

    if pin == config.pin:
        Dict["pin_correct_time"] = datetime.datetime.now()
        config.locked = False
        if success_go_to == "channel":
            return fatality(force_title="PIN correct", header="PIN correct", no_history=True)
        elif success_go_to == "advanced":
            return AdvancedMenu(randomize=timestamp())

    for i in range(10):
        oc.add(DirectoryObject(
            key=Callback(PinMenu, randomize=timestamp(), pin=pin + str(i), success_go_to=success_go_to),
            title=pad_title(str(i)),
        ))
    oc.add(DirectoryObject(
        key=Callback(PinMenu, randomize=timestamp(), success_go_to=success_go_to),
        title=pad_title("Reset"),
    ))
    return oc


@route(PREFIX + '/pin_lock')
def ClearPin(randomize=None):
    Dict["pin_correct_time"] = None
    config.locked = True
    return fatality(force_title="Menu locked", header=" ", no_history=True)
