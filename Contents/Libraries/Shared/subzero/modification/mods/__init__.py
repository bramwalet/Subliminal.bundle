# coding=utf-8
import re
import logging

from subzero.modification.processors.re_processor import ReProcessor, NReProcessor

logger = logging.getLogger(__name__)


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
                if debug:
                    logger.debug("Processor returned empty line: %s", processor)
                break
            if debug:
                if old_content == new_content:
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
