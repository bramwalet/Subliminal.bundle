# coding=utf-8

import logging
import re
import types
import os
from ignore import ignore_list
from helpers import is_recent, format_item, query_plex
from lib import Plex, get_intent
from config import config, IGNORE_FN

logger = logging.getLogger(__name__)

MI_KIND, MI_TITLE, MI_KEY, MI_DEEPER, MI_ITEM = 0, 1, 2, 3, 4

container_size_re = re.compile(ur'totalSize="(\d+)"')


def get_item(key):
    item_id = int(key)
    item_container = Plex["library"].metadata(item_id)

    item = list(item_container)[0]
    return item


def get_item_kind(item):
    return type(item).__name__


PLEX_API_TYPE_MAP = {
    "Show": "series",
    "Season": "season",
    "Episode": "episode",
    "Movie": "movie",
}


def get_item_kind_from_rating_key(key):
    item = get_item(key)
    return PLEX_API_TYPE_MAP[get_item_kind(item)]


def get_item_thumb(item):
    kind = get_item_kind(item)
    if kind == "Episode":
        return item.show.thumb
    elif kind == "Section":
        return item.art
    return item.thumb


def get_items_info(items):
    return items[0][MI_KIND], items[0][MI_DEEPER]


def get_kind(items):
    return items[0][MI_KIND]


def get_section_size(key):
    """
    quick query to determine the section size
    :param key:
    :return:
    """
    size = None
    url = "http://127.0.0.1:32400/library/sections/%s/all" % int(key)
    use_args = {
        "X-Plex-Container-Size": "0",
        "X-Plex-Container-Start": "0"
    }
    response = query_plex(url, use_args)
    matches = container_size_re.findall(response.content)
    if matches:
        size = int(matches[0])

    return size


def get_items(key="recently_added", base="library", value=None, flat=False, add_section_title=False):
    """
    try to handle all return types plex throws at us and return a generalized item tuple
    """
    items = []
    apply_value = None
    if value:
        if isinstance(value, types.ListType):
            apply_value = value
        else:
            apply_value = [value]
    result = getattr(Plex[base], key)(*(apply_value or []))

    for item in result:
        cls = getattr(getattr(item, "__class__"), "__name__")
        if hasattr(item, "scanner"):
            kind = "section"
        elif cls == "Directory":
            kind = "directory"
        else:
            kind = item.type

        # only return items for our enabled sections
        section_key = None
        if kind == "section":
            section_key = item.key
        else:
            if hasattr(item, "section_key"):
                section_key = getattr(item, "section_key")

        if section_key and section_key not in config.enabled_sections:
            continue

        if kind == "season":
            # fixme: i think this case is unused now
            if flat:
                # return episodes
                for child in item.children():
                    items.append(("episode", format_item(child, "show", parent=item, add_section_title=add_section_title), int(item.rating_key),
                                  False, child))
            else:
                # return seasons
                items.append(("season", item.title, int(item.rating_key), True, item))

        elif kind == "directory":
            items.append(("directory", item.title, item.key, True, item))

        elif kind == "section":
            if item.type in ['movie', 'show']:
                item.size = get_section_size(item.key)
                items.append(("section", item.title, int(item.key), True, item))

        elif kind == "episode":
            items.append(
                (kind, format_item(item, "show", parent=item.season, parent_title=item.show.title, section_title=item.section.title,
                                   add_section_title=add_section_title), int(item.rating_key), False, item))

        elif kind in ("movie", "artist", "photo"):
            items.append((kind, format_item(item, kind, section_title=item.section.title, add_section_title=add_section_title),
                          int(item.rating_key), False, item))

        elif kind == "show":
            items.append((
                kind, format_item(item, kind, section_title=item.section.title, add_section_title=add_section_title), int(item.rating_key), True,
                item))

    return items


def get_recently_added_items():
    items = get_items(key="recently_added")
    return filter(lambda x: is_recent(x[MI_ITEM].added_at), items)


def get_recent_items():
    """
    actually get the recent items, not limited like /library/recentlyAdded
    :return:
    """
    args = {
        "sort": "addedAt:desc",
        "X-Plex-Container-Start": "0",
        "X-Plex-Container-Size": "%s" % config.max_recent_items_per_library
    }

    episode_re = re.compile(ur'ratingKey="(?P<key>\d+)"'
                            ur'.+?grandparentRatingKey="(?P<parent_key>\d+)"'
                            ur'.+?title="(?P<title>.*?)"'
                            ur'.+?grandparentTitle="(?P<parent_title>.*?)"'
                            ur'.+?index="(?P<episode>\d+?)"'
                            ur'.+?parentIndex="(?P<season>\d+?)".+?addedAt="(?P<added>\d+)"')
    movie_re = re.compile(ur'ratingKey="(?P<key>\d+)".+?title="(?P<title>.*?)".+?addedAt="(?P<added>\d+)"')
    available_keys = ("key", "title", "parent_key", "parent_title", "season", "episode", "added")
    recent = []

    for section in Plex["library"].sections():
        if section.type not in ("movie", "show") \
                or section.key not in config.enabled_sections \
                or section.key in ignore_list.sections:
            Log.Debug(u"Skipping section: %s" % section.title)
            continue

        use_args = args.copy()
        if section.type == "show":
            use_args["type"] = "4"

        url = "http://127.0.0.1:32400/library/sections/%s/all" % int(section.key)
        response = query_plex(url, use_args)

        matcher = episode_re if section.type == "show" else movie_re
        matches = [m.groupdict() for m in matcher.finditer(response.content)]
        for match in matches:
            data = dict((key, match[key] if key in match else None) for key in available_keys)
            if section.type == "show" and data["parent_key"] in ignore_list.series:
                Log.Debug(u"Skipping series: %s" % data["parent_title"])
                continue
            if data["key"] in ignore_list.videos:
                Log.Debug(u"Skipping item: %s" % data["title"])
                continue
            if is_recent(int(data["added"])):
                recent.append((int(data["added"]), section.type, section.title, data["key"]))

    return recent


def get_on_deck_items():
    return get_items(key="on_deck", add_section_title=True)


def get_all_items(key, base="library", value=None, flat=False):
    return get_items(key, base=base, value=value, flat=flat)


def is_ignored(rating_key, item=None):
    """
    check whether an item, its show/season/section is in the soft or the hard ignore list
    :param rating_key:
    :param item:
    :return:
    """
    # item in soft ignore list
    if rating_key in ignore_list["videos"]:
        Log.Debug("Item %s is in the soft ignore list" % rating_key)
        return True

    item = item or get_item(rating_key)
    kind = get_item_kind(item)

    # show in soft ignore list
    if kind == "Episode" and item.show.rating_key in ignore_list["series"]:
        Log.Debug("Item %s's show is in the soft ignore list" % rating_key)
        return True

    # section in soft ignore list
    if item.section.key in ignore_list["sections"]:
        Log.Debug("Item %s's section is in the soft ignore list" % rating_key)
        return True

    # physical/path ignore
    if Prefs["subtitles.ignore_fs"] or config.ignore_paths:
        # normally check current item folder and the library
        check_ignore_paths = [".", "../"]
        if kind == "Episode":
            # series/episode, we've got a season folder here, also
            check_ignore_paths.append("../../")

        for part in item.media.parts:
            if config.ignore_paths and config.is_path_ignored(part.file):
                Log.Debug("Item %s's path is manually ignored" % rating_key)
                return True

            if Prefs["subtitles.ignore_fs"]:
                for sub_path in check_ignore_paths:
                    if config.is_physically_ignored(os.path.abspath(os.path.join(os.path.dirname(part.file), sub_path))):
                        Log.Debug("An ignore file exists in either the items or its parent folders")
                        return True

    return False


def refresh_item(rating_key, force=False, timeout=8000, refresh_kind=None, parent_rating_key=None):
    intent = get_intent()

    # timeout actually is the time for which the intent will be valid
    if force:
        Log.Debug("Setting intent for force-refresh of %s to timeout: %s", rating_key, timeout)
        intent.set("force", rating_key, timeout=timeout)

        # force Dict.Save()
        intent.store.save()

    refresh = [rating_key]

    if refresh_kind == "season":
        # season refresh, needs explicit per-episode refresh
        refresh = [item.rating_key for item in list(Plex["library/metadata"].children(int(rating_key)))]

    for key in refresh:
        Log.Info("%s item %s", "Refreshing" if not force else "Forced-refreshing", key)
        Plex["library/metadata"].refresh(key)
