# coding=utf-8

import os
import logging
from subliminal.video import SUBTITLE_EXTENSIONS, Language

logger = logging.getLogger(__name__)

# may be absolute or relative paths; set to selected options
CUSTOM_PATHS = []

def _search_external_subtitles(path):
    dirpath, filename = os.path.split(path)
    dirpath = dirpath or '.'
    fileroot, fileext = os.path.splitext(filename)
    subtitles = {}
    for p in os.listdir(dirpath):
        # keep only valid subtitle filenames
        if not p.startswith(fileroot) or not p.endswith(SUBTITLE_EXTENSIONS):
            continue

        # extract the potential language code
        language_code = p[len(fileroot):-len(os.path.splitext(p)[1])].replace(fileext, '').replace('_', '-')[1:]

        # default language is undefined
        language = Language('und')

        # attempt to parse
        if language_code:
            try:
                language = Language.fromietf(language_code)
            except ValueError:
                logger.error('Cannot parse language code %r', language_code)

        subtitles[p] = language

    logger.debug('Found subtitles %r', subtitles)

    return subtitles    

def patched_search_external_subtitles(path):
    """
    wrap original search_external_subtitles function to search multiple paths for one given video
    # todo: cleanup and merge with _search_external_subtitles
    """
    video_path, video_filename = os.path.split(path)
    subtitles = {}
    for folder_or_subfolder in [video_path] + CUSTOM_PATHS:
	# folder_or_subfolder may be a relative path or an absolute one
	try:
	    abspath = unicode(os.path.abspath(os.path.join(*[video_path if not os.path.isabs(folder_or_subfolder) else "", folder_or_subfolder, video_filename])))
	except Exception, e:
	    logger.error("skipping path %s because of %s", repr(folder_or_subfolder), e)
	    continue
	logger.debug("external subs: scanning path %s", abspath)

	if os.path.isdir(os.path.dirname(abspath)):
	    subtitles.update(_search_external_subtitles(abspath))
    logger.debug("external subs: found %s", subtitles)
    return subtitles

