# coding=utf-8

import logging

from subzero.modification.mods import SubtitleModification
from subzero.modification import registry

logger = logging.getLogger(__name__)


class Color(SubtitleModification):
    identifier = "color"
    description = "Change the color of the subtitle"
    exclusive = True
    advanced = True

    long_description = """\
    Adds the requested color to every line of the subtitle. Support depends on player.
    """

    def modify(self, content, debug=False, parent=None, **kwargs):
        color = kwargs.get("color")
        if color:
            return u'<font color="%s">%s</font>' % (color, content)


registry.register(Color)
