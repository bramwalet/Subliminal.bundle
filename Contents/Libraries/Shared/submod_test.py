# coding=utf-8

from subzero.modification import SubMod, HearingImpaired

submod = SubMod("test.srt")
submod.modify(HearingImpaired)

print submod.f.to_string("srt")
