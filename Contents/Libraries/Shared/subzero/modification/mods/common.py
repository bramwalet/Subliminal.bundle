# coding=utf-8

import re

from subzero.modification.processors import Processor
from subzero.modification.mods import SubtitleTextModification
from subzero.modification.processors.string_processor import StringProcessor
from subzero.modification.processors.re_processor import NReProcessor
from subzero.modification import registry


class CleanLineProcessor(Processor):
    def process(self, content, debug=False):
        return r"\N".join(line.strip() for line in content.split(r"\N"))


class CommonFixes(SubtitleTextModification):
    identifier = "common"
    description = "Basic common fixes"
    exclusive = True
    order = 40

    long_description = """\
    Fix common whitespace/punctuation issues in subtitles
    """

    processors = [
        # surrounding spaces
        CleanLineProcessor(name="CM_cleanline"),

        # -- = ...
        StringProcessor("-- ", '... ', name="CM_doubledash"),

        # remove leading ...
        NReProcessor(re.compile(r'(?u)^\.\.\.[\s]*'), "", name="CM_leading_ellipsis"),

        # no space after ellipsis
        NReProcessor(re.compile(r'(?u)\.\.\.(?![\s.,!?\'"])(?!$)'), "... ", name="CM_ellipsis_no_space"),

        # multiple spaces
        NReProcessor(re.compile(r'(?u)[\s]{2,}'), " ", name="CM_multiple_spaces"),

        # no space after starting dash
        NReProcessor(re.compile(r'(?u)^-(?![\s-])'), "- ", name="CM_dash_space"),

        # '' = "
        StringProcessor("''", '"', name="CM_double_apostrophe"),

        # remove starting spaced dots (not matching ellipses
        NReProcessor(re.compile(r'(?u)^(?!\s?(\.\s\.\s\.)|(\s?\.{3}))[\s.]*'), "", name="CM_starting_spacedots"),

        # space missing before doublequote
        # ReProcessor(re.compile(r'(?u)(?<!^)(?<![\s(\["])("[^"]+")'), r' \1', name="CM_space_before_dblquote"),

        # space missing after doublequote
        # ReProcessor(re.compile(r'(?u)("[^"\s][^"]+")([^\s.,!?)\]]+)'), r"\1 \2", name="CM_space_after_dblquote"),

        # space before ending doublequote?

        # remove >>
        NReProcessor(re.compile(r'(?u)^\s?>>\s*'), "", name="CM_leading_crocodiles"),

        # replace uppercase I with lowercase L in words
        NReProcessor(re.compile(ur'(?u)([A-zÀ-ž]+)I([à-ž]+)'), r"\1l\2", name="CM_uppercase_i_in_word"),

        # fix spaces in numbers (allows for punctuation: ,.:' (comma only fixed if after space, those may be
        # countdowns otherwise)
        # fixme: maybe check whether it's a countdown (second part smaller than the first), otherwise handle default?
        NReProcessor(re.compile(r'(?u)([0-9]+[0-9.:\']*)\s+([0-9,.:\']*[0-9]+)'), r"\1\2", name="CM_spaces_in_numbers"),

        # uppercase after dot
        NReProcessor(re.compile(ur'(?u)((?:[^.\s])+\.\s+)([a-zà-ž])'),
                     lambda match: ur'%s%s' % (match.group(1), match.group(2).upper()), name="CM_uppercase_after_dot"),
    ]


registry.register(CommonFixes)
