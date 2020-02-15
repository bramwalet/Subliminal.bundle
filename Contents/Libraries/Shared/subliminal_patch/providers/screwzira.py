# -*- coding: utf-8 -*-
from requests import Session
import json
import logging
from subzero.language import Language
from bs4 import BeautifulSoup
from guessit import guessit

from subliminal_patch.providers import Provider
from subliminal.providers import Episode, Movie
from subliminal_patch.utils import sanitize
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.subtitle import fix_line_ending

__author__ = "Dor Nizar"

logger = logging.getLogger(__name__)


class ScrewZiraSubtitle(Subtitle):
    provider_name = 'screwzira'

    def __init__(self, language, title_id, subtitle_id, series, season, episode, release, year):
        super(ScrewZiraSubtitle, self).__init__(language, subtitle_id)
        self.title_id = title_id
        self.subtitle_id = subtitle_id
        self.series = series
        self.season = season
        self.episode = episode
        self.release = release
        self.year = year

    def get_matches(self, video):
        matches = set()
        logger.debug("--ScrewZiraSubtitle--\n{}".format(self.__dict__))

        # episode
        if isinstance(video, Episode):
            # series
            if video.series and sanitize(self.series) == sanitize(video.series):
                matches.add('series')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')
            # guess
            matches |= guess_matches(video, guessit(self.release, {'type': 'episode'}))
        # movie
        elif isinstance(video, Movie):
            # title
            if video.title and (sanitize(self.series) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles)):
                matches.add('title')
            # year
            if video.year and self.year == video.year:
                matches.add('year')
            # guess
            matches |= guess_matches(video, guessit(self.release, {'type': 'movie'}))

        logger.debug("ScrewZira subtitle criteria match:\n{}".format(matches))
        return matches

    @property
    def id(self):
        return self.subtitle_id


class ScrewZiraProvider(Provider):
    subtitle_class = ScrewZiraSubtitle
    languages = {Language.fromalpha2(l) for l in ['he']}
    URL_SERVER = 'https://www.screwzira.com/'

    URI_SEARCH_TITLE = 'Services/ContentProvider.svc/GetSearchForecast'
    URI_SEARCH_SERIES_SUBTITLE = 'Services/GetModuleAjax.ashx'
    URI_SEARCH_MOVIE_SUBTITLE = "MovieInfo.aspx"
    URI_REQ_SUBTITLE_ID = "Services/ContentProvider.svc/RequestSubtitleDownload"
    URI_DOWNLOAD_SUBTITLE = "Services/DownloadFile.ashx"

    def initialize(self):
        logger.debug("ScrewZira initialize")
        self.session = Session()
        self.session.headers[
            'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; ' \
                            'Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'

    def terminate(self):
        logger.debug("ScrewZira terminate")
        self.session.close()

    def __init__(self):
        self.session = None

    def _search_series(self, title):
        logger.debug("Searching '{}'".format(title))
        title_request = {
            "request": {
                "SearchString": title,
                "SearchType": "Film"
            }
        }
        r = self.session.post(self.URL_SERVER + self.URI_SEARCH_TITLE, json=title_request, allow_redirects=False,
                              timeout=10)
        r.raise_for_status()
        series_found = r.json()
        if 'd' in series_found:
            try:
                series_found = json.loads(series_found['d'])
            except ValueError:
                series_found = None
        if 'Items' in series_found:
            return series_found['Items']
        return []

    def _search_subtitles(self, title_id, season=None, episode=None):
        if season and episode:
            params = {
                'moduleName': 'SubtitlesList',
                'SeriesID': title_id,
                'Season': season,
                'Episode': episode
            }
            r = self.session.get(url=self.URL_SERVER + self.URI_SEARCH_SERIES_SUBTITLE, params=params)
        else:
            params = {
                'ID': title_id,
            }
            r = self.session.get(url=self.URL_SERVER + self.URI_SEARCH_MOVIE_SUBTITLE, params=params)

        r.raise_for_status()
        results = r.content
        if not results:
            return []
        subtitles = BeautifulSoup(results, 'html.parser').select('a.fa')
        logger.debug("[BS4] Elements found:\n{}".format(subtitles))
        subtitle_list = []
        for i in subtitles:
            subtitle_id = i.attrs['data-subtitle-id']
            release = i.findParent().findParent().text.strip().split('\n')[0]
            subtitle_list.append((subtitle_id, release))

        return subtitle_list  # [(Subtitle ID, name), (....)]

    def _req_download_identifier(self, title_id, subtitle_id):
        logger.debug("Request subtitle identifier for: title id: {}, subtitle id: {}".format(title_id, subtitle_id))
        data = {
            'request': {
                'FilmID': title_id,
                'SubtitleID': subtitle_id,
                'FontSize': 0,
                'FontColor': "",
                'PredefinedLayout': -1
            }
        }

        r = self.session.post(self.URL_SERVER + self.URI_REQ_SUBTITLE_ID, json=data, allow_redirects=False,
                              timeout=10)
        r.raise_for_status()
        try:
            r = json.loads(r.json()['d'])
        except ValueError:
            r = {}

        if 'DownloadIdentifier' not in r:
            logger.error("Download Identifier not found")
            return None
        return r['DownloadIdentifier']

    def _download_subtitles(self, download_id):
        logger.debug("Downloading subtitles by download identifier - {}".format(download_id))
        data = {'DownloadIdentifier': download_id}
        r = self.session.get(self.URL_SERVER + self.URI_DOWNLOAD_SUBTITLE, params=data,
                             timeout=10)
        r.raise_for_status()
        if not r.content:
            logger.debug("Download subtitle failed")
            return None

        logger.debug("Download subtitle success")
        return r.content

    def query(self, title, season=None, episode=None, year=None):
        subtitles = []
        titles = self._search_series(title)
        if season and episode:
            logger.debug("Searching for:\nTitle: {}\nSeason: {}\nEpisode: {}\nYear: {}".format(title, season,
                                                                                               episode, year))
        else:
            logger.debug("Searching for:\nTitle: {}\nYear: {}\n".format(title, year))
        for title in titles:
            logger.debug("Title Candidate: {}".format(title))
            title_id = title['ID']
            if season and episode:
                result = self._search_subtitles(title_id, season, episode)
            else:
                result = self._search_subtitles(title_id)

            if not result:
                continue

            for subtitle_id, release in result:
                subtitles.append(self.subtitle_class(next(iter(self.languages)), title_id, subtitle_id,
                                                     title['EngName'], season, episode, release, year))

        if subtitles:
            logger.debug("Found Subtitle Candidates: {}".format(subtitles))
        return subtitles

    def list_subtitles(self, video, languages):
        season = episode = year = title = None

        if isinstance(video, Episode):
            logger.info("list_subtitles Series: {}, season: {}, episode: {}".format(video.series,
                                                                                    video.season,
                                                                                    video.episode))
            title = video.series
            season = video.season
            episode = video.episode
        elif isinstance(video, Movie):
            logger.info("list_subtitles Movie: {}, year: {}".format(video.title, video.year))
            title = video.title
            year = video.year

        return [s for s in self.query(title, season, episode, year) if s.language in languages]

    def download_subtitle(self, subtitle):
        # type: (ScrewZiraSubtitle) -> None

        logger.info('Downloading subtitle from ScrewZira: %r', subtitle)
        downloadID = self._req_download_identifier(subtitle.title_id, subtitle.subtitle_id)
        if not downloadID:
            logger.debug('Unable to retrieve download identifier')
            return None

        content = self._download_subtitles(downloadID)
        if not content:
            logger.debug('Unable to download subtitle')
            return None

        subtitle.content = fix_line_ending(content)
