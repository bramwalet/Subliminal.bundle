# coding=utf-8

import unicodedata
import datetime
import urllib
import time
import re

from subzero import iter

# Unicode control characters can appear in ID3v2 tags but are not legal in XML.

RE_UNICODE_CONTROL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                     u'|' + \
                     u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                     (
                         unichr(0xd800), unichr(0xdbff), unichr(0xdc00), unichr(0xdfff),
                         unichr(0xd800), unichr(0xdbff), unichr(0xdc00), unichr(0xdfff),
                         unichr(0xd800), unichr(0xdbff), unichr(0xdc00), unichr(0xdfff)
                     )


# A platform independent way to split paths which might come in with different separators.
def splitPath(str):
    if str.find('\\') != -1:
        return str.split('\\')
    else:
        return str.split('/')


def unicodize(s):
    filename = s
    try:
        filename = unicodedata.normalize('NFC', unicode(s.decode('utf-8')))
    except:
        Log('Failed to unicodize: ' + filename)
    try:
        filename = re.sub(RE_UNICODE_CONTROL, '', filename)
    except:
        Log('Couldn\'t strip control characters: ' + filename)
    return filename


def cleanFilename(filename):
    # this will remove any whitespace and punctuation chars and replace them with spaces, strip and return as lowercase
    return string.translate(filename.encode('utf-8'), string.maketrans(string.punctuation + string.whitespace,
                                                                       ' ' * len(string.punctuation + string.whitespace))).strip().lower()


def is_recent(t):
    now = datetime.datetime.now()
    when = datetime.datetime.fromtimestamp(t)
    value, key = Prefs["scheduler.item_is_recent_age"].split()
    if now - datetime.timedelta(**{key: int(value)}) < when:
        return True
    return False


# thanks, Plex-Trakt-Scrobbler
def str_pad(s, length, align='left', pad_char=' ', trim=False):
    if not s:
        return s

    if not isinstance(s, (str, unicode)):
        s = str(s)

    if len(s) == length:
        return s
    elif len(s) > length and not trim:
        return s

    if align == 'left':
        if len(s) > length:
            return s[:length]
        else:
            return s + (pad_char * (length - len(s)))
    elif align == 'right':
        if len(s) > length:
            return s[len(s) - length:]
        else:
            return (pad_char * (length - len(s))) + s
    else:
        raise ValueError("Unknown align type, expected either 'left' or 'right'")


def pad_title(value):
    """Pad a title to 30 characters to force the 'details' view."""
    return str_pad(value, 30, pad_char=' ')


def format_item(item, kind, parent=None, parent_title=None, section_title=None, add_section_title=False):
    """
    :param item: plex item
    :param kind: show or movie
    :param parent: season or None
    :param parent_title: parentTitle or None
    :return:
    """
    return format_video(kind, item.title,
                        section_title=(section_title or (parent.section.title if parent and getattr(parent, "section") else None)),
                        parent_title=(parent_title or (parent.show.title if parent else None)),
                        season=parent.index if parent else None,
                        episode=item.index if kind == "show" else None,
                        add_section_title=add_section_title)


def format_video(kind, title, section_title=None, parent_title=None, season=None, episode=None, add_section_title=False):
    section_add = ""
    if add_section_title:
        section_add = ("%s: " % section_title) if section_title else ""

    if kind == "show" and parent_title:
        if season and episode:
            return '%s%s S%02dE%02d, %s' % (section_add, parent_title, season or 0, episode or 0, title)
        return '%s%s, %s' % (section_add, parent_title, title)
    return "%s%s" % (section_add, title)


def encode_message(base, s):
    return "%s?message=%s" % (base, urllib.quote_plus(s))


def decode_message(s):
    return urllib.unquote_plus(s)


def timestamp():
    return int(time.time())


def query_plex(url, args):
    """
    simple http query to the plex API without parsing anything too complicated
    :param url:
    :param args:
    :return:
    """
    use_args = args.copy()
    if "token" in Dict and Dict["token"]:
        use_args["X-Plex-Token"] = Dict["token"]

    computed_args = "&".join(["%s=%s" % (key, String.Quote(value)) for key, value in use_args.iteritems()])

    return HTTP.Request(url + ("?%s" % computed_args) if computed_args else "", immediate=True)


class DictProxy(object):
    store = None

    patch_sandbox_methods = ("cmp", "contains", "unicode")

    def __init__(self):
        super(DictProxy, self).__init__()

        # we can't define some methods due to the plex sandbox, dynamically set them
        for item in self.patch_sandbox_methods:
            setattr(self, "__%s__" % item, getattr(self, "%s__" % item))

        if self.store not in Dict or not Dict[self.store]:
            Dict[self.store] = self.setup_defaults()

    def __getattr__(self, name):
        if name in Dict[self.store]:
            return Dict[self.store][name]
        return getattr(super(DictProxy, self), name)

    def cmp__(self, d):
        return cmp(Dict[self.store], d)

    def contains__(self, item):
        return item in Dict[self.store]

    def __setitem__(self, key, item):
        Dict[self.store][key] = item

    def __iter__(self):
        return iter(Dict[self.store])

    def __getitem__(self, key):
        if key in Dict[self.store]:
            return Dict[self.store][key]

    def __repr__(self):
        return repr(Dict[self.store])

    def __str__(self):
        return str(Dict[self.store])

    def __len__(self):
        return len(Dict[self.store].keys())

    def __delitem__(self, key):
        del Dict[self.store][key]

    def clear(self):
        del Dict[self.store]
        return None

    def copy(self):
        return Dict[self.store].copy()

    def has_key(self, k):
        return k in Dict[self.store]

    def pop(self, k, d=None):
        return Dict[self.store].pop(k, d)

    def update(self, *args, **kwargs):
        return Dict[self.store].update(*args, **kwargs)

    def keys(self):
        return Dict[self.store].keys()

    def values(self):
        return Dict[self.store].values()

    def items(self):
        return Dict[self.store].items()

    def unicode__(self):
        return unicode(repr(Dict[self.store]))

    def setup_defaults(self):
        raise NotImplementedError
