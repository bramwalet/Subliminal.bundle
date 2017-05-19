# coding=utf-8

import traceback

import re

import pysubs2
import logging

from pysubs2 import SSAStyle
from pysubs2.subrip import ms_to_timestamp
from pysubs2.substation import parse_tags
from registry import registry

logger = logging.getLogger(__name__)


class SubtitleModifications(object):
    debug = False
    language = None
    initialized_mods = {}

    font_style_tag_start = u"{\\"

    def __init__(self, debug=False):
        self.debug = debug
        self.initialized_mods = {}

    def load(self, fn=None, content=None, language=None, encoding="utf-8"):
        """
        
        :param encoding: used for decoding the content when fn is given, not used in case content is given
        :param language: babelfish.Language language of the subtitle
        :param fn:  filename
        :param content: unicode 
        :return: 
        """
        self.language = language
        self.initialized_mods = {}
        try:
            if fn:
                self.f = pysubs2.load(fn, encoding=encoding)
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
        final_mods = {}
        line_mods = []
        non_line_mods = []

        for identifier, args in parsed_mods:
            if identifier not in registry.mods:
                logger.error("Mod %s not loaded", identifier)
                continue

            mod_cls = registry.mods[identifier]
            # exclusive mod, kill old, use newest
            if identifier in final_mods and mod_cls.exclusive:
                final_mods.pop(identifier)

            # merge args of duplicate mods if possible
            elif identifier in final_mods and mod_cls.args_mergeable:
                final_mods[identifier] = mod_cls.merge_args(final_mods[identifier], args)
                continue
            final_mods[identifier] = args

        # separate all mods into line and non-line mods
        for identifier, args in final_mods.iteritems():
            mod_cls = registry.mods[identifier]
            if mod_cls.modifies_whole_file:
                non_line_mods.append((identifier, args))
            else:
                line_mods.append((mod_cls.order, identifier, args))

            # initialize the mods
            if identifier not in self.initialized_mods:
                self.initialized_mods[identifier] = mod_cls(self)

        # apply file mods
        if non_line_mods:
            for identifier, args in non_line_mods:
                mod = self.initialized_mods[identifier]
                mod.modify(None, debug=self.debug, parent=self, **args)

        # sort line mods
        line_mods.sort(key=lambda x: (x is None, x))

        # apply line mods
        if line_mods:
            for entry in self.f:
                applied_mods = []
                lines = []

                line_count = 0
                for line in entry.text.split(ur"\N"):
                    # don't bother the mods with surrounding tags
                    old_line = line
                    line = line.strip()
                    skip_line = False
                    line_count += 1

                    # clean {\X0} tags before processing
                    start_tag = u""
                    end_tag = u""
                    if line.startswith(self.font_style_tag_start):
                        start_tag = line[:5]
                        line = line[5:]
                    if line[-5:-3] == self.font_style_tag_start:
                        end_tag = line[-5:]
                        line = line[:-5]

                    for order, identifier, args in line_mods:
                        mod = self.initialized_mods[identifier]

                        line = mod.modify(line.strip(), debug=self.debug, parent=self, **args)
                        if not line:
                            if self.debug:
                                logger.debug(u"%s: %r -> ''", identifier, old_line)
                            skip_line = True
                            break

                        applied_mods.append(identifier)

                    if skip_line:
                        continue

                    lines.append(start_tag + line + end_tag)

                if not lines:
                    # don't bother logging when the entry only had one line
                    if self.debug and line_count > 1:
                        logger.debug(u"%r -> ''", entry.text)
                    continue

                # fixme: check for leftover start/endtags
                entry.text = ur"\N".join(lines)
                new_f.append(entry)

        self.f.events = new_f

    def to_unicode(self):
        def prepare_text(text, style):
            body = []
            for fragment, sty in parse_tags(text, style, self.f.styles):
                fragment = fragment.replace(ur"\h", u" ")
                fragment = fragment.replace(ur"\n", u"\n")
                fragment = fragment.replace(ur"\N", u"\n")
                if sty.italic: fragment = u"<i>%s</i>" % fragment
                if sty.underline: fragment = u"<u>%s</u>" % fragment
                if sty.strikeout: fragment = u"<s>%s</s>" % fragment
                body.append(fragment)

            return re.sub(u"\n+", u"\n", u"".join(body).strip())

        visible_lines = (line for line in self.f if not line.is_comment)

        out = []

        for i, line in enumerate(visible_lines, 1):
            start = ms_to_timestamp(line.start)
            end = ms_to_timestamp(line.end)
            text = prepare_text(line.text, self.f.styles.get(line.style, SSAStyle.DEFAULT_STYLE))

            out.append(u"%d\n" % i)
            out.append(u"%s --> %s\n" % (start, end))
            out.append(u"%s%s" % (text, "\n\n"))

        return u"".join(out)

SubMod = SubtitleModifications




