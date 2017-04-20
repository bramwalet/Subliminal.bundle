# coding=utf-8
from subliminal.extensions import RegistrableExtensionManager

refiner_manager = RegistrableExtensionManager('subliminal.refiners', [
    'metadata = subliminal_patch.refiners.metadata:refine',
    'omdb = subliminal.refiners.omdb:refine',
    'tvdb = subliminal.refiners.tvdb:refine'
])
