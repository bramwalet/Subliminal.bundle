# coding=utf-8

import importlib
import os
from subliminal.providers import Provider as _Provider
from subliminal.subtitle import Subtitle as _Subtitle
from subliminal_patch.extensions import provider_registry
from subliminal_patch.http import RetryingSession
from subliminal_patch.subtitle import Subtitle

from subzero.lib.io import get_viable_encoding

class Provider(_Provider):
    hash_verifiable = False
    hearing_impaired_verifiable = False
    skip_wrong_fps = True


# register providers
for name in os.listdir(os.path.dirname(unicode(__file__, get_viable_encoding()))):
    if name in ("__init__.py", "mixins.py", "utils.py") or not name.endswith(".py"):
        continue

    module_name = os.path.splitext(name)[0]
    mod = importlib.import_module("subliminal_patch.providers.%s" % module_name.lower())
    for item in dir(mod):
        if item.endswith("Provider") and not item.startswith("_"):
            provider_class = getattr(mod, item)
            is_sz_provider = issubclass(provider_class, Provider)

            if not is_sz_provider:
                # patch provider bases
                new_bases = []
                for base in provider_class.__bases__:
                    if issubclass(base, _Provider):
                        base.__bases__ = (Provider,)
                    new_bases.append(base)

                provider_class.__bases__ = tuple(new_bases)

                # patch subtitle bases
                new_bases = []
                for base in provider_class.subtitle_class.__bases__:
                    if issubclass(base, _Subtitle):
                        base.__bases__ = (Subtitle,)
                    new_bases.append(base)

                provider_class.subtitle_class.__bases__ = tuple(new_bases)

            # inject our requests.Session wrapper for automatic retry
            mod.Session = RetryingSession

            provider_registry.register(module_name, provider_class)

    # try patching the correspondent subliminal provider
    try:
        subliminal_mod = importlib.import_module("subliminal.providers.%s" % module_name.lower())
    except ImportError:
        pass
    else:
        subliminal_mod.Session = RetryingSession

