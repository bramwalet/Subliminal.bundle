# coding=utf-8

import logging
import types
import os
import requests

from guessit import guessit
from requests.compat import urljoin, quote, urlsplit
from subliminal import Episode, Movie
from subliminal_patch.core import REMOVE_CRAP_FROM_FILENAME

logger = logging.getLogger(__name__)


class DroneAPIClient(object):
    api_url = None
    _fill_attrs = None

    def __init__(self, version=1, session=None, headers=None, timeout=10, base_url=None, api_key=None):
        headers = dict(headers or {}, **{"X-Api-Key": api_key})

        #: Session for the requests
        self.session = session or requests.Session()
        self.session.timeout = timeout
        self.session.headers.update(headers or {})

        if not base_url.endswith("/"):
            base_url += "/"

        self.api_url = urljoin(base_url, "api/")

    def get_guess(self, video, scene_name):
        raise NotImplemented

    def get_additional_data(self, video):
        raise NotImplemented

    def build_params(self, params):
        """
        quotes values and converts keys of params to camelCase from underscore
        :param params: dict
        :return:
        """
        out = {}
        for key, value in params.iteritems():
            if not isinstance(value, types.StringTypes):
                value = str(value)

            elif isinstance(value, unicode):
                value = value.encode("utf-8")

            key = key.split('_')[0] + ''.join(x.capitalize() for x in key.split('_')[1:])
            out[key] = quote(value)
        return out

    def get(self, endpoint, **params):
        url = urljoin(self.api_url, endpoint)
        params = self.build_params(params)

        # perform the request
        r = self.session.get(url, params=params)
        r.raise_for_status()

        # get the response as json
        j = r.json()

        # check response status
        if j:
            return j
        return []

    def update_video(self, video, scene_name):
        """
        update video attributes based on scene_name
        :param video:
        :param scene_name:
        :return:
        """
        scene_fn, guess = self.get_guess(video, scene_name)
        for attr in self._fill_attrs:
            if attr in guess:
                value = guess.get(attr)
                logger.debug(u"%s: Filling attribute %s: %s", video.name, attr, value)
                setattr(video, attr, value)

        video.name = scene_fn


class SonarrClient(DroneAPIClient):
    needs_attrs_to_work = ("series", "season", "episode",)
    _fill_attrs = ("release_group", "format",)
    cfg_name = "sonarr"

    def __init__(self, base_url="http://127.0.0.1:8989/", **kwargs):
        super(SonarrClient, self).__init__(base_url=base_url, **kwargs)

    def get_additional_data(self, video):
        for attr in self.needs_attrs_to_work:
            if getattr(video, attr, None) is None:
                logger.debug(u"%s: Not enough data available for Sonarr", video.name)
                return

        found_show_id = None
        for show in self.get("series"):
            if show["title"] == video.series or (video.series_tvdb_id and show["tvdbId"] == video.series_tvdb_id):
                found_show_id = show["id"]
                break

        if not found_show_id:
            logger.debug(u"%s: Show not found in Sonarr: %s", video.name, video.series)
            return

        for episode in self.get("episode", series_id=found_show_id):
            if episode["seasonNumber"] == video.season and episode["episodeNumber"] == video.episode:
                scene_name = episode.get("episodeFile", {}).get("sceneName")
                if scene_name:
                    logger.debug(u"%s: Got original filename from Sonarr: %s", video.name, scene_name)
                    return {"scene_name": scene_name}

    def get_guess(self, video, scene_name):
        """
        run guessit on scene_name
        :param video:
        :param scene_name:
        :return:
        """
        ext = os.path.splitext(video.name)[1]
        guess_from = REMOVE_CRAP_FROM_FILENAME.sub(r"\2", scene_name + ext)

        # guess
        hints = {
            "single_value": True,
            "type": "episode",
        }

        return guess_from, guessit(guess_from, options=hints)


class RadarrClient(DroneAPIClient):
    needs_attrs_to_work = ("title",)
    _fill_attrs = ("release_group", "format",)
    cfg_name = "radarr"

    def __init__(self, base_url="http://127.0.0.1:7878/", **kwargs):
        super(RadarrClient, self).__init__(base_url=base_url, **kwargs)

    def get_additional_data(self, video):
        for attr in self.needs_attrs_to_work:
            if getattr(video, attr, None) is None:
                logger.debug(u"%s: Not enough data available for Radarr")
                return

        movie_fn = os.path.basename(video.name)
        for movie in self.get("movie"):
            movie_file = movie.get("movieFile", {})
            if movie["title"] == video.title or (video.imdb_id and movie["imdbId"] == video.imdb_id)\
                    or movie_file.get("relativePath") == movie_fn:
                scene_name = movie_file.get("sceneName")
                release_group = movie_file.get("releaseGroup")

                additional_data = {}
                if scene_name:
                    logger.debug(u"%s: Got original filename from Radarr: %s", movie_fn, scene_name)
                    additional_data["scene_name"] = scene_name

                if release_group:
                    logger.debug(u"%s: Got release group from Radarr: %s", movie_fn, release_group)
                    additional_data["release_group"] = release_group

                return additional_data

    def get_guess(self, video, scene_name):
        """
        run guessit on scene_name
        :param video:
        :param scene_name:
        :return:
        """
        ext = os.path.splitext(video.name)[1]
        guess_from = REMOVE_CRAP_FROM_FILENAME.sub(r"\2", scene_name + ext)

        # guess
        hints = {
            "single_value": True,
            "type": "movie",
        }

        return guess_from, guessit(guess_from, options=hints)


class DroneManager(object):
    registry = {
        Episode: SonarrClient,
        Movie: RadarrClient,
    }

    @classmethod
    def get_client(cls, video, cfg_kwa):
        media_type = type(video)
        client_cls = cls.registry.get(media_type)
        if not client_cls:
            raise NotImplementedError("Media type not supported: %s", media_type)

        return client_cls(**cfg_kwa[client_cls.cfg_name])


def refine(video, **kwargs):
    """

    :param video:
    :param embedded_subtitles:
    :param kwargs:
    :return:
    """

    client = DroneManager.get_client(video, kwargs)

    additional_data = client.get_additional_data(video)
    if "scene_name" in additional_data:
        client.update_video(video, additional_data["scene_name"])

    if "release_group" in additional_data and not video.release_group:
        video.release_group = REMOVE_CRAP_FROM_FILENAME.sub(r"\2", additional_data["release_group"])
