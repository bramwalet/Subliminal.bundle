# coding=utf-8

from subzero.modification import SubMod

submod = SubMod()
submod.load("test.srt")
submod.modify("remove_HI")

print submod.f.to_string("srt")
