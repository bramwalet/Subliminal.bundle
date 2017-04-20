# coding=utf-8


import logging

import chardet
import pysrt
import pysubs2
from bs4 import UnicodeDammit
from subliminal import Subtitle

logger = logging.getLogger(__name__)


class PatchedSubtitle(Subtitle):
    storage_path = None
    release_info = None
    matches = None

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