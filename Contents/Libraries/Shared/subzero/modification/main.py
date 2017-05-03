# coding=utf-8

import traceback
import pysubs2
import logging

from registry import registry

logger = logging.getLogger(__name__)


class SubtitleModifications(object):
    debug = False
    language = None
    initialized_mods = {}

    def __init__(self, debug=False):
        self.debug = debug
        self.initialized_mods = {}

    def load(self, fn=None, content=None, fps=None, language=None):
        """
        
        :param language: babelfish.Language language of the subtitle
        :param fn:  filename
        :param content: unicode 
        :param fps: 
        :return: 
        """
        self.language = language
        try:
            if fn:
                self.f = pysubs2.load(fn, fps=fps)
            elif content:
                self.f = pysubs2.SSAFile.from_string(content, fps=fps)
        except (IOError,
                UnicodeDecodeError,
                pysubs2.exceptions.UnknownFPSError,
                pysubs2.exceptions.UnknownFormatIdentifierError,
                pysubs2.exceptions.FormatAutodetectionError):
            if fn:
                logger.exception("Couldn't load subtitle: %s: %s", fn, traceback.format_exc())
            elif content:
                logger.exception("Couldn't load subtitle: %s", traceback.format_exc())

    def modify(self, *mods):
        new_f = []

        for identifier in mods:
            if identifier not in registry.mods:
                raise NotImplementedError("Mod %s not loaded" % identifier)

        for line in self.f:
            applied_mods = []
            for identifier in mods:
                if identifier in registry.mods:
                    if identifier not in self.initialized_mods:
                        self.initialized_mods[identifier] = registry.mods[identifier](self)
                    mod = self.initialized_mods[identifier]

                    # don't bother reapplying exclusive mods multiple times
                    if mod.exclusive and identifier in applied_mods:
                        continue

                    if not mod.processors:
                        continue

                    new_content = mod.modify(line.text, debug=self.debug, parent=self)
                    if not new_content:
                        if self.debug:
                            logger.debug("%s: deleting %s", identifier, line)
                        continue

                    line.text = new_content
                    applied_mods.append(identifier)
            new_f.append(line)

        self.f.events = new_f

    def to_string(self, format="srt", encoding="utf-8"):
        return self.f.to_string(format, encoding=encoding)

    def save(self, fn):
        self.f.save(fn)


SubMod = SubtitleModifications




