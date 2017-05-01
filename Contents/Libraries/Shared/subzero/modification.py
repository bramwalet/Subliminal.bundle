# coding=utf-8

import re
import traceback
from collections import OrderedDict

import pysubs2
import logging

logger = logging.getLogger(__name__)


class SubtitleModifications(object):
    debug = False

    def __init__(self, debug=False):
        self.debug = debug

    def load(self, fn=None, content=None, fps=None):
        """
        
        :param fn:  filename
        :param content: unicode 
        :param fps: 
        :return: 
        """
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
            applied_mods = []
            for identifier in mods:
                if identifier in registry.mods:
                    mod = registry.mods[identifier]

                    # don't bother reapplying exclusive mods multiple times
                    if mod.exclusive and identifier in applied_mods:
                        continue

                    new_content = mod.modify(line.text, debug=self.debug)
                    if not new_content:
                        if self.debug:
                            logger.debug("%s: deleting %s", identifier, line)
                        continue

                    line.text = new_content
                    new_f.append(line)
                    applied_mods.append(identifier)

        self.f.events = new_f

    def to_string(self, format="srt", encoding="utf-8"):
        return self.f.to_string(format, encoding=encoding)

    def save(self, fn):
        self.f.save(fn)


SubMod = SubtitleModifications


class SubtitleModRegistry(object):
    mods = None
    mods_available = None

    def __init__(self):
        self.mods = OrderedDict()
        self.mods_available = []

    def register(self, mod):
        self.mods[mod.identifier] = mod
        self.mods_available.append(mod.identifier)

registry = SubtitleModRegistry()


class Processor(object):
    """
    Processor base class
    """
    name = None

    def __init__(self, name=None):
        self.name = name

    @property
    def info(self):
        return self.name

    def process(self, content):
        return content

    def __repr__(self):
        return "Processor <%s %s>" % (self.__class__.__name__, self.info)

    def __str__(self):
        return repr(self)

    def __unicode__(self):
        return unicode(repr(self))


class StringProcessor(Processor):
    """
    String replacement processor base
    """

    def __init__(self, search, replace, name=None):
        super(StringProcessor, self).__init__(name=name)
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

    def __init__(self, pattern, replace_with, name=None):
        super(ReProcessor, self).__init__(name=name)
        self.pattern = pattern
        self.replace_with = replace_with

    def process(self, content, debug=False):
        return self.pattern.sub(self.replace_with, content)


class NReProcessor(ReProcessor):
    """
    Single line regex processor
    """

    def process(self, content, debug=False):
        lines = []
        for line in content.split(r"\N"):
            a = super(NReProcessor, self).process(line, debug=debug)
            if not a:
                continue
            lines.append(a)
        return r"\N".join(lines)


class SubtitleModification(object):
    identifier = None
    description = None
    exclusive = False
    pre_processors = []
    processors = []
    post_processors = []

    @classmethod
    def _process(cls, content, processors, debug=False):
        if not content:
            return

        new_content = content
        for processor in processors:
            old_content = new_content
            new_content = processor.process(new_content, debug=debug)
            if not new_content:
                logger.debug("Processor returned empty line: %s", processor)
                break
            if debug:
                if old_content == new_content:
                    #logger.debug("%s: %s stayed the same", processor, old_content)
                    continue
                logger.debug("%s: %s -> %s", processor, old_content, new_content)
        return new_content

    @classmethod
    def pre_process(cls, content, debug=False):
        return cls._process(content, cls.pre_processors, debug=debug)

    @classmethod
    def process(cls, content, debug=False):
        return cls._process(content, cls.processors, debug=debug)

    @classmethod
    def post_process(cls, content, debug=False):
        return cls._process(content, cls.post_processors, debug=debug)

    @classmethod
    def modify(cls, content, debug=False):
        new_content = content
        for method in ("pre_process", "process", "post_process"):
            new_content = getattr(cls, method)(new_content, debug=debug)

        return new_content


class SubtitleTextModification(SubtitleModification):
    post_processors = [
        # empty tag
        ReProcessor(re.compile(r'({\\\w+1})[\s.,-_!?]+({\\\w+0})'), "", name="empty_tag"),

        # empty line (needed?)
        NReProcessor(re.compile(r'^\s+$'), "", name="empty_line"),

        # empty dash line (needed?)
        NReProcessor(re.compile(r'(^[\s]*[\-]+[\s]*)$'), "", name="empty_dash_line"),

        # clean whitespace at start and end
        ReProcessor(re.compile(r'^\s*([^\s]+)\s*$'), r"\1", name="surrounding_whitespace"),
    ]


class HearingImpaired(SubtitleTextModification):
    identifier = "remove_HI"
    description = "Remove Hearing Impaired tags"
    exclusive = True

    processors = [
        # brackets
        NReProcessor(re.compile(r'(?sux)[([].+[)\]]'), "", name="HI_brackets"),

        # text before colon (and possible dash in front)
        NReProcessor(re.compile(r'(?u)(^[A-z\-]+[\w\s]*:[^0-9{2}][\s]*)'), "", name="HI_before_colon"),

        # all caps line (at least 3 chars)
        NReProcessor(re.compile(r'(?u)(^[A-Z]{3,}$)'), "", name="HI_all_caps"),
    ]


registry.register(HearingImpaired)
