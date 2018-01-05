# coding=utf-8

import re
import time
import logging
import traceback
import types

from guessit import guessit
from subliminal import ProviderError
from subliminal.providers.opensubtitles import Unauthorized
from subliminal.subtitle import fix_line_ending

logger = logging.getLogger(__name__)


clean_whitespace_re = re.compile(r'\s+')


class PunctuationMixin(object):
    """
    provider mixin

    fixes show ids for stuff like "Mr. Petterson", as our matcher already sees it as "Mr Petterson" but addic7ed doesn't
    """

    def clean_punctuation(self, s):
        return s.replace(".", "").replace(":", "").replace("'", "").replace("&", "").replace("-", "")

    def clean_whitespace(self, s):
        return clean_whitespace_re.sub("", s)

    def full_clean(self, s):
        return self.clean_whitespace(self.clean_punctuation(s))


class ProviderRetryMixin(object):
    def retry(self, f, amount=2, exc=Exception, retry_timeout=10):
        i = 0
        while i <= amount:
            try:
                return f()
            except exc:
                formatted_exc = traceback.format_exc()
                i += 1
                if i == amount or isinstance(exc, Unauthorized):
                    raise

            logger.debug(u"Retrying %s, try: %i/%i, exception: %s" % (self.__class__.__name__, i, amount, formatted_exc))
            time.sleep(retry_timeout)


class ProviderSubtitleArchiveMixin(object):
    """
    handled ZipFile and RarFile archives
    needs subtitle.matches and subtitle.releases to work
    """
    def get_subtitle_from_archive(self, subtitle, archive):
        # extract subtitle's content
        subs_in_archive = []
        for name in archive.namelist():
            for ext in (".srt", ".sub", ".ssa", ".ass"):
                if name.endswith(ext):
                    subs_in_archive.append(name)

        # select the correct subtitle file
        matching_sub = None
        if len(subs_in_archive) == 1:
            matching_sub = subs_in_archive[0]
        else:
            for sub_name in subs_in_archive:
                guess = guessit(sub_name)

                # consider subtitle valid if:
                # - episode and season match
                # - format matches (if it was matched before)
                # - release group matches (and we asked for one and it was matched, or it was not matched)
                is_episode = subtitle.episode is not None
                if not is_episode or (
                        (
                                guess["episode"] == subtitle.episode
                                or (subtitle.is_pack and guess["episode"] == subtitle.asked_for_episode)
                        ) and guess["season"] == subtitle.season):

                    format_matches = True

                    if "format" in subtitle.matches:
                        format_matches = False
                        if isinstance(subtitle.releases, types.ListType):
                            releases = ",".join(subtitle.releases).lower()
                        else:
                            releases = subtitle.releases.lower()

                        formats = guess["format"]
                        if not isinstance(formats, types.ListType):
                            formats = [formats]

                        for f in formats:
                            format_matches = f.lower() in releases
                            if format_matches:
                                break

                    release_group_matches = True
                    if subtitle.is_pack or (subtitle.asked_for_release_group and
                                            ("release_group" in subtitle.matches or
                                             "hash" in subtitle.matches)):

                        asked_for_rlsgrp = subtitle.asked_for_release_group.lower()
                        release_group_matches = False
                        release_groups = guess["release_group"]
                        if not isinstance(release_groups, types.ListType):
                            release_groups = [release_groups]

                        for release_group in release_groups:
                            release_group_matches = release_group.lower() == asked_for_rlsgrp
                            if release_group_matches:
                                break

                    if release_group_matches and format_matches:
                        matching_sub = sub_name
                        break

        if not matching_sub:
            raise ProviderError("None of expected subtitle found in archive")

        logger.info(u"Using %s from the archive", matching_sub)
        return fix_line_ending(archive.read(matching_sub))
