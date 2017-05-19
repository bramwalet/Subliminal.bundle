# coding=utf-8


import logging
import traceback

import re

import chardet
import pysrt
import pysubs2
from bs4 import UnicodeDammit
from pysubs2 import SSAStyle
from pysubs2.subrip import ms_to_timestamp, parse_tags
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

    _guessed_encoding = None

    def __init__(self, language, hearing_impaired=False, page_link=None, encoding=None, mods=None):
        super(PatchedSubtitle, self).__init__(language, hearing_impaired=hearing_impaired, page_link=page_link,
                                              encoding=encoding)
        self.mods = mods

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, self.page_link, self.language)

    def set_encoding(self, encoding):
        if encoding == self.guess_encoding():
            return

        unicontent = self.text
        self.content = unicontent.encode(encoding)
        self._guessed_encoding = encoding

    def guess_encoding(self):
        """Guess encoding using the language, falling back on chardet.

        :return: the guessed encoding.
        :rtype: str

        """
        if self._guessed_encoding:
            return self._guessed_encoding

        logger.info('Guessing encoding for language %s', self.language.alpha3)

        encodings = ['utf-8']

        # add language-specific encodings
        # http://scratchpad.wikia.com/wiki/Character_Encoding_Recommendation_for_Languages

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
            encodings.extend(['iso-8859-2', 'windows-1250'])

        # Bulgarian, Serbian and Macedonian, Ukranian and Russian
        elif self.language.alpha3 in ('bul', 'srp', 'mkd', 'mac', 'rus', 'ukr'):
            # Eastern European Group 2
            encodings.extend(['iso-8859-5', 'windows-1251'])
        else:
            # Western European (windows-1252) / Northern European
            encodings.extend(['iso-8859-15', 'iso-8859-9', 'iso-8859-4', 'iso-8859-1', 'latin-1'])

        # try to decode
        logger.debug('Trying encodings %r', encodings)
        for encoding in encodings:
            try:
                self.content.decode(encoding)
            except UnicodeDecodeError:
                pass
            else:
                logger.info('Guessed encoding %s', encoding)
                self._guessed_encoding = encoding
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
                self._guessed_encoding = a.original_encoding
                return a.original_encoding
            raise ValueError(u"Couldn't guess the proper encoding for %s" % self)

        self._guessed_encoding = encoding
        return encoding

    def is_valid(self):
        """Check if a :attr:`text` is a valid SubRip format.

        :return: whether or not the subtitle is valid.
        :rtype: bool

        """
        text = self.text
        if not text:
            return False

        # valid srt
        try:
            pysrt.from_string(text, error_handling=pysrt.ERROR_RAISE)
        except Exception:
            logger.error("PySRT-parsing failed, trying pysubs2")
        else:
            return True

        # something else, try to return srt
        try:
            logger.debug("Trying parsing with PySubs2")
            try:
                # in case of microdvd, try parsing the fps from the subtitle
                subs = pysubs2.SSAFile.from_string(text)
                if subs.format == "microdvd":
                    logger.info("Got FPS from MicroDVD subtitle: %s", subs.fps)
            except pysubs2.UnknownFPSError:
                # if parsing failed, suggest our media file's fps
                subs = pysubs2.SSAFile.from_string(text, fps=self.plex_media_fps)
                if subs.format == "microdvd":
                    logger.info("Suggested our own media FPS for the MicroDVD subtitle: %s", subs.fps)

            unicontent = self.pysubs2_to_unicode(subs)
            self.content = unicontent.encode(self.guess_encoding())
        except:
            logger.exception("Couldn't convert subtitle %s to .srt format: %s", self, traceback.format_exc())
            return False

        return True

    @classmethod
    def pysubs2_to_unicode(cls, sub):
        def prepare_text(text, style):
            body = []
            for fragment, sty in parse_tags(text, style, sub.styles):
                fragment = fragment.replace(ur"\h", u" ")
                fragment = fragment.replace(ur"\n", u"\n")
                fragment = fragment.replace(ur"\N", u"\n")
                if sty.italic: fragment = u"<i>%s</i>" % fragment
                if sty.underline: fragment = u"<u>%s</u>" % fragment
                if sty.strikeout: fragment = u"<s>%s</s>" % fragment
                body.append(fragment)

            return re.sub(u"\n+", u"\n", u"".join(body).strip())

        visible_lines = (line for line in sub if not line.is_comment)

        out = []

        for i, line in enumerate(visible_lines, 1):
            start = ms_to_timestamp(line.start)
            end = ms_to_timestamp(line.end)
            text = prepare_text(line.text, sub.styles.get(line.style, SSAStyle.DEFAULT_STYLE))

            out.append(u"%d\n" % i)
            out.append(u"%s --> %s\n" % (start, end))
            out.append(u"%s%s" % (text, "\n\n"))

        return u"".join(out)

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
            return self.pysubs2_to_unicode(submods.f).encode(encoding=encoding)
        except UnicodeEncodeError:
            return self.pysubs2_to_unicode(submods.f).encode(encoding="utf-8")

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
