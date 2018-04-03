# coding=utf-8

import inspect

from support.config import config


core = getattr(Data, "_core")


# get original localization module in order to access its base classes later on
def get_localization_module():
    cls = getattr(core.localization, "__class__")
    return inspect.getmodule(cls)


plex_i18n_module = get_localization_module()


class SmartLocalStringFormatter(plex_i18n_module.LocalStringFormatter):
    """
    this allows the use of dictionaries for string formatting, also does some sanity checking on the keys and values
    """
    def __init__(self, string1, string2, locale=None):
        setattr(self, "_string1", string1)

        if isinstance(string2, tuple) and len(string2) == 1 and hasattr(string2[0], "iteritems"):
            string2 = string2[0]
            if config.debug_i18n:
                if "%(" not in string1.__str__():
                    Log.Error(u"%r: dictionary for non-named format string supplied" % string1)
                    string2 = "BROKEN STRING"

        setattr(self, "_string2", string2)
        setattr(self, "_locale", locale)


def local_string_with_optional_format(key, *args, **kwargs):
    if kwargs:
        args = (kwargs,)
    else:
        args = tuple(args)

    if args:
        return SmartLocalStringFormatter(plex_i18n_module.LocalString(core, key, Locale.CurrentLocale), args)

    # check string instances for arguments
    if config.debug_i18n:
        k = key.__str__().replace("%%", "")
        if ("%s" in k or "%(" in k) and not args:
            Log.Error(u"%r requires a arguments for formatting" % k)
            return "NEEDS FORMAT ARGUMENTS"

    return plex_i18n_module.LocalString(core, key, Locale.CurrentLocale)


_ = local_string_with_optional_format


def is_localized_string(s):
    return hasattr(s, "localize")
