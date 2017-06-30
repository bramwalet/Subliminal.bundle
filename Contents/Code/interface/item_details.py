# coding=utf-8
import os

from sub_mod import SubtitleModificationsMenu
from menu_helpers import debounce, SubFolderObjectContainer, default_thumb, add_ignore_options, get_item_task_data, \
    set_refresh_menu_state

from refresh_item import RefreshItem
from subzero.constants import PREFIX
from support.config import config
from support.helpers import timestamp, cast_bool, df, get_language
from support.items import get_item_kind_from_rating_key, get_item, get_current_sub
from support.lib import Plex
from support.plex_media import get_plex_metadata, scan_videos, PMSMediaProxy
from support.scheduler import scheduler
from support.storage import get_subtitle_storage


# fixme: needs kwargs cleanup

@route(PREFIX + '/item/{rating_key}/actions')
@debounce
def ItemDetailsMenu(rating_key, title=None, base_title=None, item_title=None, randomize=None):
    """
    displays the item details menu of an item that doesn't contain any deeper tree, such as a movie or an episode
    :param rating_key:
    :param title:
    :param base_title:
    :param item_title:
    :param randomize:
    :return:
    """
    from interface.main import IgnoreMenu

    title = unicode(base_title) + " > " + unicode(title) if base_title else unicode(title)
    item = get_item(rating_key)
    current_kind = get_item_kind_from_rating_key(rating_key)

    timeout = 30

    oc = SubFolderObjectContainer(title2=title, replace_parent=True)

    # add back to season for episode
    if current_kind == "episode":
        from interface.menu import MetadataMenu
        show = get_item(item.show.rating_key)
        season = get_item(item.season.rating_key)

        oc.add(DirectoryObject(
            key=Callback(MetadataMenu, rating_key=season.rating_key, title=season.title, base_title=show.title,
                         previous_item_type="show", previous_rating_key=show.rating_key,
                         display_items=True, randomize=timestamp()),
            title=u"< Back to %s" % season.title,
            summary="Back to %s > %s" % (show.title, season.title),
            thumb=season.thumb or default_thumb
        ))

    oc.add(DirectoryObject(
        key=Callback(RefreshItem, rating_key=rating_key, item_title=item_title, randomize=timestamp(),
                     timeout=timeout * 1000),
        title=u"Refresh: %s" % item_title,
        summary="Refreshes the %s, possibly searching for missing and picking up new subtitles on disk" % current_kind,
        thumb=item.thumb or default_thumb
    ))
    oc.add(DirectoryObject(
        key=Callback(RefreshItem, rating_key=rating_key, item_title=item_title, force=True, randomize=timestamp(),
                     timeout=timeout * 1000),
        title=u"Force-find subtitles: %s" % item_title,
        summary="Issues a forced refresh, ignoring known subtitles and searching for new ones",
        thumb=item.thumb or default_thumb
    ))

    # get stored subtitle info for item id
    subtitle_storage = get_subtitle_storage()
    stored_subs = subtitle_storage.load_or_new(item)

    # get the plex item
    plex_item = get_item(rating_key)

    # look for subtitles for all available media parts and all of their languages
    has_multiple_parts = len(plex_item.media) > 1
    part_index = 0
    for media in plex_item.media:
        for part in media.parts:
            filename = os.path.basename(part.file)
            if not os.path.exists(part.file):
                continue

            part_id = str(part.id)
            part_index += 1

            # iterate through all configured languages
            for lang in config.lang_list:
                # get corresponding stored subtitle data for that media part (physical media item), for language
                current_sub = stored_subs.get_any(part_id, lang)
                current_sub_id = None
                current_sub_provider_name = None

                part_index_addon = ""
                part_summary_addon = ""
                if has_multiple_parts:
                    part_index_addon = u"File %s: " % part_index
                    part_summary_addon = "%s " % filename

                summary = u"%sNo current subtitle in storage" % part_summary_addon
                current_score = None
                if current_sub:
                    current_sub_id = current_sub.id
                    current_sub_provider_name = current_sub.provider_name
                    current_score = current_sub.score

                    summary = u"%sCurrent subtitle: %s (added: %s, %s), Language: %s, Score: %i, Storage: %s" % \
                              (part_summary_addon, current_sub.provider_name, df(current_sub.date_added),
                               current_sub.mode_verbose, lang, current_sub.score, current_sub.storage_type)

                    oc.add(DirectoryObject(
                        key=Callback(SubtitleOptionsMenu, rating_key=rating_key, part_id=part_id, title=title,
                                     item_title=item_title, language=lang, language_name=lang.name,
                                     current_id=current_sub_id,
                                     item_type=plex_item.type, filename=filename, current_data=summary,
                                     randomize=timestamp(), current_provider=current_sub_provider_name,
                                     current_score=current_score),
                        title=u"%sActions for %s subtitle" % (part_index_addon, lang.name),
                        summary=summary
                    ))
                else:
                    oc.add(DirectoryObject(
                        key=Callback(ListAvailableSubsForItemMenu, rating_key=rating_key, part_id=part_id, title=title,
                                     item_title=item_title, language=lang, language_name=lang.name,
                                     current_id=current_sub_id,
                                     item_type=plex_item.type, filename=filename, current_data=summary,
                                     randomize=timestamp(), current_provider=current_sub_provider_name,
                                     current_score=current_score),
                        title=u"%sList %s subtitles" % (part_index_addon, lang.name),
                        summary=summary
                    ))

    add_ignore_options(oc, "videos", title=item_title, rating_key=rating_key, callback_menu=IgnoreMenu)

    return oc


@route(PREFIX + '/item/current_sub/{rating_key}/{part_id}', force=bool)
@debounce
def SubtitleOptionsMenu(**kwargs):
    oc = SubFolderObjectContainer(title2=kwargs["title"], replace_parent=True)
    rating_key = kwargs["rating_key"]
    part_id = kwargs["part_id"]
    language = kwargs["language"]

    current_sub, stored_subs, storage = get_current_sub(rating_key, part_id, language)
    kwargs.pop("randomize")

    oc.add(DirectoryObject(
        key=Callback(ItemDetailsMenu, rating_key=kwargs["rating_key"], item_title=kwargs["item_title"],
                     title=kwargs["title"], randomize=timestamp()),
        title=u"< Back to %s" % kwargs["title"],
        summary=kwargs["current_data"],
        thumb=default_thumb
    ))
    oc.add(DirectoryObject(
        key=Callback(ListAvailableSubsForItemMenu, randomize=timestamp(), **kwargs),
        title=u"List %s subtitles" % kwargs["language_name"],
        summary=kwargs["current_data"]
    ))
    if current_sub:
        oc.add(DirectoryObject(
            key=Callback(SubtitleModificationsMenu, randomize=timestamp(), **kwargs),
            title=u"Modify %s subtitle" % kwargs["language_name"],
            summary=u"Currently applied mods: %s" % (", ".join(current_sub.mods) if current_sub.mods else "none")
        ))
    return oc


@route(PREFIX + '/item/search/{rating_key}/{part_id}', force=bool)
@debounce
def ListAvailableSubsForItemMenu(rating_key=None, part_id=None, title=None, item_title=None, filename=None,
                                 item_type="episode", language=None, language_name=None, force=False, current_id=None,
                                 current_data=None,
                                 current_provider=None, current_score=None, randomize=None):
    assert rating_key, part_id

    running = scheduler.is_task_running("AvailableSubsForItem")
    search_results = get_item_task_data("AvailableSubsForItem", rating_key, language)

    if (search_results is None or force) and not running:
        scheduler.dispatch_task("AvailableSubsForItem", rating_key=rating_key, item_type=item_type, part_id=part_id,
                                language=language)
        running = True

    oc = SubFolderObjectContainer(title2=unicode(title), replace_parent=True)
    oc.add(DirectoryObject(
        key=Callback(ItemDetailsMenu, rating_key=rating_key, item_title=item_title, title=title, randomize=timestamp()),
        title=u"< Back to %s" % title,
        summary=current_data,
        thumb=default_thumb
    ))

    metadata = get_plex_metadata(rating_key, part_id, item_type)
    scanned_parts = scan_videos([metadata], kind="series" if item_type == "episode" else "movie", ignore_all=True)

    if not scanned_parts:
        Log.Error("Couldn't list available subtitles for %s", rating_key)
        return oc

    video, plex_part = scanned_parts.items()[0]

    video_display_data = [video.format] if video.format else []
    if video.release_group:
        video_display_data.append(u"by %s" % video.release_group)
    video_display_data = " ".join(video_display_data)

    current_display = (u"Current: %s (%s) " % (current_provider, current_score) if current_provider else "")
    if not running:
        oc.add(DirectoryObject(
            key=Callback(ListAvailableSubsForItemMenu, rating_key=rating_key, item_title=item_title, language=language,
                         filename=filename, part_id=part_id, title=title, current_id=current_id, force=True,
                         current_provider=current_provider, current_score=current_score,
                         current_data=current_data, item_type=item_type, randomize=timestamp()),
            title=u"Search for %s subs (%s)" % (get_language(language).name, video_display_data),
            summary=u"%sFilename: %s" % (current_display, filename),
            thumb=default_thumb
        ))

        if search_results == "found_none":
            oc.add(DirectoryObject(
                key=Callback(ListAvailableSubsForItemMenu, rating_key=rating_key, item_title=item_title,
                             language=language, filename=filename, current_data=current_data, force=True,
                             part_id=part_id, title=title, current_id=current_id, item_type=item_type,
                             current_provider=current_provider, current_score=current_score,
                             randomize=timestamp()),
                title=u"No subtitles found",
                summary=u"%sFilename: %s" % (current_display, filename),
                thumb=default_thumb
            ))
    else:
        oc.add(DirectoryObject(
            key=Callback(ListAvailableSubsForItemMenu, rating_key=rating_key, item_title=item_title,
                         language=language, filename=filename, current_data=current_data,
                         part_id=part_id, title=title, current_id=current_id, item_type=item_type,
                         current_provider=current_provider, current_score=current_score,
                         randomize=timestamp()),
            title=u"Searching for %s subs (%s), refresh here ..." % (get_language(language).name, video_display_data),
            summary=u"%sFilename: %s" % (current_display, filename),
            thumb=default_thumb
        ))

    if not search_results or search_results == "found_none":
        return oc

    seen = []
    for subtitle in search_results:
        if subtitle.id in seen:
            continue

        wrong_fps_addon = ""
        if subtitle.wrong_fps:
            wrong_fps_addon = " (wrong FPS, sub: %s, media: %s)" % (subtitle.fps, plex_part.fps)

        oc.add(DirectoryObject(
            key=Callback(TriggerDownloadSubtitle, rating_key=rating_key, randomize=timestamp(), item_title=item_title,
                         subtitle_id=str(subtitle.id), language=language),
            title=u"%s: %s, score: %s%s" % ("Available" if current_id != subtitle.id else "Current",
                                            subtitle.provider_name, subtitle.score, wrong_fps_addon),
            summary=u"Release: %s, Matches: %s" % (subtitle.release_info, ", ".join(subtitle.matches)),
            thumb=default_thumb
        ))

        seen.append(current_id)

    return oc


@route(PREFIX + '/download_subtitle/{rating_key}')
@debounce
def TriggerDownloadSubtitle(rating_key=None, subtitle_id=None, item_title=None, language=None, randomize=None):
    from interface.main import fatality

    set_refresh_menu_state("Downloading subtitle for %s" % item_title or rating_key)
    search_results = get_item_task_data("AvailableSubsForItem", rating_key, language)

    download_subtitle = None
    for subtitle in search_results:
        if str(subtitle.id) == subtitle_id:
            download_subtitle = subtitle
            break
    if not download_subtitle:
        Log.Error(u"Something went horribly wrong")

    else:
        scheduler.dispatch_task("DownloadSubtitleForItem", rating_key=rating_key, subtitle=download_subtitle)

    return fatality(randomize=timestamp(), header=" ", replace_parent=True)
