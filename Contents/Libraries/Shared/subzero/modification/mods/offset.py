# coding=utf-8

import logging

from subzero.modification.mods import SubtitleModification
from subzero.modification import registry

logger = logging.getLogger(__name__)


class ShiftOffset(SubtitleModification):
    identifier = "shift_offset"
    description = "Change the timing of the subtitle"
    exclusive = True
    advanced = True
    modifies_whole_file = True

    long_description = """\
    Adds or substracts a certain amount of time from the whole subtitle to match your media 
    """

    def modify(self, content, debug=False, parent=None, **kwargs):
        parent.f.shift(h=int(kwargs.get("h", 0)), m=int(kwargs.get("m", 0)), s=int(kwargs.get("s", 0)),
                       ms=int(kwargs.get("ms", 0)))


registry.register(ShiftOffset)
