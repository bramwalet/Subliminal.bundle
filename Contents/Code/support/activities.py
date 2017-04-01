# coding=utf-8
from config import config
from plex_activity import Activity
from plex_activity.sources.s_logging.main import Logging as Activity_Logging


class PlexActivity(object):
    def start(self):
        activity_sources_enabled = None

        if config.universal_plex_token:
            from plex import Plex
            Plex.configuration.defaults.authentication(config.universal_plex_token)
            activity_sources_enabled = ["websocket"]
            Activity.on('websocket.playing', self.on_playing)

        elif config.server_log_path:
            Activity_Logging.add_hint(config.server_log_path, None)
            activity_sources_enabled = ["logging"]
            Activity.on('logging.playing', self.on_playing)

        if activity_sources_enabled:
            Activity.start(activity_sources_enabled)

    def on_playing(self, info, *args, **kwargs):
        if info["viewOffset"] / 60000 <= 2:
            print info, args, kwargs


activity = PlexActivity()
