# coding=utf-8

import logging
import re
from random import randint
from subliminal.providers.addic7ed import Addic7edProvider, Addic7edSubtitle, ParserBeautifulSoup, Language
from subliminal.cache import SHOW_EXPIRATION_TIME, region

logger = logging.getLogger(__name__)

series_year_re = re.compile('^(?P<series>[ \w.:]+)(?: \((?P<year>\d{4})\))?$')

class PatchedAddic7edProvider(Addic7edProvider):
    USE_ADDICTED_RANDOM_AGENTS = False

    def __init__(self, username=None, password=None, use_random_agents=False):
	super(PatchedAddic7edProvider, self).__init__(username=username, password=password)
	self.USE_ADDICTED_RANDOM_AGENTS = use_random_agents

    def initialize(self):
	super(PatchedAddic7edProvider, self).initialize()
	if self.USE_ADDICTED_RANDOM_AGENTS:
	    from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
	    logger.debug("addic7ed: using random user agents")
	    self.session.headers = {
        	'User-Agent': AGENT_LIST[randint(0, len(AGENT_LIST)-1)],
        	'Referer': self.server_url,
    	    }

    def clean_punctuation(self, s):
	# fixes show ids for stuff like "Mr. Petterson", as our matcher already sees it as "Mr Petterson" but addic7ed doesn't
	return s.replace(".", "")

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _search_show_id(self, series, year=None):
        """Search the show id from the `series` and `year`.
        :param string series: series of the episode.
        :param year: year of the series, if any.
        :type year: int or None
        :return: the show id, if found.
        :rtype: int or None
        """
        # build the params
        series_year = '%s (%d)' % (series, year) if year is not None else series
        params = {'search': series_year, 'Submit': 'Search'}

        # make the search
        logger.info('Searching show ids with %r', params)
        r = self.session.get(self.server_url + 'search.php', params=params, timeout=10)
        r.raise_for_status()
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # get the suggestion
        suggestion = soup.select('span.titulo > a[href^="/show/"]')
        if not suggestion:
            logger.warning('Show id not found: no suggestion')
            return None
        if not self.clean_punctuation(suggestion[0].i.text.lower()) == self.clean_punctuation(series_year.lower()):
            logger.warning('Show id not found: suggestion does not match')
            return None
        show_id = int(suggestion[0]['href'][6:])
        logger.debug('Found show id %d', show_id)

        return show_id
    
    def query(self, series, season, year=None, country=None):
        # get the show id
        show_id = self.get_show_id(series, year, country)
        if show_id is None:
            logger.error('No show id found for %r (%r)', series, {'year': year, 'country': country})
            return []

        # get the page of the season of the show
        logger.info('Getting the page of show id %d, season %d', show_id, season)
        r = self.session.get(self.server_url + 'show/%d' % show_id, params={'season': season}, timeout=10)
        r.raise_for_status()
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over subtitle rows
        header = soup.select('#header font')
        if header:
            match = series_year_re.match(header[0].text.strip()[:-10])
            series = match.group('series')
            year = int(match.group('year')) if match.group('year') else None

        subtitles = []
        for row in soup.select('tr.epeven'):
            cells = row('td')

            # ignore incomplete subtitles
            status = cells[5].text
            if status != 'Completed':
                logger.debug('Ignoring subtitle with status %s', status)
                continue

            # read the item
            language = Language.fromaddic7ed(cells[3].text)
            hearing_impaired = bool(cells[6].text)
            page_link = self.server_url + cells[2].a['href'][1:]
            season = int(cells[0].text)
            episode = int(cells[1].text)
            title = cells[2].text
            version = cells[4].text
            download_link = cells[9].a['href'][1:]

            subtitle = Addic7edSubtitle(language, hearing_impaired, page_link, series, season, episode, title, year,
                                        version, download_link)
            logger.debug('Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        return subtitles
