# coding=utf-8
import logging

from subliminal.providers.argenteam import ArgenteamProvider as _ArgenteamProvider, \
    ArgenteamSubtitle as _ArgenteamSubtitle, json, ZipFile, io
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin

logger = logging.getLogger(__name__)


class ArgenteamSubtitle(_ArgenteamSubtitle):
    hearing_impaired_verifiable = False

    def __init__(self, language, download_link, series, season, episode, release, version, asked_for_episode=None,
                 asked_for_release_group=None, *args, **kwargs):
        super(ArgenteamSubtitle, self).__init__(language, download_link, series, season, episode, release, version,
                                                *args, **kwargs)
        self.release_info = u"%s-%s" % (version, release)
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode
        self.matches = None

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, self.release_info, self.language)

    def get_matches(self, video):
        self.matches = super(ArgenteamSubtitle, self).get_matches(video)
        return self.matches


class ArgenteamProvider(_ArgenteamProvider, ProviderSubtitleArchiveMixin):
    subtitle_class = ArgenteamSubtitle
    hearing_impaired_verifiable = False
    language_list = list(_ArgenteamProvider.languages)

    def query(self, video, series, season, episode):

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
                sub = ArgenteamSubtitle(language, s['uri'], series, season, episode, r['team'], r['tags'],
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
