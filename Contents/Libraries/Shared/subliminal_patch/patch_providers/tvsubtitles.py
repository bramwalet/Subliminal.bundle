# coding=utf-8

import logging
from subliminal.providers import ParserBeautifulSoup
from subliminal.cache import SHOW_EXPIRATION_TIME, region
from subliminal.providers.tvsubtitles import TVsubtitlesProvider, link_re

from .mixins import PunctuationMixin

logger = logging.getLogger(__name__)


class PatchedTVsubtitlesProvider(PunctuationMixin, TVsubtitlesProvider):
    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def search_show_id(self, series, year=None):
        """Search the show id from the `series` and `year`.
        :param string series: series of the episode.
        :param year: year of the series, if any.
        :type year: int or None
        :return: the show id, if any.
        :rtype: int or None
        """
        # make the search
        logger.info('Searching show id for %r', series)
        r = self.session.post(self.server_url + 'search.php', data={'q': series}, timeout=10)
        r.raise_for_status()

        # get the series out of the suggestions
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
        show_id = None
        for suggestion in soup.select('div.left li div a[href^="/tvshow-"]'):
            match = link_re.match(self.clean_punctuation(suggestion.text))
            if not match:
                logger.error('Failed to match %s', suggestion.text)
                continue

            if match.group('series').lower() == series.lower():
                if year is not None and int(match.group('first_year')) != year:
                    logger.debug('Year does not match')
                    continue
                show_id = int(suggestion['href'][8:-5])
                logger.debug('Found show id %d', show_id)
                break

        return show_id