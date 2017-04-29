# coding=utf-8

import re
import pysubs2

characters_considered_empty_when_alone = r"[\s.,-_!?]"


class SubtitleModifications(object):
    def __init__(self, fn):
        self.f = pysubs2.load("test.srt")

    def modify(self, *mods):
        new_f = []
        for key, line in enumerate(self.f):
            for mod in mods:
                new_content = mod.modify(line.text)
                if not new_content:
                    print "deleting %s", line
                    continue

                line.text = new_content
                new_f.append(line)

        self.f.events = new_f

    def save(self, fn):
        self.f.save(fn)

SubMod = SubtitleModifications


class Processor(object):
    def process(self, content):
        return content


class StringProcessor(Processor):
    def __init__(self, search, replace):
        self.search = search
        self.replace = replace

    def process(self, content):
        return content.replace(self.search, self.replace)


class ReProcessor(Processor):
    pattern = None
    replace_with = None

    def __init__(self, pattern, replace_with):
        self.pattern = pattern
        self.replace_with = replace_with

    def process(self, content):
        return re.sub(self.pattern, self.replace_with, content)


class NReProcessor(ReProcessor):
    def process(self, content):
        lines = []
        for line in content.split(r"\N"):
            a = super(NReProcessor, self).process(line)
            if not a:
                continue
            lines.append(a)
        return r"\N".join(lines)


class SubtitleModification(object):
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
        ReProcessor(r'(<[A-z]+[^>]*>)%s+(</[A-z]>)' % characters_considered_empty_when_alone, ""),

        # empty line (needed?)
        ReProcessor(r'(?m)^\s+$', ""),

        # empty dash line (needed?)
        ReProcessor(r'(?m)(^[\s]*[\-]+[\s]*)$', ""),

        # clean start or end
        ReProcessor(r'^\s*([^\s]+)\s*$', r"\1"),
    ]


class HearingImpaired(SubtitleTextModification):
    processors = [
        # brackets
        ReProcessor(r'(?sux)[([{].+[)\]}]', ""),

        # text before colon
        ReProcessor(r'(?mu)(^[A-z\-]+[\w\s]*:[^0-9{2}][\s]*)', ""),

        # all caps line
        NReProcessor(r'(?mu)(^[A-Z\.\-_]+$)', ""),
    ]

