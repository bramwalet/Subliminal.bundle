# coding=utf-8
import subliminal
import babelfish
from subliminal.extensions import RegistrableExtensionManager

provider_manager = RegistrableExtensionManager('subliminal.providers', [
    'addic7ed = subliminal_patch.providers.addic7ed:Addic7edProvider',
    'legendastv = subliminal_patch.providers.legendastv:LegendasTVProvider',
    'opensubtitles = subliminal_patch.providers.opensubtitles:OpenSubtitlesProvider',
    'podnapisi = subliminal_patch.providers.podnapisi:PodnapisiProvider',
    'shooter = subliminal.providers.shooter:ShooterProvider',
    'napiprojekt = subliminal_patch.providers.napiprojekt:NapiProjektProvider',
    'subscenter = subliminal.providers.subscenter:SubsCenterProvider',
    'thesubdb = subliminal.providers.thesubdb:TheSubDBProvider',
    'tvsubtitles = subliminal_patch.providers.tvsubtitles:TVsubtitlesProvider'
])

# add language converters
babelfish.language_converters.unregister('addic7ed = subliminal.converters.addic7ed:Addic7edConverter')
babelfish.language_converters.register('addic7ed = subliminal_patch.language:PatchedAddic7edConverter')
subliminal.refiner_manager.register('sz_metadata = subliminal_patch.refiners.metadata:refine')

