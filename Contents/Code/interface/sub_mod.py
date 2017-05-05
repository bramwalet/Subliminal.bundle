# coding=utf-8

import traceback
import types

from babelfish import Language

from menu_helpers import debounce, SubFolderObjectContainer
from subliminal_patch import PatchedSubtitle as Subtitle
from subzero.modification import registry as mod_registry, SubtitleModifications
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
        if mod.advanced:
            continue

        if mod.exclusive and identifier in current_sub.mods:
            continue

        oc.add(DirectoryObject(
            key=Callback(SubtitleSetMods, mods=identifier, mode="add", randomize=timestamp(), **kwargs),
            title=pad_title(mod.description), summary=mod.long_description or ""
        ))

    fps_mod = SubtitleModifications.get_mod_class("change_FPS")
    oc.add(DirectoryObject(
        key=Callback(SubtitleFPSModMenu, randomize=timestamp(), **kwargs),
        title=pad_title(fps_mod.description), summary=fps_mod.long_description or ""
    ))

    shift_mod = SubtitleModifications.get_mod_class("shift_offset")
    oc.add(DirectoryObject(
        key=Callback(SubtitleShiftModUnitMenu, randomize=timestamp(), **kwargs),
        title=pad_title(shift_mod.description), summary=shift_mod.long_description or ""
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


@route(PREFIX + '/item/sub_mod_fps/{rating_key}/{part_id}', force=bool)
@debounce
def SubtitleFPSModMenu(**kwargs):
    rating_key = kwargs["rating_key"]
    part_id = kwargs["part_id"]
    item_type = kwargs["item_type"]

    oc = SubFolderObjectContainer(title2=kwargs["title"], replace_parent=True)

    metadata = get_plex_metadata(rating_key, part_id, item_type)
    scanned_parts = scan_videos([metadata], kind="series" if item_type == "episode" else "movie", ignore_all=True)
    video, plex_part = scanned_parts.items()[0]

    target_fps = plex_part.fps

    kwargs.pop("randomize")

    for fps in ["23.976", "24.000", "25.000", "29.970", "50.000", "59.940", "60.000"]:
        if fps == str(target_fps):
            continue

        mod_ident = SubtitleModifications.get_mod_signature("change_FPS", **{"from": fps, "to": target_fps})
        oc.add(DirectoryObject(
            key=Callback(SubtitleSetMods, mods=mod_ident, mode="add", randomize=timestamp(), **kwargs),
            title="%s fps -> %s fps" % (fps, target_fps)
        ))

    return oc


POSSIBLE_UNITS = (("ms", "milliseconds"), ("s", "seconds"), ("m", "minutes"), ("h", "hours"))
POSSIBLE_UNITS_D = dict(POSSIBLE_UNITS)


@route(PREFIX + '/item/sub_mod_shift_unit/{rating_key}/{part_id}', force=bool)
@debounce
def SubtitleShiftModUnitMenu(**kwargs):
    oc = SubFolderObjectContainer(title2=kwargs["title"], replace_parent=True)

    kwargs.pop("randomize")

    for unit, title in POSSIBLE_UNITS:
        oc.add(DirectoryObject(
            key=Callback(SubtitleShiftModMenu, unit=unit, randomize=timestamp(), **kwargs),
            title="Adjust by %s" % title
        ))

    return oc


@route(PREFIX + '/item/sub_mod_shift/{rating_key}/{part_id}/{unit}', force=bool)
@debounce
def SubtitleShiftModMenu(unit=None, **kwargs):
    if unit not in POSSIBLE_UNITS_D:
        raise NotImplementedError

    oc = SubFolderObjectContainer(title2=kwargs["title"], replace_parent=True)

    kwargs.pop("randomize")

    unit_title = POSSIBLE_UNITS_D[unit]

    rng = []
    if unit == "h":
        rng = range(-10, 11)
    elif unit in ("m", "s"):
        rng = range(-59, 60)
    elif unit == "ms":
        rng = range(-900, 1000, 100)

    for i in rng:
        if i == 0:
            continue

        mod_ident = SubtitleModifications.get_mod_signature("shift_offset", **{unit: i})
        oc.add(DirectoryObject(
            key=Callback(SubtitleSetMods, mods=mod_ident, mode="add", randomize=timestamp(), **kwargs),
            title="%s %s" % (("%s" if i < 0 else "+%s") % i, unit)
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
            identifier, args = SubtitleModifications.parse_identifier(mod)
            if identifier not in mod_registry.mods_available:
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
