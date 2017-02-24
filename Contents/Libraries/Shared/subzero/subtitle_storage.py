# coding=utf-8
import datetime
import hashlib
import os
import logging

from constants import mode_map

logger = logging.getLogger(__name__)


class StoredSubtitle(object):
    score = None
    storage_type = None
    hash = None
    provider_name = None
    id = None
    date_added = None
    mode = "a"  # auto/manual/auto-better (a/m/b)
    content = None

    def __init__(self, score, storage_type, hash, provider_name, id, date_added=None, mode="a", content=None):
        self.score = int(score)
        self.storage_type = storage_type
        self.hash = hash
        self.provider_name = provider_name
        self.id = id
        self.date_added = date_added or datetime.datetime.now()
        self.mode = mode
        self.content = content

    @property
    def mode_verbose(self):
        return mode_map.get(self.mode, "Unknown")


class StoredVideoSubtitles(object):
    """
    manages stored subtitles for video_id per media_part/language combination
    """
    video_id = None  # rating_key
    title = None
    parts = None
    version = None
    item_type = None  # movie / episode
    added_at = None

    def __init__(self, plex_item, version=None):
        self.video_id = str(plex_item.rating_key)

        self.title = plex_item.title
        self.parts = {}
        self.version = version
        self.item_type = plex_item.type
        self.added_at = datetime.datetime.fromtimestamp(plex_item.added_at)

    def add(self, part_id, lang, subtitle, storage_type, date_added=None, mode="a"):
        part_id = str(part_id)
        part = self.parts.get(part_id)
        if not part:
            self.parts[part_id] = {}
            part = self.parts[part_id]

        subs = part.get(lang)
        if not subs:
            part[lang] = {}
            subs = part[lang]

        sub_key = self.get_sub_key(subtitle.provider_name, subtitle.id)
        if sub_key in subs:
            return

        subs[sub_key] = StoredSubtitle(subtitle.score, storage_type, hashlib.md5(subtitle.content).hexdigest(),
                                       subtitle.provider_name, subtitle.id, date_added=date_added, mode=mode,
                                       content=subtitle.content)
        subs["current"] = sub_key

        return True

    def get_any(self, part_id, lang):
        part_id = str(part_id)
        part = self.parts.get(part_id)
        if not part:
            return

        subs = part.get(lang)
        if not subs:
            return

        if "current" in subs and subs["current"]:
            return subs.get(subs["current"])

    def get_sub_key(self, provider_name, id):
        return provider_name, str(id)

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return u"%s (%s)" % (self.title, self.video_id)

    def __str__(self):
        return str(self.video_id)


class StoredSubtitlesManager(object):
    """
    manages the storage and retrieval of StoredVideoSubtitles instances for a given video_id
    """
    storage = None
    version = 2

    def __init__(self, storage, plexapi_item_getter):
        self.storage = storage
        self.get_item = plexapi_item_getter

    def get_storage_filename(self, video_id):
        return "subs_%s" % video_id

    @property
    def dataitems_path(self):
        return os.path.join(getattr(self.storage, "_core").storage.data_path, "DataItems")

    def get_all_files(self):
        return os.listdir(self.dataitems_path)

    def get_recent_files(self, age_days=30):
        fl = []
        root = self.dataitems_path
        recent_dt = datetime.datetime.now() - datetime.timedelta(days=age_days)
        for fn in self.get_all_files():
            if not fn.startswith("subs_"):
                continue

            finfo = os.stat(os.path.join(root, fn))
            created = datetime.datetime.fromtimestamp(finfo.st_ctime)
            if created > recent_dt:
                fl.append(fn)
        return fl

    def load_recent_files(self, age_days=30):
        fl = self.get_recent_files(age_days=age_days)
        out = {}
        for fn in fl:
            out[fn] = self.load(filename=fn)
        return out

    def migrate_v2(self, subs_for_video):
        plex_item = self.get_item(subs_for_video.video_id)
        subs_for_video.item_type = plex_item.type
        subs_for_video.added_at = datetime.datetime.fromtimestamp(plex_item.added_at)
        subs_for_video.version = 2
        return True

    def load(self, video_id=None, filename=None):
        subs_for_video = self.storage.LoadObject(self.get_storage_filename(video_id) if video_id else filename)

        if not subs_for_video:
            return

        # apply possible migrations
        cur_ver = old_ver = subs_for_video.version

        if cur_ver < self.version:
            success = False
            while cur_ver < self.version:
                cur_ver += 1
                mig_func = "migrate_v%s" % cur_ver
                if hasattr(self, mig_func):
                    logger.info("Migrating subtitle storage for %s %s>%s" % (subs_for_video.video_id, old_ver, cur_ver))
                    success = getattr(self, mig_func)(subs_for_video)
                    if not success:
                        break

            if cur_ver > old_ver and success:
                logger.info("Storing migrated subtitle storage for %s" % subs_for_video.video_id)
                self.save(subs_for_video)
            elif not success:
                logger.info("Migration of %s %s>%s failed" % (subs_for_video.video_id, old_ver, cur_ver))

        return subs_for_video

    def load_or_new(self, plex_item):
        subs_for_video = self.load(plex_item.rating_key)
        if not subs_for_video:
            subs_for_video = StoredVideoSubtitles(plex_item, version=self.version)
            self.save(subs_for_video)
        return subs_for_video

    def save(self, subs_for_video):
        self.storage.SaveObject(self.get_storage_filename(subs_for_video.video_id), subs_for_video)
