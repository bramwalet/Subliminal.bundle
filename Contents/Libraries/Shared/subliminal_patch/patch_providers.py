# coding=utf-8

import logging
from random import randint
from subliminal.providers.addic7ed import Addic7edProvider, Addic7edSubtitle, ParserBeautifulSoup, series_year_re, Language

logger = logging.getLogger(__name__)

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
