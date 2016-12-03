#!/usr/bin/python
"""Simple generator of SCC files.

Reads a format with 608 command mnemonics and UTF-8 text and generate SCC files from them.

The format typically has the ending .ccs and has the following structure.

# Here is a timestamp in .scc format
00:00:00:00

# Here are commands associated
> RCL ENM EDM PAC_1_white
# The PAC command has two attributes (line# and color/italics) and an optional third attribute u for underline
# Text is in UTF-8 format and associated with the latest timestamp
Here is a first line
> EOC
# Everything above will be associated with 00:00:00:00. Next comes a new time

00:00:00:10
This is sample text
> EOC ENM

> PAC_1_white BKG_blue_semi

BBS
> TO3 BKG_transparent  BLK_u
Black underlined text on transparent bkg
"""

# The copyright in this software is being made available under the BSD License,
# included below. This software may be subject to other third party and contributor
# rights, including patent rights, and no such rights are granted under this license.
#
# Copyright (c) 2016, Dash Industry Forum.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation and/or
#  other materials provided with the distribution.
#  * Neither the name of Dash Industry Forum nor the names of its
#  contributors may be used to endorse or promote products derived from this software
#  without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY
#  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
#  INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#  NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

from cea608 import odd_parity_check, byte_to_utf8

utf8_to_byte = dict([(unicode(v, "utf-8"), k) for k,v in byte_to_utf8.items()])
pac_row_codes = [(0x11, 0x40), (0x11, 0x60), (0x12, 0x40), (0x12, 0x60),
                 (0x15, 0x40), (0x15, 0x60), (0x16, 0x40), (0x16, 0x60),
                 (0x17, 0x40), (0x17, 0x60), (0x10, 0x40), (0x13, 0x40),
                 (0x13, 0x60), (0x14, 0x40), (0x14, 0x60)]
colors = ("white", "green", "blue", "cyan", "red", "yellow", "magenta", "italics")
background_colors = ('white', 'green', 'blue', 'cyan', 'red', 'yellow', 'magenta', 'black', 'transparent')
class SCCGenError(Exception):
    "Error in SCCGen."

class Assembler(object):

    def __init__(self, infile_handler, outfile_handler, verbose_level=0):
        self.ifh = infile_handler
        self.ofh = outfile_handler
        self.verbose_level = verbose_level
        self.time = None
        self.ofh.write("Scenarist_SCC V1.0")
        self.buffer_code = None # Code of a non-outputted char

    def parse(self):
        for line in self.ifh:
            self.parse_line(line)
        self.handle_dangling_char()

    def parse_line(self, line):
        line = line.rstrip()
        if len(line) == 0: # Empty line
            return
        if line[0] == "#": # Comment
            return
        time_parts = line.split(":")
        if len(time_parts) == 4:
            self.handle_dangling_char()
            self.time = line
            self.ofh.write("\n\n%s" % self.time)
        elif line.startswith(">"): # Commands
            line = line[1:].strip()
            parts = line.split()
            for p in parts:
                self.interpret_cmd(p)
        else: #unicode text
            self.interpret_text(line)

    def interpret_cmd(self, part):
        "Interpret an individual command, and produce double output codes."
        code = None
        if part == "RCL":
            code = (0x14, 0x20)
        elif part == "BS":
            code = (0x14, 0x21)
        elif part == "DER":
            code = (0x14, 0x24)
        elif part == "RU2":
            code = (0x14, 0x25)
        elif part == "RU3":
            code = (0x14, 0x26)
        elif part == "RU4":
            code = (0x14, 0x27)
        elif part == "FON":
            code = (0x14, 0x28)
        elif part == "RDC":
            code = (0x14, 0x29)
        elif part == "EDM":
            code = (0x14, 0x2c)
        elif part == "CR":
            code = (0x14, 0x2d)
        elif part == "ENM":
            code = (0x14, 0x2e)
        elif part == "EOC":
            code = (0x14, 0x2f)
        elif part == "TO1":
            code = (0x17, 0x21)
        elif part == "TO2":
            code = (0x17, 0x22)
        elif part == "TO3":
            code = (0x17, 0x23)
        elif part.startswith("PAC"):
            parts = part.split("_")
            line_nr = int(parts[1])
            pac_code = pac_row_codes[line_nr-1]
            color = None
            underline = None
            if len(parts) > 2:
                color = parts[2]
                if color == "indent":
                    # Pattern is PAC_indent_amount or PAC_indent_amount_u
                    indent_amount = int(parts[3])
                    if not indent_amount % 4 == 0 or indent_amount > 20:
                        raise SCCGenError("Strange indent amount %d" % indent_amount)
                    underline = (len(parts) > 4  and parts[4] == "u") and 1 or 0
                    byte2_offset = 0x10 + indent_amount/2 + underline
                    code = (pac_code[0], pac_code[1] + byte2_offset)
                    if self.verbose_level > 0:
                        print "PAC_code for row=%d indent=%d underline=%d (%02x, %02x)" % (line_nr, indent_amount, underline, code[0], code[1])
                else:
                    # Pattern is PAC_color or PAC_color_u
                    try:
                        color_code = 2*colors.index(color)
                    except ValueError:
                        raise SCCGenError("Cannot decode PAC color %s" % color)
                    underline = len(parts) > 3 and parts[3] == "u" and 1 or 0
                    byte2_offset = color_code + underline
                    code = (pac_code[0], pac_code[1] + byte2_offset)
                    if self.verbose_level > 0:
                        print "PAC_code for row=%d color=%s underline=%d (%02x, %02x)" % (line_nr, color, underline, code[0], code[1])
        elif part.startswith("MID"):
            # Pattern is MID_color or MID_color_u
            parts = part.split("_")
            color = parts[1]
            try:
                color_code = 2*colors.index(color) + 0x20
            except ValueError:
                raise SCCGenError("Cannot decode midrow color %s" % color)
            underline = len(parts) > 2 and 1 or 0
            code = (0x11, color_code + underline)
            if self.verbose_level > 0:
                print "MIDROW color=%s underline=%d (%02x, %02x)" % (color, underline, code[0], code[1])
        elif part.startswith("BKG"):
            parts = part.split("_")
            color = parts[1]
            if color == "transparent":
                code = (0x17, 0x2d)
                self.print_uchar("&") # One should insert space according to standard, but we put & for debug
            else:
                try:
                    color_code = 2*background_colors.index(color) + 0x20
                except ValueError:
                    raise SCCGenError("Cannot decode background color %s" % color)
                if len(parts) == 3 and parts[2] == "semi":
                    color_code += 1
                self.print_uchar("&") # One should insert space according to standard, but we put & for debug
                code = (0x10, color_code)
        elif part.startswith("BLK"):
            parts = part.split("_")
            black_code = 0x2e
            if len(parts) == 2 and parts[1] == "u":
                black_code += 1
            self.print_uchar("$") # One should insert space according to standard, but we put $ for debug
            code = (0x17, black_code)
        if code is None:
            raise SCCGenError("Cannot interpret command %s" % part)
        self.print_pair(code)
        #self.print_pair(code) # This repeat was important for analog transmission. Not needed any longer
        return code != None

    def insert_BS(self):
        self.print_pair((14, 21))
        #self.print_pair((14, 21)) # This repeat was important for analog transmission. Not needed any longer

    def interpret_text(self, line):
        utf8text = unicode(line, "utf-8")
        for c in utf8text:
            self.print_uchar(c)

    def print_uchar(self, c):
        "Print a unicode character. Preceed BS if needed."
        if utf8_to_byte.has_key(c):
            byte = utf8_to_byte[c]
            if byte < 0x80:
                code = byte
                self.print_code(code)
            elif byte < 0x90:
                code = byte - 0x50
                self.print_pair((0x11, code))
            elif byte < 0xb0:
                code = byte - 0x70
                # All symbols include automatic BS, so we must insert extra char
                self.print_code(0x23) # We insert a hash # which is not always optimal
                self.print_pair((0x12, code))
            else:
                code = byte - 0x90
                # All symbols include automatic BS, so we must insert extra char
                self.print_code(0x23) # We insert a hash # which is not always optimal
                self.print_pair((0x13, code))
        else:
            code = ord(c.encode("ascii"))
            self.print_code(code)

    def print_code(self, code):
        if self.buffer_code is not None:
            old_code = self.buffer_code
            self.buffer_code = None
            self.print_pair((old_code, code))
        else:
            self.buffer_code = code

    def handle_dangling_char(self):
        if self.buffer_code is not None:
            dangling_pair = (self.buffer_code, 0)
            self.buffer_code = None
            self.print_pair(dangling_pair)

    def fix_parity(self, byte):
        if not odd_parity_check(byte):
            byte = byte ^ 0x80
        return byte

    def print_pair(self, pair):
        self.handle_dangling_char()
        self.ofh.write(" ")
        for p in pair:
            byte = self.fix_parity(p)
            self.ofh.write("%02x" % byte)

    def close(self):
        self.handle_dangling_char()
        self.ofh.write("\n")


def cmd_line():
    import os, sys
    from optparse import OptionParser

    parser = OptionParser(usage="%prog [options] file.ccs", description="Create .scc file from .css input file")
    parser.add_option('-v', '--verbosity', help='verbosity level [default: %default]', type='int', action='store', default=0, dest='verbosity_level')
    (opts, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)
    filename = args[0]
    ifh = open(filename, "r")
    outfilename = os.path.splitext(filename)[0] + ".scc"
    ofh = open(outfilename, "wb")
    a = Assembler(ifh, ofh, opts.verbosity_level)
    a.parse()
    a.close()


if __name__ == "__main__":
    cmd_line()
