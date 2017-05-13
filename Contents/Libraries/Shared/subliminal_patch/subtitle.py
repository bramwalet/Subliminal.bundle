# coding=utf-8


import logging

import chardet
import pysrt
import pysubs2
from bs4 import UnicodeDammit
from subzero.modification import SubtitleModifications
from subliminal import Subtitle

logger = logging.getLogger(__name__)


class PatchedSubtitle(Subtitle):
    storage_path = None
    release_info = None
    matches = None
    hash_verifiable = False
    mods = None
    plex_media_fps = None
    skip_wrong_fps = False
    wrong_fps = False

    def __init__(self, language, hearing_impaired=False, page_link=None, encoding=None, mods=None):
        super(PatchedSubtitle, self).__init__(language, hearing_impaired=hearing_impaired, page_link=page_link,
                                              encoding=encoding)
        self.mods = mods

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, self.page_link, self.language)

    def guess_encoding(self):
        """Guess encoding using the language, falling back on chardet.

        :return: the guessed encoding.
        :rtype: str

        """
        logger.info('Guessing encoding for language %s', self.language.alpha3)

        encodings = ['utf-8']

        # add language-specific encodings
        if self.language.alpha3 == 'zho':
            encodings.extend(['gb18030', 'big5'])
        elif self.language.alpha3 == 'jpn':
            encodings.append('shift-jis')
        elif self.language.alpha3 == 'tha':
            encodings.append('tis-620')

        # arabian/farsi
        elif self.language.alpha3 in ('ara', 'fas', 'per'):
            encodings.append('windows-1256')
        elif self.language.alpha3 == 'heb':
            encodings.append('windows-1255')
        elif self.language.alpha3 == 'tur':
            encodings.extend(['iso-8859-9', 'windows-1254'])

        # Greek
        elif self.language.alpha3 in ('grc', 'gre', 'ell'):
            encodings.extend(['windows-1253', 'cp1253', 'cp737', 'iso8859_7', 'cp875', 'cp869', 'iso2022_jp_2',
                              'mac_greek'])

        # Polish, Czech, Slovak, Hungarian, Slovene, Bosnian, Croatian, Serbian (Latin script),
        # Romanian (before 1993 spelling reform) and Albanian
        elif self.language.alpha3 in ('pol', 'cze', 'ces', 'slk', 'slo', 'slv', 'hun', 'bos', 'hbs', 'hrv', 'rsb',
                                      'ron', 'rum', 'sqi', 'alb'):
            # Eastern European Group 1
            encodings.append('windows-1250')

        # Bulgarian, Serbian and Macedonian
        elif self.language.alpha3 in ('bul', 'srp', 'mkd', 'mac'):
            # Eastern European Group 2
            encodings.append('windows-1251')
        else:
            # Western European (windows-1252)
            encodings.append('latin-1')

        # try to decode
        logger.debug('Trying encodings %r', encodings)
        for encoding in encodings:
            try:
                self.content.decode(encoding)
            except UnicodeDecodeError:
                pass
            else:
                logger.info('Guessed encoding %s', encoding)
                return encoding

        logger.warning('Could not guess encoding from language')

        # fallback on chardet
        encoding = chardet.detect(self.content)['encoding']
        logger.info('Chardet found encoding %s', encoding)

        if not encoding:
            # fallback on bs4
            logger.info('Falling back to bs4 detection')
            a = UnicodeDammit(self.content)

            Log.Debug("bs4 detected encoding: %s" % a.original_encoding)

            if a.original_encoding:
                return a.original_encoding
            raise ValueError(u"Couldn't guess the proper encoding for %s" % self)

        return encoding

    def is_valid(self):
        """Check if a :attr:`text` is a valid SubRip format.

        :return: whether or not the subtitle is valid.
        :rtype: bool

        """
        if not self.text:
            return False

        # valid srt
        try:
            pysrt.from_string(self.text, error_handling=pysrt.ERROR_RAISE)
        except Exception, e:
            logger.error("PySRT-parsing failed: %s, trying pysubs2", e)
        else:
            return True

        # something else, try to return srt
        try:
            logger.debug("Trying parsing with PySubs2")
            subs = pysubs2.SSAFile.from_string(self.text)
            self.content = subs.to_string("srt")
        except:
            logger.exception("Couldn't convert subtitle %s to .srt format", self)
            return False

        return True

    def get_modified_content(self, debug=False):
        """
        :return: string 
        """
        if not self.mods:
            return self.content

        encoding = self.guess_encoding()
        submods = SubtitleModifications(debug=debug)
        submods.load(content=self.text, language=self.language)
        submods.modify(*self.mods)

        try:
            return submods.to_unicode().encode(encoding=encoding)
        except UnicodeEncodeError:
            return submods.to_unicode().encode(encoding="utf-8")

    def get_modified_text(self, debug=False):
        """
        :return: unicode 
        """
        content = self.get_modified_content(debug=debug)
        if not content:
            return
        encoding = self.guess_encoding()
        return content.decode(encoding=encoding)


class ModifiedSubtitle(PatchedSubtitle):
    id = None
