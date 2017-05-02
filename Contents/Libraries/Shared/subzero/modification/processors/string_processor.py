# coding=utf-8
from subzero.modification.processors import Processor


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
