# coding=utf-8

import os
import logging
from subliminal.video import SUBTITLE_EXTENSIONS, search_external_subtitles

logger = logging.getLogger(__name__)

# may be absolute or relative paths; set to selected options
CUSTOM_PATHS = []

def patched_search_external_subtitles(path):
    """
    WIP; fix isinstance(path, bytes) to skip; may already be so
    wrap original search_external_subtitles function to search multiple paths for one given video
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
	logger.debug("external subs: scanning path %s", folder_or_subfolder)
	subtitles.update(search_external_subtitles(abspath))
    logger.debug("external subs: found %s", subtitles)
    return subtitles
    