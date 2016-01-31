# coding=utf-8

import os
import re
import inspect
from babelfish import Language
from subzero.lib.io import FileIO
from subzero.constants import PLUGIN_NAME
from auth import refresh_plex_token
from lib import configure_plex, Plex

SUBTITLE_EXTS = ['utf', 'utf8', 'utf-8', 'srt', 'smi', 'rt', 'ssa', 'aqt', 'jss', 'ass', 'idx', 'sub', 'txt', 'psb']
VIDEO_EXTS = ['3g2', '3gp', 'asf', 'asx', 'avc', 'avi', 'avs', 'bivx', 'bup', 'divx', 'dv', 'dvr-ms', 'evo', 'fli', 'flv',
              'm2t', 'm2ts', 'm2v', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'mts', 'nsv', 'nuv', 'ogm', 'ogv', 'tp',
              'pva', 'qt', 'rm', 'rmvb', 'sdp', 'svq3', 'strm', 'ts', 'ty', 'vdr', 'viv', 'vob', 'vp3', 'wmv', 'wpl', 'wtv', 'xsp', 'xvid',
              'webm']

VERSION_RE = re.compile(ur'CFBundleVersion.+?<string>([0-9\.]+)</string>', re.DOTALL)


def int_or_default(s, default):
    try:
        return int(s)
    except ValueError:
        return default


class Config(object):
    version = None
    langList = None
    subtitleDestinationFolder = None
    providers = None
    providerSettings = None
    max_recent_items_per_library = 200
    plex_api_working = False

    initialized = False

    def initialize(self):
        self.version = self.getVersion()
        self.full_version = u"%s %s" % (PLUGIN_NAME, self.version)
        self.langList = self.getLangList()
        self.subtitleDestinationFolder = self.getSubtitleDestinationFolder()
        self.providers = self.getProviders()
        self.providerSettings = self.getProviderSettings()
        self.max_recent_items_per_library = int_or_default(Prefs["scheduler.max_recent_items_per_library"], 200)
        self.initialized = True
        configure_plex()
        self.plex_api_working = self.checkPlexAPI()

    def checkPlexAPI(self):
        return bool(Plex["library"].sections())

    def getVersion(self):
        curDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        info_file_path = os.path.abspath(os.path.join(curDir, "..", "..", "Info.plist"))
        data = FileIO.read(info_file_path)
        result = VERSION_RE.search(data)
        if result:
            return result.group(1)

    def getBlacklist(self, key):
        return map(lambda id: id.strip(), (Prefs[key] or "").split(","))

    # Prepare a list of languages we want subs for
    def getLangList(self):
        l = {Language.fromietf(Prefs["langPref1"])}
        langCustom = Prefs["langPrefCustom"].strip()

        if Prefs["langPref2"] != "None":
            l.update({Language.fromietf(Prefs["langPref2"])})

        if Prefs["langPref3"] != "None":
            l.update({Language.fromietf(Prefs["langPref3"])})

        if len(langCustom) and langCustom != "None":
            for lang in langCustom.split(u","):
                lang = lang.strip()
                try:
                    real_lang = Language.fromietf(lang)
                except:
                    try:
                        real_lang = Language.fromname(lang)
                    except:
                        continue
                l.update({real_lang})

        return l

    def getSubtitleDestinationFolder(self):
        if not Prefs["subtitles.save.filesystem"]:
            return

        fld_custom = Prefs["subtitles.save.subFolder.Custom"].strip() if bool(Prefs["subtitles.save.subFolder.Custom"]) else None
        return fld_custom or (Prefs["subtitles.save.subFolder"] if Prefs["subtitles.save.subFolder"] != "current folder" else None)

    def getProviders(self):
        providers = {'opensubtitles': Prefs['provider.opensubtitles.enabled'],
                     #'thesubdb': Prefs['provider.thesubdb.enabled'],
                     'podnapisi': Prefs['provider.podnapisi.enabled'],
                     'addic7ed': Prefs['provider.addic7ed.enabled'],
                     'tvsubtitles': Prefs['provider.tvsubtitles.enabled']
                     }
        return filter(lambda prov: providers[prov], providers)

    def getProviderSettings(self):
        provider_settings = {'addic7ed': {'username': Prefs['provider.addic7ed.username'],
                                          'password': Prefs['provider.addic7ed.password'],
                                          'use_random_agents': Prefs['provider.addic7ed.use_random_agents'],
                                          },
                             'opensubtitles': {'username': Prefs['provider.opensubtitles.username'],
                                               'password': Prefs['provider.opensubtitles.password'],
                                               'use_tag_search': Prefs['provider.opensubtitles.use_tags']
                                               },
                             }

        return provider_settings


config = Config()
