# coding=utf-8

import logging

from rarfile import RarFile as _RarFile, UNRAR_TOOL, ORIG_OPEN_ARGS as OPEN_ARGS, custom_popen, check_returncode, \
    XTempFile

log = logging.getLogger(__name__)


class RarFile(_RarFile):
    def read(self, fname, psw=None):
        """
        read specific content of rarfile without parsing
        :param fname:
        :param psw:
        :return:
        """
        cmd = [UNRAR_TOOL] + list(OPEN_ARGS)

        with XTempFile(self._rarfile) as rf:
            log.debug(u"RAR CMD: %s", cmd + [rf, fname])
            p = custom_popen(cmd + [rf, fname])
            output = p.communicate()[0]
            check_returncode(p, output)

            return output
