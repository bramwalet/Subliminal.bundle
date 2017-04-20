# coding=utf-8

from subliminal.converters.addic7ed import Addic7edConverter


class PatchedAddic7edConverter(Addic7edConverter):
    def __init__(self):
        super(PatchedAddic7edConverter, self).__init__()
        self.from_addic7ed.update({
            "French (Canadian)": ("fra", "CA"),
        })
        self.to_addic7ed.update({
            ("fra", "CA"): "French (Canadian)",
        })
