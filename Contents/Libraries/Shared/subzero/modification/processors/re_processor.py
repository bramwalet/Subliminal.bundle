# coding=utf-8
import re
import logging

from subzero.modification.processors import Processor

logger = logging.getLogger(__name__)


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

    font_style_tag_start = u"{\\"

    def process(self, content, debug=False):
        lines = []
        for line in content.split(r"\N"):
            a = line.strip()
            # clean {\X0} tags
            start_tag = u""
            end_tag = u""
            if a.startswith(self.font_style_tag_start):
                start_tag = a[:5]
                a = a[5:]
            if a[-5:-3] == self.font_style_tag_start:
                end_tag = a[-5:]
                a = a[:-5]

            a = super(NReProcessor, self).process(a, debug=debug)
            if not a:
                continue
            lines.append(start_tag + a + end_tag)
        return r"\N".join(lines)


class MultipleWordReProcessor(ReProcessor):
    """
    Expects a dictionary in the form of:
    dict = {
        "data": {"old_value": "new_value"},
        "pattern": compiled re object that matches data.keys()
    }
    replaces found key in pattern with the corresponding value in data
    """
    def __init__(self, snr_dict, name=None, parent=None):
        super(ReProcessor, self).__init__(name=name)
        self.snr_dict = snr_dict

    def process(self, content, debug=False):
        if not self.snr_dict["data"]:
            return content

        out = []
        for a in content.split(ur"\N"):
            out.append(self.snr_dict["pattern"].sub(lambda x: self.snr_dict["data"][x.group(0)], a))
        return ur"\N".join(out)

