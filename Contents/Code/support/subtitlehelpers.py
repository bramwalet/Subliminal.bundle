# coding=utf-8

import re, unicodedata, os
import config
import helpers


class SubtitleHelper(object):
    def __init__(self, filename):
        self.filename = filename


def SubtitleHelpers(filename):
    filename = helpers.unicodize(filename)
    for cls in [VobSubSubtitleHelper, DefaultSubtitleHelper]:
        if cls.is_helper_for(filename):
            return cls(filename)
    return None


#####################################################################################################################

class VobSubSubtitleHelper(SubtitleHelper):
    @classmethod
    def is_helper_for(cls, filename):
        (file, file_extension) = os.path.splitext(filename)

        # We only support idx (and maybe sub)
        if not file_extension.lower() in ['.idx', '.sub']:
            return False

        # If we've been given a sub, we only support it if there exists a matching idx file
        return os.path.exists(file + '.idx')

    def process_subtitles(self, part):

        lang_sub_map = {}

        # We don't directly process the sub file, only the idx. Therefore if we are passed on of these files, we simply
        # ignore it.
        (file, ext) = os.path.splitext(self.filename)
        if ext == '.sub':
            return lang_sub_map

        # If we have an idx file, we need to confirm there is an identically names sub file before we can proceed.
        sub_filename = file + ".sub"
        if not os.path.exists(sub_filename):
            return lang_sub_map

        Log('Attempting to parse VobSub file: ' + self.filename)
        idx = Core.storage.load(os.path.join(self.filename))
        if idx.count('VobSub index file') == 0:
            Log('The idx file does not appear to be a VobSub, skipping...')
            return lang_sub_map

        languages = {}
        language_index = 0
        basename = os.path.basename(self.filename)
        for language in re.findall('\nid: ([A-Za-z]{2})', idx):

            if not languages.has_key(language):
                languages[language] = []

            Log('Found .idx subtitle file: ' + self.filename + ' language: ' + language + ' stream index: ' + str(language_index))
            languages[language].append(Proxy.LocalFile(self.filename, index=str(language_index), format="vobsub"))
            language_index += 1

            if not lang_sub_map.has_key(language):
                lang_sub_map[language] = []
            lang_sub_map[language].append(basename)

        for language, subs in languages.items():
            part.subtitles[language][basename] = subs

        return lang_sub_map


#####################################################################################################################

class DefaultSubtitleHelper(SubtitleHelper):
    @classmethod
    def is_helper_for(cls, filename):
        (file, file_extension) = os.path.splitext(filename)
        return file_extension.lower()[1:] in config.SUBTITLE_EXTS

    def process_subtitles(self, part):

        lang_sub_map = {}

        basename = os.path.basename(self.filename)
        (file, ext) = os.path.splitext(self.filename)

        # Remove the initial '.' from the extension
        ext = ext[1:]

        # Attempt to extract the language from the filename (e.g. Avatar (2009).eng)
        language = ""

        # IETF support thanks to https://github.com/hpsbranco/LocalMedia.bundle/commit/4fad9aefedece78a1fa96401304351347f644369
        language_match = re.match(".+\.([^\.]+)$" if not Prefs["subtitles.language.ietf"] else ".+\.([^-.]+)(?:-[A-Za-z]+)?$", file)
        if language_match and len(language_match.groups()) == 1:
            language = language_match.groups()[0]
        language = Locale.Language.Match(language)

        codec = None
        format = None
        if ext in ['txt', 'sub']:
            try:

                file_contents = Core.storage.load(self.filename)
                lines = [line.strip() for line in file_contents.splitlines(True)]
                if re.match('^\{[0-9]+\}\{[0-9]*\}', lines[1]):
                    format = 'microdvd'
                elif re.match('^[0-9]{1,2}:[0-9]{2}:[0-9]{2}[:=,]', lines[1]):
                    format = 'txt'
                elif '[SUBTITLE]' in lines[1]:
                    format = 'subviewer'
                else:
                    Log("The subtitle file does not have a known format, skipping... : " + self.filename)
                    return lang_sub_map
            except:
                Log("An error occurred while attempting to parse the subtitle file, skipping... : " + self.filename)
                return lang_sub_map

        if codec is None and ext in ['ass', 'ssa', 'smi', 'srt', 'psb']:
            codec = ext.replace('ass', 'ssa')

        if format is None:
            format = codec

        Log('Found subtitle file: ' + self.filename + ' language: ' + language + ' codec: ' + str(codec) + ' format: ' + str(format))
        part.subtitles[language][basename] = Proxy.LocalFile(self.filename, codec=codec, format=format)

        lang_sub_map[language] = [basename]
        return lang_sub_map


def getSubtitlesFromMetadata(part):
    subs = {}
    for language in part.subtitles:
        subs[language] = []
        for key, proxy in getattr(part.subtitles[language], "_proxies").iteritems():
            try:
                p_type, p_value, p_sort, p_index, p_codec, p_format = proxy
            except ValueError:
                Log.Error("Couldn't parse subtitle info, got proxy %s" % proxy)
                continue

            if p_type == "Media":
                # metadata subtitle
                subs[language].append(key)
    return subs
