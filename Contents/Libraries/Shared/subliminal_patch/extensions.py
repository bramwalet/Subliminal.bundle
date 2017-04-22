# coding=utf-8
from subliminal.extensions import RegistrableExtensionManager

provider_manager = RegistrableExtensionManager('subliminal.providers', [
    'addic7ed = subliminal_patch.providers.addic7ed:Addic7edProvider',
    'legendastv = subliminal.providers.legendastv:LegendasTVProvider',
    'opensubtitles = subliminal_patch.providers.opensubtitles:OpenSubtitlesProvider',
    'podnapisi = subliminal_patch.providers.podnapisi:PodnapisiProvider',
    'shooter = subliminal.providers.shooter:ShooterProvider',
    'subscenter = subliminal.providers.subscenter:SubsCenterProvider',
    'thesubdb = subliminal.providers.thesubdb:TheSubDBProvider',
    'tvsubtitles = subliminal.providers.tvsubtitles:TVsubtitlesProvider'
])
