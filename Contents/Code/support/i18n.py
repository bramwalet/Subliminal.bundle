# coding=utf-8

import inspect

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
            if not is_localized_string(string1) and "%(" not in string1:
                Log.Error(u"%s requires a dictionary for formatting" % string1)
            string2 = string2[0]

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
    if not is_localized_string(key) and ("%s" in key or "%(" in key) and not args:
        raise Log.Error(u"%s requires a arguments for formatting" % key)

    return plex_i18n_module.LocalString(core, key, Locale.CurrentLocale)


_ = local_string_with_optional_format


def is_localized_string(s):
    return hasattr(s, "localize")
