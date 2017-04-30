# coding=utf-8

import re
import traceback
from collections import OrderedDict

import pysubs2
import logging

logger = logging.getLogger(__name__)


class SubtitleModifications(object):
    def load(self, fn=None, content=None, fps=None):
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
        for line in self.f:
            for identifier in mods:
                if identifier in registry.mods:
                    mod = registry.mods[identifier]
                    new_content = mod.modify(line.text)
                    if not new_content:
                        logger.debug("deleting %s", line)
                        continue

                    line.text = new_content
                    new_f.append(line)

        self.f.events = new_f

    def to_string(self, format="srt"):
        return self.f.to_string(format)

    def save(self, fn):
        self.f.save(fn)


SubMod = SubtitleModifications


class Processor(object):
    """
    Processor base class
    """

    def process(self, content):
        return content


class StringProcessor(Processor):
    """
    String replacement processor base
    """

    def __init__(self, search, replace):
        self.search = search
        self.replace = replace

    def process(self, content):
        return content.replace(self.search, self.replace)


class ReProcessor(Processor):
    """
    Regex processor
    """
    pattern = None
    replace_with = None

    def __init__(self, pattern, replace_with):
        self.pattern = pattern
        self.replace_with = replace_with

    def process(self, content):
        return self.pattern.sub(self.replace_with, content)


class NReProcessor(ReProcessor):
    """
    Single line regex processor
    """

    def process(self, content):
        lines = []
        for line in content.split(r"\N"):
            a = super(NReProcessor, self).process(line)
            if not a:
                continue
            lines.append(a)
        return r"\N".join(lines)


class SubtitleModRegistry(object):
    mods = None

    def __init__(self):
        self.mods = OrderedDict()

    def register(self, mod):
        self.mods[mod.identifier] = mod

registry = SubtitleModRegistry()


class SubtitleModification(object):
    short_name = None
    pre_processors = []
    processors = []
    post_processors = []

    @classmethod
    def _process(cls, content, processors):
        if not content:
            return

        new_content = content
        for processor in processors:
            new_content = processor.process(new_content)
        return new_content

    @classmethod
    def pre_process(cls, content):
        return cls._process(content, cls.pre_processors)

    @classmethod
    def process(cls, content):
        return cls._process(content, cls.processors)

    @classmethod
    def post_process(cls, content):
        return cls._process(content, cls.post_processors)

    @classmethod
    def modify(cls, content):
        new_content = content
        for method in ("pre_process", "process", "post_process"):
            new_content = getattr(cls, method)(new_content)

        return new_content


class SubtitleTextModification(SubtitleModification):
    post_processors = [
        # empty tag
        ReProcessor(re.compile(r'(<[A-z]+[^>]*>)[\s.,-_!?]+(</[A-z]>)'), ""),

        # empty line (needed?)
        ReProcessor(re.compile(r'(?m)^\s+$'), ""),

        # empty dash line (needed?)
        ReProcessor(re.compile(r'(?m)(^[\s]*[\-]+[\s]*)$'), ""),

        # clean whitespace at start and end
        ReProcessor(re.compile(r'^\s*([^\s]+)\s*$'), r"\1"),
    ]


class HearingImpaired(SubtitleTextModification):
    identifier = "remove_HI"
    name = "Remove Hearing Impaired tags"
    processors = [
        # brackets
        ReProcessor(re.compile(r'(?sux)[([{].+[)\]}]'), ""),

        # text before colon (and possible dash in front)
        ReProcessor(re.compile(r'(?mu)(^[A-z\-]+[\w\s]*:[^0-9{2}][\s]*)'), ""),

        # all caps line (at least 3 chars
        NReProcessor(re.compile(r'(?mu)(^[A-Z\.\-_]{3,}$)'), ""),
    ]


registry.register(HearingImpaired)
