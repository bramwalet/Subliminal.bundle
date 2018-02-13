# coding=utf-8

from libfilebot import get_filebot_attrs
from common import update_video


def refine(video, **kwargs):
    """

    :param video:
    :param kwargs:
    :return:
    """
    orig_fn = get_filebot_attrs(video.name)

    if orig_fn:
        update_video(video, orig_fn)
