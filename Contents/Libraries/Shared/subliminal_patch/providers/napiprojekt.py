# coding=utf-8

from subliminal.providers.napiprojekt import NapiProjektProvider as _NapiProjektProvider, \
    NapiProjektSubtitle as _NapiProjektSubtitle


class NapiProjektSubtitle(_NapiProjektSubtitle):
    def __init__(self, language, hash):
        super(NapiProjektSubtitle, self).__init__(language, hash)
        self.release_info = hash


class NapiProjektProvider(_NapiProjektProvider):
    subtitle_class = NapiProjektSubtitle
