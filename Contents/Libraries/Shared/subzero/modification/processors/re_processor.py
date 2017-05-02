# coding=utf-8
from subzero.modification.processors import Processor


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
