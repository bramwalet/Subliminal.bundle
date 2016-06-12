# coding=utf-8
import os
import logging
from bs4 import UnicodeDammit
from subliminal.api import get_subtitle_path, io
from subzero.lib.io import get_viable_encoding

logger = logging.getLogger(__name__)


def save_subtitles(video, subtitles, single=False, directory=None, encoding=None, encode_with=None):
    """Save subtitles on filesystem.

    Subtitles are saved in the order of the list. If a subtitle with a language has already been saved, other subtitles
    with the same language are silently ignored.

    The extension used is `.lang.srt` by default or `.srt` is `single` is `True`, with `lang` being the IETF code for
    the :attr:`~subliminal.subtitle.Subtitle.language` of the subtitle.

    :param video: video of the subtitles.
    :type video: :class:`~subliminal.video.Video`
    :param subtitles: subtitles to save.
    :type subtitles: list of :class:`~subliminal.subtitle.Subtitle`
    :param bool single: save a single subtitle, default is to save one subtitle per language.
    :param str directory: path to directory where to save the subtitles, default is next to the video.
    :param str encoding: encoding in which to save the subtitles, default is to keep original encoding.
    :return: the saved subtitles
    :rtype: list of :class:`~subliminal.subtitle.Subtitle`

    patch: unicode path probems
    """
    saved_subtitles = []
    for subtitle in subtitles:
        # check content
        if subtitle.content is None:
            logger.error('Skipping subtitle %r: no content', subtitle)
            continue

        # check language
        if subtitle.language in set(s.language for s in saved_subtitles):
            logger.debug('Skipping subtitle %r: language already saved', subtitle)
            continue

        # create subtitle path
        subtitle_path = get_subtitle_path(video.name, None if single else subtitle.language)
        if directory is not None:
            subtitle_path = os.path.join(directory, os.path.split(subtitle_path)[1])

        # force unicode
        subtitle_path = UnicodeDammit(subtitle_path).unicode_markup

        subtitle.storage_path = subtitle_path

        # save content as is or in the specified encoding
        logger.info('Saving %r to %r', subtitle, subtitle_path)
        has_encoder = callable(encode_with)

        if has_encoder:
            logger.info('Using encoder %s' % encode_with.__name__)

        # save normalized subtitle if encoder or no encoding is given
        if has_encoder or encoding is None:
            content = encode_with(subtitle.text) if has_encoder else subtitle.content
            with io.open(subtitle_path, 'wb') as f:
                f.write(content)

            if single:
                break
            continue

        # save subtitle if encoding given
        if encoding is not None:
            with io.open(subtitle_path, 'w', encoding=encoding) as f:
                f.write(subtitle.text)

        saved_subtitles.append(subtitle)

        # check single
        if single:
            break

    return saved_subtitles
