# coding=utf-8

import re
import logging
from babelfish import Language
from subliminal.providers import ParserBeautifulSoup
from subliminal.cache import SHOW_EXPIRATION_TIME, region
from subliminal.providers.tvsubtitles import TVsubtitlesProvider as _TVsubtitlesProvider, \
    TVsubtitlesSubtitle as _TVsubtitlesSubtitle, link_re
from subliminal.utils import sanitize
from subliminal_patch.extensions import provider_registry

logger = logging.getLogger(__name__)


class TVsubtitlesSubtitle(_TVsubtitlesSubtitle):
    def __init__(self, language, page_link, subtitle_id, series, season, episode, year, rip, release):
        super(TVsubtitlesSubtitle, self).__init__(language, page_link, subtitle_id, series, season, episode,
                                                  year, rip, release)
        self.release_info = u"%s, %s" % (rip, release)


class TVsubtitlesProvider(_TVsubtitlesProvider):
    subtitle_class = TVsubtitlesSubtitle

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
            match = link_re.match(suggestion.text)
            if not match:
                logger.error('Failed to match %s', suggestion.text)
                continue

            if sanitize(match.group('series')).lower() == series.lower():
                if year is not None and int(match.group('first_year')) != year:
                    logger.debug('Year does not match')
                    continue
                show_id = int(suggestion['href'][8:-5])
                logger.debug('Found show id %d', show_id)
                break

        return show_id

    def query(self, series, season, episode, year=None):
        # search the show id
        show_id = self.search_show_id(series, year)
        if show_id is None:
            logger.error('No show id found for %r (%r)', series, {'year': year})
            return []

        # get the episode ids
        episode_ids = self.get_episode_ids(show_id, season)
        if episode not in episode_ids:
            logger.error('Episode %d not found', episode)
            return []

        # get the episode page
        logger.info('Getting the page for episode %d', episode_ids[episode])
        r = self.session.get(self.server_url + 'episode-%d.html' % episode_ids[episode], timeout=10)
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over subtitles rows
        subtitles = []
        for row in soup.select('.subtitlen'):
            # read the item
            language = Language.fromtvsubtitles(row.h5.img['src'][13:-4])
            subtitle_id = int(row.parent['href'][10:-5])
            page_link = self.server_url + 'subtitle-%d.html' % subtitle_id
            rip = row.find('p', title='rip').text.strip() or None
            release = row.find('p', title='release').text.strip() or None

            subtitle = self.subtitle_class(language, page_link, subtitle_id, series, season, episode, year, rip,
                                           release)
            logger.info('Found subtitle %s', subtitle)
            subtitles.append(subtitle)

        return subtitles
