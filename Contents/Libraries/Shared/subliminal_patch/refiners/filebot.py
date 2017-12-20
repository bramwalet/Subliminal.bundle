# coding=utf-8
import subprocess
import sys
import traceback
import logging
import re
import binascii
import types
import os

from pipes import quote
from guessit import guessit
from subliminal import Episode
from subliminal_patch.core import REMOVE_CRAP_FROM_FILENAME
from subzero.lib.which import find_executable

if sys.platform == "win32":
    from pyads import ADS

logger = logging.getLogger(__name__)


def quote_args(seq):
    return ' '.join(quote(arg) for arg in seq)


def win32_xattr(fn):
    handler = ADS(fn)
    return handler.get_stream_content("net.filebot.filename")


def default_xattr(fn):
    if not default_xattr_bin:
        raise Exception("Neither getfattr, attr nor filebot were found")

    if "getfattr" in default_xattr_bin:
        return ["getfattr", "-n", "user.net.filebot.filename", fn]

    elif "attr" in default_xattr_bin:
        return ["attr", "-g", "net.filebot.filename", fn]

    return ["filebot", "-script", "fn:xattr", fn]


XATTR_MAP = {
    "default": (
        default_xattr,
        lambda result: re.search('(?um)(net\.filebot\.filename(?=="|: )[=:" ]+|Attribute.+:\s)([^"\n\r\0]+)',
                                 result).group(2)
    ),
    "darwin": {
        lambda fn: ["xattr", "-p", "net.filebot.filename", fn],
        lambda result: binascii.unhexlify(result.replace(' ', '').replace('\n', '')).strip("\x00")
    },
    "win32": {
        lambda fn: fn,
        win32_xattr,
    }
}

if sys.platform not in XATTR_MAP:
    default_xattr_bin = find_executable("getfattr") or find_executable("attr") or find_executable("filebot")


def refine(video, **kwargs):
    """

    :param video:
    :param kwargs:
    :return:
    """

    if sys.platform in XATTR_MAP:
        logger.debug("Using native xattr calls for %s", sys.platform)
    else:
        logger.debug("Using %s for %s", default_xattr_bin, sys.platform)

    args_func, match_func = XATTR_MAP.get(sys.platform, XATTR_MAP["default"])

    args = args_func(video.name)
    if isinstance(args, types.ListType):
        try:
            output = subprocess.check_output(quote_args(args), stderr=subprocess.PIPE, shell=True)
        except subprocess.CalledProcessError, e:
            if e.returncode == 1:
                logger.info(u"%s: Couldn't get filebot original filename", video.name)
            else:
                logger.error(u"%s: Unexpected error while getting filebot original filename: %s", video.name,
                              traceback.format_exc())
            return
    else:
        output = args

    try:
        orig_fn = match_func(output)
    except:
        logger.info(u"%s: Couldn't get filebot original filename" % video.name)
    else:
        guess_from = REMOVE_CRAP_FROM_FILENAME.sub(r"\2", orig_fn)

        logger.debug(u"Got original filename: %s", guess_from)

        # guess
        hints = {
            "single_value": True,
            "type": "episode" if isinstance(video, Episode) else "movie",
        }

        guess = guessit(guess_from, options=hints)

        for attr in ("release_group", "format",):
            if attr in guess:
                value = guess.get(attr)
                logger.debug(u"%s: Filling attribute %s: %s", video.name, attr, value)
                setattr(video, attr, value)

        video.original_name = os.path.basename(guess_from)
