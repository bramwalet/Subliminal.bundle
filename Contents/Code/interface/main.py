# coding=utf-8

from subzero.constants import PREFIX, TITLE, ART
from support.config import config
from support.helpers import pad_title, timestamp, df
from support.background import scheduler
from support.ignore import ignore_list
from advanced import PinMenu, ClearPin, AdvancedMenu


@handler(PREFIX, TITLE if not config.is_development else TITLE + " DEV", art=ART, thumb=main_icon)
@route(PREFIX)
def fatality(randomize=None, force_title=None, header=None, message=None, only_refresh=False, no_history=False,
             replace_parent=False):
    """
    subzero main menu
    """
    title = config.full_version  # force_title if force_title is not None else config.full_version
    oc = ObjectContainer(title1=title, title2=title, header=unicode(header) if header else title, message=message,
                         no_history=no_history,
                         replace_parent=replace_parent, no_cache=True)

    from menu import OnDeckMenu, RecentlyAddedMenu, RecentMissingSubtitlesMenu, SectionsMenu, RefreshMissing,\
        IgnoreListMenu, HistoryMenu

    # always re-check permissions
    config.refresh_permissions_status()

    # always re-check enabled sections
    config.refresh_enabled_sections()

    if config.lock_menu and not config.pin_correct:
        oc.add(DirectoryObject(
            key=Callback(PinMenu, randomize=timestamp()),
            title=pad_title("Enter PIN"),
            summary="The owner has restricted the access to this menu. Please enter the correct pin",
        ))
        return oc

    if not config.permissions_ok and config.missing_permissions:
        for title, path in config.missing_permissions:
            oc.add(DirectoryObject(
                key=Callback(fatality, randomize=timestamp()),
                title=pad_title("Insufficient permissions"),
                summary="Insufficient permissions on library %s, folder: %s" % (title, path),
            ))
        return oc

    if not config.enabled_sections:
        oc.add(DirectoryObject(
            key=Callback(fatality, randomize=timestamp()),
            title=pad_title("I'm not enabled!"),
            summary="Please enable me for some of your libraries in your server settings; currently I do nothing",
        ))
        return oc

    if not only_refresh:
        if Dict["current_refresh_state"]:
            oc.add(DirectoryObject(
                key=Callback(fatality, force_title=" ", randomize=timestamp()),
                title=pad_title("Working ... refresh here"),
                summary="Current state: %s; Last state: %s" % (
                    (Dict["current_refresh_state"] or "Idle") if "current_refresh_state" in Dict else "Idle",
                    (Dict["last_refresh_state"] or "None") if "last_refresh_state" in Dict else "None"
                )
            ))

        oc.add(DirectoryObject(
            key=Callback(OnDeckMenu),
            title="On Deck items",
            summary="Shows the current on deck items and allows you to individually (force-) refresh their metadata/"
                    "subtitles.",
            thumb=R("icon-ondeck.jpg")
        ))
        oc.add(DirectoryObject(
            key=Callback(RecentlyAddedMenu),
            title="Recently Added items",
            summary="Shows the recently added items per section.",
            thumb=R("icon-recent.jpg")
        ))
        oc.add(DirectoryObject(
            key=Callback(RecentMissingSubtitlesMenu, randomize=timestamp()),
            title="Items with missing subtitles",
            summary="Shows the items honoring the configured 'Item age to be considered recent'-setting (%s)"
                    " and allowing you to individually (force-) refresh their metadata/subtitles. " %
                    Prefs["scheduler.item_is_recent_age"],
            thumb=R("icon-missing.jpg")
        ))
        oc.add(DirectoryObject(
            key=Callback(SectionsMenu),
            title="Browse all items",
            summary="Go through your whole library and manage your ignore list. You can also "
                    "(force-) refresh the metadata/subtitles of individual items.",
            thumb=R("icon-browse.jpg")
        ))

        task_name = "SearchAllRecentlyAddedMissing"
        task = scheduler.task(task_name)

        if task.ready_for_display:
            task_state = "Running: %s/%s (%s%%)" % (len(task.items_done), len(task.items_searching), task.percentage)
        else:
            task_state = "Last scheduler run: %s; Next scheduled run: %s; Last runtime: %s" % (
                df(scheduler.last_run(task_name)) or "never",
                df(scheduler.next_run(task_name)) or "never",
                str(task.last_run_time).split(".")[0])

        oc.add(DirectoryObject(
            key=Callback(RefreshMissing, randomize=timestamp()),
            title="Search for missing subtitles (in recently-added items, max-age: %s)" % Prefs[
                "scheduler.item_is_recent_age"],
            summary="Automatically run periodically by the scheduler, if configured. %s" % task_state,
            thumb=R("icon-search.jpg")
        ))

        oc.add(DirectoryObject(
            key=Callback(IgnoreListMenu),
            title="Display ignore list (%d)" % len(ignore_list),
            summary="Show the current ignore list (mainly used for the automatic tasks)",
            thumb=R("icon-ignore.jpg")
        ))

        oc.add(DirectoryObject(
            key=Callback(HistoryMenu),
            title="History",
            summary="Show the last %i downloaded subtitles" % int(Prefs["history_size"]),
            thumb=R("icon-history.jpg")
        ))

    oc.add(DirectoryObject(
        key=Callback(fatality, force_title=" ", randomize=timestamp()),
        title=pad_title("Refresh"),
        summary="Current state: %s; Last state: %s" % (
            (Dict["current_refresh_state"] or "Idle") if "current_refresh_state" in Dict else "Idle",
            (Dict["last_refresh_state"] or "None") if "last_refresh_state" in Dict else "None"
        ),
        thumb=R("icon-refresh.jpg")
    ))

    # add re-lock after pin unlock
    if config.pin:
        oc.add(DirectoryObject(
            key=Callback(ClearPin, randomize=timestamp()),
            title=pad_title("Re-lock menu(s)"),
            summary="Enabled the PIN again for menu(s)"
        ))

    if not only_refresh:
        oc.add(DirectoryObject(
            key=Callback(AdvancedMenu),
            title=pad_title("Advanced functions"),
            summary="Use at your own risk",
            thumb=R("icon-advanced.jpg")
        ))

    return oc