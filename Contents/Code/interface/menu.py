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
ObjectContainer.art = R(ART)
ObjectContainer.no_history = True
ObjectContainer.no_cache = True


@handler(PREFIX, TITLE, art=ART, thumb=ICON)
@route(PREFIX)
def fatality(randomize=None, force_title=None, header=None, message=None, only_refresh=False):
    """
    subzero main menu
    """
    title = force_title if force_title is not None else config.full_version
    oc = ObjectContainer(title1=title, title2=None, header=header, message=message, no_cache=True, no_history=True)

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
                    " and allowing you to individually (force-) refresh their metadata/subtitles. " % Prefs["scheduler.item_is_recent_age"]
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
        key=Callback(fatality, force_title=" ", randomize=timestamp()),
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
    return mergedItemsMenu(title="Items On Deck", base_title="Items On Deck", itemGetter=getOnDeckItems)


@route(PREFIX + '/recent')
def RecentlyAddedMenu(message=None):
    return recentItemsMenu(title="Missing Subtitles", base_title="Missing Subtitles")


def recentItemsMenu(title, base_title=None):
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)
    recent_items = getRecentItems()
    if recent_items:
        missing_items = getAllMissing(recent_items)
        if missing_items:
            for added_at, item_id, title in missing_items:
                oc.add(DirectoryObject(
                    key=Callback(RefreshItemMenu, title=base_title + " > " + title, item_title=title, rating_key=item_id), title=title
                ))

    return oc


def mergedItemsMenu(title, itemGetter, itemGetterKwArgs=None, base_title=None, *args, **kwargs):
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)
    items = itemGetter(*args, **kwargs)

    for kind, title, item_id, deeper, item in items:
        oc.add(DirectoryObject(
            title=title,
            key=Callback(RefreshItemMenu, title=base_title + " > " + title, item_title=title, rating_key=item_id)
        ))

    return oc


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


def determine_section_display(kind, item):
    if item.size > 200:
        return SectionFirstLetterMenu
    return SectionMenu


@route(PREFIX + '/sections')
def SectionsMenu():
    items = getAllItems("sections")

    return dig_tree(ObjectContainer(title2="Sections", no_cache=True, no_history=True), items, None,
                    menu_determination_callback=determine_section_display, pass_kwargs={"base_title": "Sections"})


@route(PREFIX + '/section', deeper=bool)
def SectionMenu(rating_key, title=None, base_title=None, deeper=False):
    items = getAllItems(key="all", value=rating_key, base="library/sections", flat=not deeper)

    title = base_title + " > " + title
    return dig_tree(ObjectContainer(title2=title, no_cache=True, no_history=True), items, MetadataMenu, pass_kwargs={"base_title": title})


@route(PREFIX + '/section/firstLetter', deeper=bool)
def SectionFirstLetterMenu(rating_key, title=None, base_title=None, deeper=False):
    items = getAllItems(key="first_character", value=rating_key, base="library/sections", flat=not deeper)

    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)
    title = base_title + " > " + title

    oc.add(DirectoryObject(
            key=Callback(SectionMenu, title="All", base_title=title, rating_key=rating_key),
            title="All"
        )
    )
    return dig_tree(oc, items, FirstLetterMetadataMenu, force_rating_key=rating_key, pass_kwargs={"base_title": title})


@route(PREFIX + '/section/firstLetter/key', deeper=bool)
def FirstLetterMetadataMenu(rating_key, title=None, base_title=None, deeper=False):
    """

    :param rating_key: actually is the section's key
    :param key: the firstLetter wanted
    :param title: the first letter, or #
    :param deeper:
    :return:
    """
    item_title = title
    title = base_title + " > " + title
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)

    items = getAllItems(key="first_character", value=[rating_key, item_title], base="library/sections", flat=False)
    dig_tree(oc, items, MetadataMenu, pass_kwargs={"base_title": title})
    return oc


@route(PREFIX + '/section/contents', deeper=bool)
def MetadataMenu(rating_key, title=None, base_title=None, deeper=False):
    item_title = title
    title = base_title + " > " + title
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)

    if deeper:
        items = getAllItems(key="children", value=rating_key, base="library/metadata", flat=False)
        dig_tree(oc, items, MetadataMenu, pass_kwargs={"base_title": title})
    else:
        return RefreshItemMenu(rating_key=rating_key, title=title, item_title=item_title)

    return oc


@route(PREFIX + '/item/{rating_key}/actions')
def RefreshItemMenu(rating_key, title=None, base_title=None, item_title=None, came_from="/recent"):
    title = unicode(base_title) + " > " + unicode(title) if base_title else title
    oc = ObjectContainer(title2=title, no_cache=True, no_history=True)
    oc.add(DirectoryObject(
        key=Callback(RefreshItem, rating_key=rating_key),
        title="Refresh: %s" % item_title,
        summary="Refreshes the item, possibly picking up new subtitles on disk"
    ))
    oc.add(DirectoryObject(
        key=Callback(RefreshItem, rating_key=rating_key, force=True),
        title="Force-Refresh: %s" % item_title,
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
    return fatality(header="Restart triggered, please wait about 5 seconds", force_title=" ", only_refresh=True)


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
