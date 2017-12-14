# coding=utf-8

import gzip

from gzip import read32


__all__ = ["GeezipFile", "open"]


def open(filename, mode="rb", compresslevel=9):
    """Shorthand for GzipFile(filename, mode, compresslevel).

    The filename argument is required; mode defaults to 'rb'
    and compresslevel defaults to 9.

    """
    return GeezipFile(filename, mode, compresslevel)


class GeezipFile(gzip.GzipFile):
    def _read_eof(self):
        # We've read to the end of the file, so we have to rewind in order
        # to reread the 8 bytes containing the CRC and the file size.
        # We check the that the computed CRC and size of the
        # uncompressed data matches the stored values.  Note that the size
        # stored is the true file size mod 2**32.
        self.fileobj.seek(-8, 1)
        crc32 = read32(self.fileobj)
        isize = read32(self.fileobj)  # may exceed 2GB
        # if crc32 != self.crc:
        #     raise IOError("CRC check failed %s != %s" % (hex(crc32),
        #                                                  hex(self.crc)))
        # elif isize != (self.size & 0xffffffffL):
        if isize != (self.size & 0xffffffffL):
            raise IOError, "Incorrect length of data produced"

        # Gzip files can be padded with zeroes and still have archives.
        # Consume all zero bytes and set the file position to the first
        # non-zero byte. See http://www.gzip.org/#faq8
        c = "\x00"
        while c == "\x00":
            c = self.fileobj.read(1)
        if c:
            self.fileobj.seek(-1, 1)
