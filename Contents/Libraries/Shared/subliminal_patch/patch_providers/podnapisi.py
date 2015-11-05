# coding=utf-8

import logging
import io
from zipfile import ZipFile
from subliminal.providers.podnapisi import PodnapisiProvider, fix_line_ending, ProviderError

logger = logging.getLogger(__name__)


class PatchedPodnapisiProvider(PodnapisiProvider):
    def download_subtitle(self, subtitle):
        # download as a zip
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(self.server_url + subtitle.pid + '/download', params={'container': 'zip'}, timeout=10)
        r.raise_for_status()

        # open the zip
        with ZipFile(io.BytesIO(r.content)) as zf:
            if len(zf.namelist()) > 1:
                raise ProviderError('More than one file to unzip')

            subtitle.content = fix_line_ending(zf.read(zf.namelist()[0]))
