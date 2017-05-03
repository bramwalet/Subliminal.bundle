# coding=utf-8

import logging
import sys

from babelfish import Language

logger = logging.getLogger(__name__)

from subzero.modification import SubMod

fn = sys.argv[1]
debug = "--debug" in sys.argv

if debug:
    logging.basicConfig(level=logging.DEBUG)

submod = SubMod(debug=debug)
submod.load(fn, language=Language.fromietf("en"))
submod.modify("remove_HI", "OCR_fixes")
#submod.modify("OCR_fixes")

#print submod.f.to_string("srt")
