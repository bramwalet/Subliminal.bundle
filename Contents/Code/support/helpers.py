# coding=utf-8

import unicodedata
import datetime
import urllib
import time

# Unicode control characters can appear in ID3v2 tags but are not legal in XML.
RE_UNICODE_CONTROL =  u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                      u'|' + \
                      u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                      (
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff)
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
  #this will remove any whitespace and punctuation chars and replace them with spaces, strip and return as lowercase
  return string.translate(filename.encode('utf-8'), string.maketrans(string.punctuation + string.whitespace, ' ' * len (string.punctuation + string.whitespace))).strip().lower()

now = datetime.datetime.now()
def is_recent(item):
    addedAt =  datetime.datetime.fromtimestamp(item.added_at)
    value, key = Prefs["scheduler.item_is_recent_age"].split()
    if now - datetime.timedelta(**{key: int(value)}) > addedAt:
        return False
    return True

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

def format_video(item, kind, parent=None, parentTitle=None):
    if kind == "episode" and parent:
	return unicode('%s S%02dE%02d' % (parentTitle or parent.show.title, parent.index, item.index)).encode("ascii", errors="ignore")
    return unicode(item.title).encode("ascii", errors="ignore")

def encode_message(base, s):
    return "%s?message=%s" % (base, urllib.quote_plus(s))

def decode_message(s):
    return urllib.unquote_plus(s)

def timestamp():
    return int(time.time())