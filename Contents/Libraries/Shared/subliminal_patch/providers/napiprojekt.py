# coding=utf-8

from subliminal.providers.napiprojekt import NapiProjektProvider as _NapiProjektProvider, \
    NapiProjektSubtitle as _NapiProjektSubtitle


class NapiProjektSubtitle(_NapiProjektSubtitle):
    def __init__(self, language, hash):
        super(NapiProjektSubtitle, self).__init__(language, hash)
        self.release_info = hash

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, self.release_info, self.language)


class NapiProjektProvider(_NapiProjektProvider):
    subtitle_class = NapiProjektSubtitle
