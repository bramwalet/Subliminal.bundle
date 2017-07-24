# coding=utf-8
import logging

from subliminal.providers.legendastv import LegendasTVSubtitle as _LegendasTVSubtitle, \
    LegendasTVProvider as _LegendasTVProvider

logger = logging.getLogger(__name__)


class LegendasTVSubtitle(_LegendasTVSubtitle):
    def __init__(self, language, type, title, year, imdb_id, season, archive, name):
        super(LegendasTVSubtitle, self).__init__(language, type, title, year, imdb_id, season, archive, name)
        self.archive.content = None
        self.release_info = archive.name
        self.page_link = archive.link

    def make_picklable(self):
        self.archive.content = None
        return self


class LegendasTVProvider(_LegendasTVProvider):
    subtitle_class = LegendasTVSubtitle

    def download_subtitle(self, subtitle):
        super(LegendasTVProvider, self).download_subtitle(subtitle)
        subtitle.archive.content = None
