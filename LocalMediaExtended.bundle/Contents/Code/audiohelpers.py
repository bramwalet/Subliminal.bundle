import os
import helpers

from mutagen import File as MFile
from mutagen.flac import Picture

class AudioHelper(object):
  def __init__(self, filename):
    self.filename = filename

def AudioHelpers(filename):
  filename = helpers.unicodize(filename)
  try:
    tag = MFile(filename, None, True)
  except Exception, e:
    Log('Error getting file details for %s: %s' % (filename, e))
    return None

  if tag is not None:
    for cls in [ ID3AudioHelper, MP4AudioHelper, FLACAudioHelper, OGGAudioHelper ]:
      if cls.is_helper_for(type(tag).__name__):
        return cls(filename)
  return None


def parse_genres(genre):
  if genre.find(';') != -1:
    genre_list = genre.split(';')
  else:
    genre_list = genre.split('/')
    
  return genre_list


#####################################################################################################################

class ID3AudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, tagType):
    return tagType in ('EasyID3', 'EasyMP3', 'EasyTrueAudio', 'ID3', 'MP3', 'TrueAudio', 'AIFF') # All of these file types use ID3 tags like MP3

  def get_album_sort_title(self):
    return self.tags.get('TSOA')
    
  def get_track_sort_title(self):
    return self.tags.get('TSOT')
    
  def get_artist_sort_title(self):
    try:
      self.tags = tags = MFile(self.filename)
      tag = self.tags.get('TSO2')
      if tag:
        return tag
    
      return self.tags.get('TSOP')
    except:
      pass
      
    return None

  def process_metadata(self, metadata):
    
    Log('Reading ID3 tags from: ' + self.filename)
    try:
      self.tags = tags = MFile(self.filename)
      Log('Found tags: ' + str(tags.keys()))
    except: 
      Log('An error occurred while attempting to read ID3 tags from ' + self.filename)
      return

    # Release Date
    try:
      year = tags.get('TDRC')
      if year is not None and len(year.text) > 0:
        metadata.originally_available_at = Datetime.ParseDate('01-01-' + str(year.text[0])).date()
    except Exception, e:
      Log('Exception reading TDRC (year): ' + str(e))

    # Genres
    try:
      genres = tags.get('TCON')
      if genres is not None and len(genres.text) > 0:
        metadata.genres.clear()
        for genre in genres.text:
          for sub_genre in parse_genres(genre):
            metadata.genres.add(sub_genre.strip())
    except Exception, e:
      Log('Exception reading TCON (genre): ' + str(e))

    # Posters
    try:
      valid_posters = []
      frames = [f for f in tags if f.startswith('APIC:')]
      for frame in frames:
        if (tags[frame].mime == 'image/jpeg') or (tags[frame].mime == 'image/jpg'): ext = 'jpg'
        elif tags[frame].mime == 'image/png': ext = 'png'
        elif tags[frame].mime == 'image/gif': ext = 'gif'
        else: ext = ''

        poster_name = hashlib.md5(tags[frame].data).hexdigest()
        valid_posters.append(poster_name)
        if poster_name not in metadata.posters:
          Log('Adding embedded APIC art: ' + poster_name)
          metadata.posters[poster_name] = Proxy.Media(tags[frame].data, ext = ext)
    except Exception, e:
      Log('Exception adding posters: ' + str(e))

    return valid_posters

#####################################################################################################################

class MP4AudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, tagType):
    return tagType in ['MP4','EasyMP4']

  def get_track_sort_title(self):
    try:
      tags = MFile(self.filename, easy=True)
      return tags.get('titlesort')[0]  # 'sonm'
    except:      
      return None

  def get_album_sort_title(self):
    try:
      tags = MFile(self.filename, easy=True)
      return tags.get('albumsort')[0]  # 'soal'
    except:      
      return None
        
  def get_artist_sort_title(self):
    try:
      tags = MFile(self.filename, easy=True)
      return tags.get('artistsort')[0]  # 'soar'
    except:      
      return None

  def process_metadata(self, metadata):

    Log('Reading MP4 tags from: ' + self.filename)
    try: 
      tags = MFile(self.filename)
      Log('Found tags: ' + str(tags.keys()))
    except: 
      Log('An error occurred while attempting to parse the MP4 file: ' + self.filename)
      return

    # Genres
    try:
      genres = tags.get('\xa9gen')
      if genres is not None and len(genres) > 0:
        metadata.genres.clear()
        for genre in genres:
          for sub_genre in parse_genres(genre):
            metadata.genres.add(sub_genre.strip())
    except Exception, e:
      Log('Exception reading \xa9gen (genre): ' + str(e))

    # Release Date
    try:
      release_date = tags.get('\xa9day')
      if release_date is not None and len(release_date) > 0:
        metadata.originally_available_at = Datetime.ParseDate(release_date[0].split('T')[0])
    except Exception, e:
      Log('Exception reading \xa9day (release date)' + str(e))

    # Posters
    valid_posters = []
    try:
      covers = tags.get('covr')
      if covers is not None and len(covers) > 0:
        for cover in covers:
          poster_name = hashlib.md5(cover).hexdigest()
          valid_posters.append(poster_name)
          if poster_name not in metadata.posters:
            Log('Adding embedded cover art: ' + poster_name)
            metadata.posters[poster_name] = Proxy.Media(cover)
    except Exception, e:
      Log('Exception adding posters: ' + str(e))

    return valid_posters

#####################################################################################################################

class FLACAudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, tagType):
    return tagType in ['FLAC']

  def process_metadata(self, metadata):

    Log('Reading FLAC tags from: ' + self.filename)
    try: 
      tags = MFile(self.filename)
      Log('Found tags: ' + str(tags.keys()))
    except:
      Log('An error occurred while attempting to parse the FLAC file: ' + self.filename)
      return

    # Genres
    try:
      genres = tags.get('genre')
      if genres is not None and len(genres) > 0:
        metadata.genres.clear()
        for genre in genres:
          for sub_genre in parse_genres(genre):
            metadata.genres.add(sub_genre.strip())
    except Exception, e:
      Log('Exception reading genre: ' + str(e))

    # Release Date
    try:
      release_date = tags.get('date')
      if release_date is not None and len(release_date) > 0:
        metadata.originally_available_at = Datetime.ParseDate(release_date[0])
    except Exception, e:
      Log('Exception reading release date' + str(e))

    # Posters
    valid_posters = []
    try:
      covers = tags.pictures
      if covers is not None and len(covers) > 0:
        for cover in covers:
          poster_name = hashlib.md5(cover.data).hexdigest()
          valid_posters.append(poster_name)
          if poster_name not in metadata.posters:
            Log('Adding embedded cover art: ' + poster_name)
            metadata.posters[poster_name] = Proxy.Media(cover.data)
    except Exception, e:
      Log('Exception adding posters: ' + str(e))

    return valid_posters

#####################################################################################################################

class OGGAudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, tagType):
    return tagType in ['OggVorbis']

  def process_metadata(self, metadata):

    Log('Reading OGG tags from: ' + self.filename)
    try: 
      tags = MFile(self.filename)
      Log('Found tags: ' + str(tags.keys()))
    except:
      Log('An error occured while attempting to parse the OGG file: ' + self.filename)
      return

    # Genres
    try:
      genres = tags.get('genre')
      if genres is not None and len(genres) > 0:
        metadata.genres.clear()
        for genre in genres:
          for sub_genre in parse_genres(genre):
            metadata.genres.add(sub_genre.strip())
    except Exception, e:
      Log('Exception reading genre: ' + str(e))

    # Release Date
    try:
      release_date = tags.get('date')
      if release_date is not None and len(release_date) > 0:
        metadata.originally_available_at = Datetime.ParseDate(release_date[0])
    except Exception, e:
      Log('Exception reading release date' + str(e))

    # Posters
    valid_posters = []
    try:
      covers = tags.get('metadata_block_picture')
      if covers is not None and len(covers) > 0:
        for cover in covers:
          poster = Picture(base64.standard_b64decode(cover))
          poster_name = hashlib.md5(poster.data).hexdigest()
          valid_posters.append(poster_name)
          if poster_name not in metadata.posters:
            Log('Adding embedded cover art: ' + poster_name)
            metadata.posters[poster_name] = Proxy.Media(poster.data)
    except Exception, e:
      Log('Exception adding posters: ' + str(e))

    return valid_posters