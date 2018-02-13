# coding=utf-8

from babelfish import Language as Language_


repl_map = {
    "dk": "da",
}


class Language(Language_):
    @classmethod
    def fromietf(cls, ietf):
        if ietf in repl_map:
            ietf = repl_map[ietf]

        return Language_.fromietf(ietf)
