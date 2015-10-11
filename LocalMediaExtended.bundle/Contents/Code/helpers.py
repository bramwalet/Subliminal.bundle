import unicodedata

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