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

    def load(self, fn=None, content=None, language=None):
        """
        
        :param language: babelfish.Language language of the subtitle
        :param fn:  filename
        :param content: unicode 
        :return: 
        """
        self.language = language
        self.initialized_mods = {}
        try:
            if fn:
                self.f = pysubs2.load(fn)
            elif content:
                self.f = pysubs2.SSAFile.from_string(content)
        except (IOError,
                UnicodeDecodeError,
                pysubs2.exceptions.UnknownFPSError,
                pysubs2.exceptions.UnknownFormatIdentifierError,
                pysubs2.exceptions.FormatAutodetectionError):
            if fn:
                logger.exception("Couldn't load subtitle: %s: %s", fn, traceback.format_exc())
            elif content:
                logger.exception("Couldn't load subtitle: %s", traceback.format_exc())

    @classmethod
    def parse_identifier(cls, identifier):
        # simple identifier
        if identifier in registry.mods:
            return identifier, {}

        # identifier with params; identifier(param=value)
        split_args = identifier[identifier.find("(")+1:-1].split(",")
        args = dict((key, value) for key, value in [sub.split("=") for sub in split_args])
        return identifier[:identifier.find("(")], args

    @classmethod
    def get_mod_class(cls, identifier):
        identifier, args = cls.parse_identifier(identifier)
        return registry.mods[identifier]

    @classmethod
    def get_mod_signature(cls, identifier, **kwargs):
        return cls.get_mod_class(identifier).get_signature(**kwargs)

    def modify(self, *mods):
        new_f = []

        parsed_mods = [SubtitleModifications.parse_identifier(mod) for mod in mods]
        line_mods = []
        non_line_mods = []

        print parsed_mods
        for identifier, args in parsed_mods:
            if identifier not in registry.mods:
                raise NotImplementedError("Mod %s not loaded" % identifier)

            mod_cls = registry.mods[identifier]
            if mod_cls.modifies_whole_file:
                non_line_mods.append((identifier, args))
            else:
                line_mods.append((identifier, args))

            if identifier not in self.initialized_mods:
                self.initialized_mods[identifier] = mod_cls(self)

        # apply file mods
        if non_line_mods:
            for identifier, args in non_line_mods:
                mod = self.initialized_mods[identifier]
                mod.modify(None, debug=self.debug, parent=self, **args)

        # apply line mods
        if line_mods:
            for line in self.f:
                applied_mods = []
                for identifier, args in line_mods:
                    mod = self.initialized_mods[identifier]

                    # don't bother reapplying exclusive mods multiple times
                    if mod.exclusive and identifier in applied_mods:
                        continue

                    if not mod.processors:
                        continue

                    new_content = mod.modify(line.text, debug=self.debug, parent=self, **args)
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




