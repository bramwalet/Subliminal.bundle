# coding=utf-8

import gzip
from zlib import Z_FINISH


__all__ = ["GeezipFile", "open", "Z_FINISH"]


def open(filename, mode="rb", compresslevel=9):
    """Shorthand for GzipFile(filename, mode, compresslevel).

    The filename argument is required; mode defaults to 'rb'
    and compresslevel defaults to 9.

    """
    return GeezipFile(filename, mode, compresslevel)


class GeezipFile(gzip.GzipFile):
    pass
