# coding=utf-8

import traceback
import types

from babelfish import Language

from menu_helpers import debounce, SubFolderObjectContainer
from subliminal_patch import PatchedSubtitle as Subtitle
from subzero.modification import registry as mod_registry
from subzero.constants import PREFIX
from support.plex_media import get_plex_metadata, scan_videos
from support.storage import save_subtitles
from support.helpers import timestamp, pad_title
from support.items import get_current_sub


@route(PREFIX + '/item/sub_mods/{rating_key}/{part_id}', force=bool)
@debounce
def SubtitleModificationsMenu(**kwargs):
    rating_key = kwargs["rating_key"]
    part_id = kwargs["part_id"]
    language = kwargs["language"]
    current_sub, stored_subs, storage = get_current_sub(rating_key, part_id, language)
    kwargs.pop("randomize")

    oc = SubFolderObjectContainer(title2=kwargs["title"], replace_parent=True)
    for identifier, mod in mod_registry.mods.iteritems():
        oc.add(DirectoryObject(
            key=Callback(SubtitleSetMods, mods=identifier, mode="add", randomize=timestamp(), **kwargs),
            title=pad_title(mod.description), summary=mod.long_description or ""
        ))

    if current_sub.mods:
        oc.add(DirectoryObject(
            key=Callback(SubtitleSetMods, mods=None, mode="remove_last", randomize=timestamp(), **kwargs),
            title=pad_title("Remove last applied mod (%s)" % current_sub.mods[-1]),
            summary=u"Currently applied mods: %s" % (", ".join(current_sub.mods) if current_sub.mods else "none")
        ))

    oc.add(DirectoryObject(
        key=Callback(SubtitleSetMods, mods=None, mode="clear", randomize=timestamp(), **kwargs),
        title=pad_title("Restore original version"),
        summary=u"Currently applied mods: %s" % (", ".join(current_sub.mods) if current_sub.mods else "none")
    ))

    return oc


@route(PREFIX + '/item/sub_set_mods/{rating_key}/{part_id}/{mods}/{mode}', force=bool)
@debounce
def SubtitleSetMods(mods=None, mode=None, **kwargs):
    if not isinstance(mods, types.ListType) and mods:
        mods = [mods]

    rating_key = kwargs["rating_key"]
    part_id = kwargs["part_id"]
    lang_a2 = kwargs["language"]
    item_type = kwargs["item_type"]

    language = Language.fromietf(lang_a2)

    current_sub, stored_subs, storage = get_current_sub(rating_key, part_id, language)
    if mode == "add":
        for mod in mods:
            if mod not in mod_registry.mods_available:
                raise NotImplementedError("Mod unknown or not registered")

            current_sub.add_mod(mod)
    elif mode == "clear":
        current_sub.add_mod(None)
    elif mode == "remove_last":
        if current_sub.mods:
            current_sub.mods.pop()
    else:
        raise NotImplementedError("Wrong mode given")
    storage.save(stored_subs)

    metadata = get_plex_metadata(rating_key, part_id, item_type)
    scanned_parts = scan_videos([metadata], kind="series" if item_type == "episode" else "movie", ignore_all=True)
    video, plex_part = scanned_parts.items()[0]

    subtitle = Subtitle(language, mods=current_sub.mods)
    subtitle.content = current_sub.content
    subtitle.plex_media_fps = plex_part.fps
    subtitle.page_link = "modify subtitles with: %s" % (", ".join(current_sub.mods) if current_sub.mods else "none")
    subtitle.language = language

    try:
        save_subtitles(scanned_parts, {video: [subtitle]}, mode="m", bare_save=True)
        Log.Debug("Modified %s subtitle for: %s:%s with: %s", language.name, rating_key, part_id,
                  ", ".join(current_sub.mods) if current_sub.mods else "none")
    except:
        Log.Error("Something went wrong when modifying subtitle: %s", traceback.format_exc())

    kwargs.pop("randomize")
    return SubtitleModificationsMenu(randomize=timestamp(), **kwargs)
