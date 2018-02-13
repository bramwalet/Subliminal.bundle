import os
import sys

# thanks @ plex trakt scrobbler: https://github.com/trakt/Plex-Trakt-Scrobbler/blob/master/Trakttv.bundle/Contents/Libraries/Shared/plugin/core/io.py


class FileIO(object):
    @staticmethod
    def exists(path):
        return os.path.exists(path)

    @staticmethod
    def delete(path):
        os.remove(path)

    @staticmethod
    def read(path, mode='r'):
        with open(path, mode) as fp:
            data = fp.read()

        return data

    @staticmethod
    def write(path, data, mode='w'):
        with open(path, mode) as fp:
            fp.write(data)


VALID_ENCODINGS = ("latin1", "utf-8", "mbcs")


def get_viable_encoding():
    # fixme: bad
    encoding = sys.getfilesystemencoding()
    return "utf-8" if not encoding or encoding.lower() not in VALID_ENCODINGS else encoding

