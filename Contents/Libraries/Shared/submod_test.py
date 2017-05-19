# coding=utf-8

import logging
import sys
import codecs

from babelfish import Language

logger = logging.getLogger(__name__)

from subzero.modification import SubMod

fn = sys.argv[1]
debug = "--debug" in sys.argv

if debug:
    logging.basicConfig(level=logging.DEBUG)

submod = SubMod(debug=debug)
submod.load(fn, language=Language.fromietf("eng"), encoding="utf-8")
submod.modify("remove_HI", "OCR_fixes", "common", "OCR_fixes", "shift_offset(s=20)", "OCR_fixes", "color(color=#FF0000)", "shift_offset(s=-5, ms=-350)")

#srt = submod.to_unicode()
#print submod.f.to_string("srt", encoding="utf-8")
#print repr(srt)
#f = codecs.open("testout.srt", "w+", encoding="latin-1")
#f.write(srt)
#f.close()
#print submod.f.to_string("srt")
#submod.modify("OCR_fixes")
#submod.modify("change_FPS(from=24,to=25)")
#submod.modify("common")

#print submod.f.to_string("srt")
