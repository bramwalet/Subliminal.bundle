# coding: iso8859_2
import io
import six
from pkg_resources import require
import logging
import re
from zipfile import ZipFile

from babelfish import Language, language_converters
from requests import Session

from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal.providers import ParserBeautifulSoup
from subliminal_patch.exceptions import ProviderError
from subliminal.score import get_equivalent_release_groups
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal.utils import sanitize, sanitize_release_group
from subliminal.video import Episode
from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from subliminal_patch.utils import sanitize, fix_inconsistent_naming as _fix_inconsistent_naming
from guessit import guessit


def fix_inconsistent_naming(title):
    """Fix titles with inconsistent naming using dictionary and sanitize them.

    :param str title: original title.
    :return: new title.
    :rtype: str

    """
    return _fix_inconsistent_naming(title, {"DC's Legends of Tomorrow": "Legends of Tomorrow",
                                            "Marvel's Jessica Jones": "Jessica Jones"})


logger = logging.getLogger(__name__)

language_converters.register('hosszupuska = subliminal_patch.converters.hosszupuska:HosszupuskaConverter')


class HosszupuskaSubtitle(Subtitle):
    """Hosszupuska Subtitle."""
    provider_name = 'hosszupuska'

    def __str__(self):
        subtit = "Subtitle id: " + str(self.subtitle_id) \
               + " Series: " + self.series \
               + " Season: " + str(self.season) \
               + " Episode: " + str(self.episode) \
               + " Releases: " + str(self.releases)
        if self.year:
            subtit = subtit + " Year: " + str(self.year)
        if six.PY3:
            return subtit
        return subtit.encode('utf-8')

    def __init__(self, language, page_link, subtitle_id, series, season, episode,
                 releases, year, asked_for_release_group=None, asked_for_episode=None):
        super(HosszupuskaSubtitle, self).__init__(language, page_link=page_link)
        self.subtitle_id = subtitle_id
        self.series = series
        self.season = season
        self.episode = episode
        self.releases = releases
        self.year = year
        if year:
            self.year = int(year)

        self.release_info = hash
        self.page_link = page_link
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode

    @property
    def id(self):
        return str(self.subtitle_id)

    def get_matches(self, video):
        matches = set()
        # series
        if video.series and sanitize(self.series) == sanitize(video.series):
            matches.add('series')
        # season
        if video.season and self.season == video.season:
            matches.add('season')
        # episode
        if video.episode and self.episode == video.episode:
            matches.add('episode')
        # year
        if ('series' in matches and video.original_series and self.year is None or
           video.year and video.year == self.year):
            matches.add('year')

        # release_group
        if (video.release_group and self.releases and
                any(r in sanitize_release_group(self.releases)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        # resolution
        if video.resolution and self.releases and video.resolution in self.releases.lower():
            matches.add('resolution')
        # format
        if video.format and self.releases and video.format.lower() in self.releases.lower():
            matches.add('format')
        # other properties
        matches |= guess_matches(video, guessit(self.releases))

        return matches


class HosszupuskaProvider(Provider, ProviderSubtitleArchiveMixin):
    """Hosszupuska Provider."""
    languages = {Language('hun', 'HU')} | {Language(l) for l in [
        'hun', 'eng'
    ]}
    video_types = (Episode,)
    server_url = 'http://hosszupuskasub.com/'
    subtitle_class = HosszupuskaSubtitle
    hearing_impaired_verifiable = True

    def initialize(self):
        self.session = Session()
        # self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__

    def terminate(self):
        self.session.close()

    def get_language(self, text):
        if text == '1.gif':
            return Language.fromhosszupuska('hu')
        if text == '2.gif':
            return Language.fromhosszupuska('en')
        return None

    def query(self, series, season, episode, year=None, video=None):

        # Search for s01e03 instead of s1e3
        seasona = season
        episodea = episode
        series = fix_inconsistent_naming(series)
        seriesa = series.replace(' ', '+').replace('\'', '')

        if season < 10:
            seasona = '0'+str(season)
        else:
            seasona = str(season)
        if episode < 10:
            episodea = '0'+str(episode)
        else:
            episodea = str(episode)

        # get the episode page
        logger.info('Getting the page for episode %s', episode)
        url = self.server_url + "sorozatok.php?cim=" + seriesa + "&evad="+str(seasona) + \
            "&resz="+str(episodea)+"&nyelvtipus=%25&x=24&y=8"
        logger.info('Url %s', url)

        r = self.session.get(url, timeout=10).content

        i = 0
        soup = ParserBeautifulSoup(r, ['lxml'])

        table = soup.find_all("table")[9]

        subtitles = []
        # loop over subtitles rows
        for row in table.find_all("tr"):
            i = i + 1
            if "this.style.backgroundImage='url(css/over2.jpg)" in str(row) and i > 5:
                datas = row.find_all("td")

                # Currently subliminal not use these params, but maybe later will come in handy
                # hunagrian_name = re.split('s(\d{1,2})', datas[1].find_all('b')[0].getText())[0]
                # Translator of subtitle
                # sub_translator = datas[3].getText()
                # Posting date of subtitle
                # sub_date = datas[4].getText()

                sub_year = None
                # Handle the case when '(' in subtitle
                if datas[1].getText().count('(') == 2:
                    sub_english_name = re.split('s(\d{1,2})e(\d{1,2})', datas[1].getText())[3]
                if datas[1].getText().count('(') == 3:
                    sub_year = re.findall(r"(?<=\()(\d{4})(?=\))", datas[1].getText().strip())[0]
                    sub_english_name = re.split('s(\d{1,2})e(\d{1,2})', datas[1].getText().split('(')[0])[0]
                sub_season = int((re.findall('s(\d{1,2})', datas[1].find_all('b')[0].getText(), re.VERBOSE)[0])
                                 .lstrip('0'))
                sub_episode = int((re.findall('e(\d{1,2})', datas[1].find_all('b')[0].getText(), re.VERBOSE)[0])
                                  .lstrip('0'))
                sub_language = self.get_language(datas[2].find_all('img')[0]['src'].split('/')[1])
                sub_downloadlink = datas[6].find_all('a')[1]['href']
                sub_id = sub_downloadlink.split('=')[1].split('.')[0]

                if datas[1].getText().count('(') == 2:
                    sub_version = datas[1].getText().split('(')[1].split(')')[0]
                if datas[1].getText().count('(') == 3:
                    sub_version = datas[1].getText().split('(')[2].split(')')[0]

                # One subtitle can be used for sevearl relase add both of them.
                sub_releases = str(sub_version.split(','))
                subtitle = self.subtitle_class(sub_language, sub_downloadlink, sub_id, sub_english_name, sub_season,
                                               sub_episode, sub_releases, sub_year,
                                               asked_for_release_group=video.release_group, asked_for_episode=episode)

                if sub_season == season and sub_episode == episode:
                    logger.debug('Found subtitle \r\n%s', subtitle)
                    subtitles.append(subtitle)
        return subtitles

    def list_subtitles(self, video, languages):
        return [s for s in self.query(video.series, video.season, video.episode, video.year, video=video)
                if s.language in languages]

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.page_link, timeout=10)
        r.raise_for_status()

        # open the archive
        archive_stream = io.BytesIO(r.content)
        if is_rarfile(archive_stream):
            logger.debug('Archive identified as rar')
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            logger.debug('Archive identified as zip')
            archive = ZipFile(archive_stream)
        else:
            raise ProviderError('Unidentified archive type')

        subtitle.content = self.get_subtitle_from_archive(subtitle, archive)
