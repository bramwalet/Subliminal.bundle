# coding=utf-8
import logging
import os

from subliminal.providers.argenteam import ArgenteamProvider as _ArgenteamProvider, \
    ArgenteamSubtitle as _ArgenteamSubtitle, json, ZipFile, io, sanitize, sanitize_release_group, \
    get_equivalent_release_groups, guess_matches, guessit, Session
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin

logger = logging.getLogger(__name__)


# fixme: add movie support

class ArgenteamSubtitle(_ArgenteamSubtitle):
    hearing_impaired_verifiable = False
    _release_info = None

    def __init__(self, language, download_link, series, season, episode, release, version, source, video_codec, tvdb_id,
                 asked_for_episode=None, asked_for_release_group=None, *args, **kwargs):
        super(ArgenteamSubtitle, self).__init__(language, download_link, series, season, episode, release, version,
                                                *args, **kwargs)

        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode
        self.matches = None
        self.format = source
        self.video_codec = video_codec
        self.tvdb_id = tvdb_id

    @property
    def release_info(self):
        if self._release_info:
            return self._release_info

        combine = []
        for attr in ("format", "version", "video_codec"):
            value = getattr(self, attr)
            if value:
                combine.append(value)

        self._release_info = u".".join(combine) + (u"-"+self.release if self.release else "")
        return self._release_info

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, self.release_info, self.language)

    def get_matches(self, video):
        matches = set()
        # series
        if video.series and (sanitize(self.series) in (
                 sanitize(name) for name in [video.series] + video.alternative_series)):
            matches.add('series')
        # season
        if video.season and self.season == video.season:
            matches.add('season')
        # episode
        if video.episode and self.episode == video.episode:
            matches.add('episode')

        # release_group
        if video.release_group and self.release:
            rg = sanitize_release_group(video.release_group)
            if any(r in sanitize_release_group(self.release) for r in get_equivalent_release_groups(rg)):
                matches.add('release_group')

                # blatantly assume we've got a matching format if the release group matches
                # fixme: smart?
                #matches.add('format')

        # resolution
        if video.resolution and self.version and str(video.resolution) in self.version.lower():
            matches.add('resolution')
        # format
        if video.format and self.format:
            formats = [video.format]
            if video.format == "WEB-DL":
                formats.append("WEB")

            for fmt in formats:
                if fmt.lower() in self.format.lower():
                    matches.add('format')
                    break

        # tvdb_id
        if video.tvdb_id and str(self.tvdb_id) == str(video.tvdb_id):
            matches.add('tvdb_id')

        matches |= guess_matches(video, guessit(self.release_info), partial=True)
        return matches


class ArgenteamProvider(_ArgenteamProvider, ProviderSubtitleArchiveMixin):
    subtitle_class = ArgenteamSubtitle
    hearing_impaired_verifiable = False
    language_list = list(_ArgenteamProvider.languages)

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}

    def search_episode_id(self, series, season, episode):
        """Search the episode id from the `series`, `season` and `episode`.

        :param str series: series of the episode.
        :param int season: season of the episode.
        :param int episode: episode number.
        :return: the episode id, if any.
        :rtype: int or None

        """
        # make the search
        query = '%s S%#02dE%#02d' % (series, season, episode)
        logger.info('Searching episode id for %r', query)
        r = self.session.get(self.API_URL + 'search', params={'q': query}, timeout=10)
        r.raise_for_status()
        results = json.loads(r.text)
        episode_id = None
        if results['total'] == 1:
            if results['results'][0]['type'] == "episode":
                episode_id = results['results'][0]['id']
        else:
            logger.error('No episode id found for %r', series)

        return episode_id

    def query(self, series, video, season, episode):

        episode_id = self.search_episode_id(series, season, episode)
        if episode_id is None:
            return []

        response = self.session.get(self.API_URL + 'episode', params={'id': episode_id}, timeout=10)
        response.raise_for_status()
        content = json.loads(response.text)
        language = self.language_list[0]
        subtitles = []
        for r in content['releases']:
            for s in r['subtitles']:
                sub = ArgenteamSubtitle(language, s['uri'], series, season, episode, r['team'], r['tags'], r['source'],
                                        r['codec'], content["tvdb"],
                                        asked_for_release_group=video.release_group,
                                        asked_for_episode=episode
                                        )
                subtitles.append(sub)

        return subtitles

    def list_subtitles(self, video, languages):
        titles = [video.series] + video.alternative_series
        for title in titles:
            subs = self.query(title, video, video.season, video.episode)
            if subs:
                return subs

        return []

    def download_subtitle(self, subtitle):
        # download as a zip
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        # open the zip
        with ZipFile(io.BytesIO(r.content)) as zf:
            subtitle.content = self.get_subtitle_from_archive(subtitle, zf)
