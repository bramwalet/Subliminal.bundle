# coding=utf-8

import logging
import io
import re

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        import xml.etree.ElementTree as etree
from babelfish import Language
from zipfile import ZipFile
from subliminal import Episode
from subliminal import Movie
from subliminal.providers.podnapisi import PodnapisiProvider, PodnapisiSubtitle, fix_line_ending, ProviderError
from mixins import ProviderRetryMixin

logger = logging.getLogger(__name__)


class PatchedPodnapisiSubtitle(PodnapisiSubtitle):
    provider_name = 'podnapisi'

    def __init__(self, language, hearing_impaired, page_link, pid, releases, title, season=None, episode=None,
                 year=None):
        super(PatchedPodnapisiSubtitle, self).__init__(language, hearing_impaired, page_link, pid, releases, title,
                                                       season=season, episode=episode, year=year)
        self.release_info = u", ".join(releases)


class PatchedPodnapisiProvider(ProviderRetryMixin, PodnapisiProvider):
    only_foreign = False

    def __init__(self, only_foreign=False):
        self.only_foreign = only_foreign

        if only_foreign:
            logger.info("Only searching for foreign/forced subtitles")

        super(PatchedPodnapisiProvider, self).__init__()

    def list_subtitles(self, video, languages):
        if isinstance(video, Episode):
            return [s for l in languages for s in self.query(l, video.series, season=video.season,
                                                             episode=video.episode, year=video.year,
                                                             only_foreign=self.only_foreign)]
        elif isinstance(video, Movie):
            return [s for l in languages for s in self.query(l, video.title, year=video.year,
                                                             only_foreign=self.only_foreign)]

    def download_subtitle(self, subtitle):
        # download as a zip
        logger.info('Downloading subtitle %r', subtitle)
        r = self.retry(lambda: self.session.get(self.server_url + subtitle.pid + '/download',
                                                params={'container': 'zip'}, timeout=10))
        r.raise_for_status()

        # open the zip
        with ZipFile(io.BytesIO(r.content)) as zf:
            if len(zf.namelist()) > 1:
                raise ProviderError('More than one file to unzip')

            subtitle.content = fix_line_ending(zf.read(zf.namelist()[0]))

    def query(self, language, keyword, season=None, episode=None, year=None, only_foreign=False):
        # set parameters, see http://www.podnapisi.net/forum/viewtopic.php?f=62&t=26164#p212652
        params = {'sXML': 1, 'sL': str(language), 'sK': keyword}
        is_episode = False
        if season and episode:
            is_episode = True
            params['sTS'] = season
            params['sTE'] = episode
        if year:
            params['sY'] = year

        # loop over paginated results
        logger.info('Searching subtitles %r', params)
        subtitles = []
        pids = set()
        while True:
            # query the server
            xml = etree.fromstring(self.retry(lambda: self.session.get(self.server_url + 'search/old',
                                                                       params=params, timeout=10).content))

            # exit if no results
            if not int(xml.find('pagination/results').text):
                logger.debug('No subtitles found')
                break

            # loop over subtitles
            for subtitle_xml in xml.findall('subtitle'):
                # read xml elements
                language = Language.fromietf(subtitle_xml.find('language').text)
                hearing_impaired = 'n' in (subtitle_xml.find('flags').text or '')
                foreign = 'f' in (subtitle_xml.find('flags').text or '')
                if only_foreign and not foreign:
                    continue

                if not only_foreign and foreign:
                    continue

                page_link = subtitle_xml.find('url').text
                pid = subtitle_xml.find('pid').text
                releases = []
                if subtitle_xml.find('release').text:
                    for release in subtitle_xml.find('release').text.split():
                        releases.append(re.sub(r'\.+$', '', release))  # remove trailing dots
                title = subtitle_xml.find('title').text
                season = int(subtitle_xml.find('tvSeason').text)
                episode = int(subtitle_xml.find('tvEpisode').text)
                year = int(subtitle_xml.find('year').text)

                if is_episode:
                    subtitle = PatchedPodnapisiSubtitle(language, hearing_impaired, page_link, pid, releases, title,
                                                 season=season, episode=episode, year=year)
                else:
                    subtitle = PatchedPodnapisiSubtitle(language, hearing_impaired, page_link, pid, releases, title,
                                                 year=year)

                # ignore duplicates, see http://www.podnapisi.net/forum/viewtopic.php?f=62&t=26164&start=10#p213321
                if pid in pids:
                    continue

                logger.debug('Found subtitle %r', subtitle)
                subtitles.append(subtitle)
                pids.add(pid)

            # stop on last page
            if int(xml.find('pagination/current').text) >= int(xml.find('pagination/count').text):
                break

            # increment current page
            params['page'] = int(xml.find('pagination/current').text) + 1
            logger.debug('Getting page %d', params['page'])

        return subtitles