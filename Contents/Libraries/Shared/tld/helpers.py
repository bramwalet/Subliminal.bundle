# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from os.path import abspath, join
from .conf import get_setting
__author__ = u'Artur Barseghyan'
__copyright__ = u'2013-2019 Artur Barseghyan'
__license__ = u'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = (u'project_dir', u'PROJECT_DIR')


def project_dir(base):
    u'Project dir.'
    tld_names_local_path_parent = get_setting(u'NAMES_LOCAL_PATH_PARENT')
    return abspath(join(tld_names_local_path_parent, base).replace(u'\\', u'/'))


PROJECT_DIR = project_dir
