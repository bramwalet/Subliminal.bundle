# coding=utf-8
import os
import logging
import pytz

from dogpile.cache.api import NO_VALUE
from datetime import datetime
from guessit import guessit
from subliminal import region, SUBTITLE_EXTENSIONS
from subliminal.providers.legendastv import LegendasTVSubtitle as _LegendasTVSubtitle, \
    LegendasTVProvider as _LegendasTVProvider, releases_key
from subliminal.utils import sanitize

logger = logging.getLogger(__name__)


class LegendasTVSubtitle(_LegendasTVSubtitle):
    def __init__(self, language, type, title, year, imdb_id, season, archive, name):
        super(LegendasTVSubtitle, self).__init__(language, type, title, year, imdb_id, season, archive, name)
        self.release_info = archive.name
        self.page_link = archive.link


class LegendasTVProvider(_LegendasTVProvider):
    def query(self, language, title, season=None, episode=None, year=None):
        # search for titles
        titles = self.search_titles(sanitize(title))

        # search for titles with the quote or dot character
        ignore_characters = {'\'', '.'}
        if any(c in title for c in ignore_characters):
            titles.update(self.search_titles(sanitize(title, ignore_characters=ignore_characters)))

        subtitles = []
        # iterate over titles
        for title_id, t in titles.items():
            # discard mismatches on title
            if sanitize(t['title']) != sanitize(title):
                continue

            # episode
            if season and episode:
                # discard mismatches on type
                if t['type'] != 'episode':
                    continue

                # discard mismatches on season
                if 'season' not in t or t['season'] != season:
                    continue
            # movie
            else:
                # discard mismatches on type
                if t['type'] != 'movie':
                    continue

                # discard mismatches on year
                if year is not None and 'year' in t and t['year'] != year:
                    continue

            # iterate over title's archives
            for a in self.get_archives(title_id, language.legendastv):
                # clean name of path separators and pack flags
                clean_name = a.name.replace('/', '-')
                if a.pack and clean_name.startswith('(p)'):
                    clean_name = clean_name[3:]

                # guess from name
                guess = guessit(clean_name, {'type': t['type']})

                # episode
                if season and episode:
                    # discard mismatches on episode in non-pack archives
                    if not a.pack and 'episode' in guess and guess['episode'] != episode:
                        continue

                # compute an expiration time based on the archive timestamp
                expiration_time = (datetime.utcnow().replace(tzinfo=pytz.utc) - a.timestamp).total_seconds()

                # attempt to get the releases from the cache
                releases = region.get(releases_key.format(archive_id=a.id), expiration_time=expiration_time)

                # the releases are not in cache or cache is expired
                if releases == NO_VALUE:
                    logger.info('Releases not found in cache')

                    # download archive
                    self.download_archive(a)

                    # extract the releases
                    releases = []
                    for name in a.content.namelist():
                        # discard the legendastv file
                        if name.startswith('Legendas.tv'):
                            continue

                        # discard hidden files
                        if os.path.split(name)[-1].startswith('.'):
                            continue

                        # discard non-subtitle files
                        if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                            continue

                        releases.append(name)

                    # cache the releases
                    region.set(releases_key.format(archive_id=a.id), releases)

                # iterate over releases
                for r in releases:
                    subtitle = LegendasTVSubtitle(language, t['type'], t['title'], t.get('year'), t.get('imdb_id'),
                                                  t.get('season'), a, r)
                    logger.debug('Found subtitle %r', subtitle)
                    subtitles.append(subtitle)

        return subtitles
