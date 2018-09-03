# coding=utf-8
from babelfish.exceptions import LanguageError

from babelfish import Language as Language_


repl_map = {
    "dk": "da",
    "nld": "nl",
    "english": "en",
}


def language_from_stream(l):
    if not l:
        raise LanguageError()
    for method in ("fromietf", "fromalpha3t", "fromalpha3b"):
        try:
            return getattr(Language, method)(l)
        except (LanguageError, ValueError):
            pass
    raise LanguageError()


def wrap_forced(f):
    def inner(*args):
        args = list(args)[1:]
        s = args.pop(0)
        base, forced = s.split(":")
        instance = f(base, *args)
        instance.forced = forced == "forced"
        return instance

    return inner


class Language(Language_):
    def __init__(self, language, country=None, script=None, unknown=None, forced=False):
        super(Language, self).__init__(language, country=country, script=script, unknown=unknown)
        self.forced = forced

    def __getstate__(self):
        return self.alpha3, self.country, self.script, self.forced

    def __setstate__(self, state):
        self.alpha3, self.country, self.script, self.forced = state

    def __eq__(self, other):
        if isinstance(other, Language):
            return super(Language, self).__eq__(other) and other.forced == self.forced
        return super(Language, self).__eq__(other)

    def __str__(self):
        return super(Language, self).__str__() + (":forced" if self.forced else "")

    def __getattr__(self, name):
        ret = super(Language, self).__getattr(name)
        if ret:
            ret.forced = self.forced
            return ret

    @classmethod
    @wrap_forced
    def fromcode(cls, code, converter):
        return Language_.fromcode(code, converter)

    @classmethod
    @wrap_forced
    def fromietf(cls, ietf):
        ietf_lower = ietf.lower()
        if ietf_lower in repl_map:
            ietf = repl_map[ietf_lower]

        return Language_.fromietf(ietf)

    @classmethod
    @wrap_forced
    def fromalpha3b(cls, s):
        if s in repl_map:
            s = repl_map[s]
            return Language_.fromietf(s)

        return Language_.fromalpha3b(s)
