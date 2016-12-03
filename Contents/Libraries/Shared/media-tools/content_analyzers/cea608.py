"""Parser of CEA-608 Closed Captioning.

Can generate WebVTT output according to http://www.w3.org/community/texttracks/wiki/608_to_WebVTT.
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

NR_ROWS = 15
NR_COLS = 32

#Tables to look up row from PAC data
rows_low_ch1 = {0x11 : 1, 0x12 : 3, 0x15 : 5, 0x16 : 7, 0x17 : 9, 0x10 : 11, 0x13 : 12, 0x14 : 14}
rows_high_ch1 = {0x11 : 2, 0x12 : 4, 0x15 : 6, 0x16 : 8, 0x17 : 10, 0x13 : 13, 0x14 : 15}
rows_low_ch2 = {0x19 : 1, 0x1A : 3, 0x1D : 5, 0x1E : 7, 0x1F : 9, 0x18 : 11, 0x1B : 12, 0x1C : 14}
rows_high_ch2 = {0x19 : 2, 0x1A : 4, 0x1D : 6, 0x1E : 8, 0x1F : 10, 0x1B : 13, 0x1C : 15}

# Background color list (from table 3) (in addition they may be color_semi for semitransparent)
background_colors = ('white', 'green', 'blue', 'cyan', 'red', 'yellow', 'magenta', 'black', 'transparent')

class Logger(object):
    "Simple logger class to be able to write with time-stamps and filter_top_boxes on level."

    verbose_filter = {'DATA' : 3, 'DEBUG' : 3, 'INFO' : 2, 'WARNING' : 2, 'TEXT' : 1, 'ERROR' : 0}

    def __init__(self, verbose_level=0):
        self.time = ""
        self.verbose_level = verbose_level

    def set_time(self, time):
        self.time = time

    def set_verbose_level(self, verbose_level):
        self.verbose_level = verbose_level

    def log(self, severity, msg):
        try:
            minimal_level = self.verbose_filter[severity]
        except KeyError:
            print "WARNING: Severity %s not defined" % severity
        else:
            if self.verbose_level >= minimal_level:
                print "%s [%s] %s" % (self.time, severity, msg)


# Here comes the global logger instance
logger = Logger()
#logger = Logger(verbose_level=3)

byte_to_utf8 = {
    # Regular line-21 character set, mostly ASCII except these exceptions
    0x2a : "\xc3\xa1", # lowercase a, acute accent
    0x5c : "\xc3\xa9", # lowercase e, acute accent
    0x5e : "\xc3\xad", # lowercase i, acute accent
    0x5f : "\xc3\xb3", # lowercase o, acute accent
    0x60 : "\xc3\xba", # lowercase u, acute accent
    0x7b : "\xc3\xa7", # lowercase c with cedilla
    0x7c : "\xc3\xb7", # division symbol
    0x7d : "\xc3\x91", # uppercase N tilde
    0x7e : "\xc3\xb1", # lowercase n tilde
    0x7f : "\xe2\x96\x88", # Full block
    # THIS BLOCK INCLUDES THE 16 EXTENDED (TWO-BYTE) LINE 21 CHARACTERS
    # THAT COME FROM HI BYTE=0x11 AND LOW BETWEEN 0x30 AND 0x3F
    # THIS MEANS THAT \x50 MUST BE ADDED TO THE VALUES
    0x80 : "\xc2\xae", # Registered symbol (R)
    0x81 : "\xc2\xb0", # degree sign
    0x82 : "\xc2\xbd", # 1/2 symbol
    0x83 : "\xc2\xbf", # Inverted (open) question mark
    0x84 : "\xe2\x84\xa2", # Trademark symbol (TM)
    0x85 : "\xc2\xa2", # Cents symbol
    0x86 : "\xc2\xa3", # Pounds sterling
    0x87 : "\xe2\x99\xaa", # Music note
    0x88 : "\xc3\xa0", # lowercase a, grave accent
    0x89 : "\x20", # transparent space, we make it regular
    0x8a : "\xc3\xa8", # lowercase e, grave accent
    0x8b : "\xc3\xa2", # lowercase a, circumflex accent
    0x8c : "\xc3\xaa", # lowercase e, circumflex accent
    0x8d : "\xc3\xae", # lowercase i, circumflex accent
    0x8e : "\xc3\xb4", # lowercase o, circumflex accent
    0x8f : "\xc3\xbb", # lowercase u, circumflex accent
    # THIS BLOCK INCLUDES THE 32 EXTENDED (TWO-BYTE) LINE 21 CHARACTERS
    # THAT COME FROM HI BYTE=0x12 AND LOW BETWEEN 0x20 AND 0x3F
    0x90 : "\xc3\x81", # capital letter A with acute
    0x91 : "\xc3\x89", # capital letter E with acute
    0x92 : "\xc3\x93", # capital letter O with acute
    0x93 : "\xc3\x9a", # capital letter U with acute
    0x94 : "\xc3\x9c", # capital letter U with diaresis
    0x95 : "\xc3\xbc", # lowercase letter U with diaeresis
    0x96 : "\xe2\x80\x98", # opening single quote
    0x97 : "\xc2\xa1", # inverted exclamation mark
    0x98 : "\x2a", # asterisk
    0x99 : "\xe2\x80\x99", # closing single quote
    0x9a : "\xe2\x94\x81", # box drawings heavy horizontal
    0x9b : "\xc2\xa9", # copyright sign
    0x9c : "\xe2\x84\xa0", # Service mark
    0x9d : "\xe2\x80\xa2", # (round) bullet
    0x9e : "\xe2\x80\x9c", # Left double quotation mark
    0x9f : "\xe2\x80\x9d", # Right double quotation mark
    0xa0 : "\xc3\x80", # uppercase A, grave accent
    0xa1 : "\xc3\x82", # uppercase A, circumflex
    0xa2 : "\xc3\x87", # uppercase C with cedilla
    0xa3 : "\xc3\x88", # uppercase E, grave accent
    0xa4 : "\xc3\x8a", # uppercase E, circumflex
    0xa5 : "\xc3\x8b", # capital letter E with diaresis
    0xa6 : "\xc3\xab", # lowercase letter e with diaresis
    0xa7 : "\xc3\x8e", # uppercase I, circumflex
    0xa8 : "\xc3\x8f", # uppercase I, with diaresis
    0xa9 : "\xc3\xaf", # lowercase i, with diaresis
    0xaa : "\xc3\x94", # uppercase O, circumflex
    0xab : "\xc3\x99", # uppercase U, grave accent
    0xac : "\xc3\xb9", # lowercase u, grave accent
    0xad : "\xc3\x9b", # uppercase U, circumflex
    0xae : "\xc2\xab", # left-pointing guillemet
    0xaf : "\xc2\xbb", # right-pointing guillemet
    # THIS BLOCK INCLUDES THE 32 EXTENDED (TWO-BYTE) LINE 21 CHARACTERS
    # THAT COME FROM HI BYTE=0x13 AND LOW BETWEEN 0x20 AND 0x3F
    0xb0 : "\xc3\x83", # Uppercase A, tilde
    0xb1 : "\xc3\xa3", # Lowercase a, tilde
    0xb2 : "\xc3\x8d", # Uppercase I, acute accent
    0xb3 : "\xc3\x8c", # Uppercase I, grave accent
    0xb4 : "\xc3\xac", # Lowercase i, grave accent
    0xb5 : "\xc3\x92", # Uppercase O, grave accent
    0xb6 : "\xc3\xb2", # Lowercase o, grave accent
    0xb7 : "\xc3\x95", # Uppercase O, tilde
    0xb8 : "\xc3\xb5", # Lowercase o, tilde
    0xb9 : "\x7b", # Open curly brace
    0xba : "\x7d", # Closing curly brace
    0xbb : "\x5c", # Backslash
    0xbc : "\x5e", # Caret
    0xbd : "\x5f", # Underscore
    0xbe : "\x7c", # Pipe (vertical line)
    0xbf : "\xe2\x88\xbc", # Tilde operator
    0xc0 : "\xc3\x84", # Uppercase A, umlaut
    0xc1 : "\xc3\xa4", # Lowercase A, umlaut
    0xc2 : "\xc3\x96", # Uppercase O, umlaut
    0xc3 : "\xc3\xb6", # Lowercase o, umlaut
    0xc4 : "\xc3\x9f", # Esszett (sharp S)
    0xc5 : "\xc2\xa5", # Yen symbol
    0xc6 : "\xc2\xa4", # Generic currency symbol
    0xc7 : "\xe2\x94\x83", # Box drawings heavy vertical
    0xc8 : "\xc3\x85", # Uppercase A, ring
    0xc9 : "\xc3\xa5", # Lowercase A, ring
    0xca : "\xc3\x98", # Uppercase O, slash
    0xcb : "\xc3\xb8", # Lowercase o, slash
    0xcc : "\xe2\x94\x8f", # Box drawings heavy down and right
    0xcd : "\xe2\x94\x93", # Box drawings heavy down and left
    0xce : "\xe2\x94\x97", # Box drawings heavy up and right
    0xcf : "\xe2\x94\x9b", # Box drawings heavy up and left
}

def get_char_from_byte(byte):
    "Get character given byte."
    if byte_to_utf8.has_key(byte):
        char = byte_to_utf8[byte]
    else:
        char = chr(byte)
    return char


class PenState(object):
    "State of the pen"
    def __init__(self, foreground="white", underline=False, italics=False, background="black", flash=False):
        self.foreground = foreground
        self.background = background
        self.underline = underline
        self.italics = italics
        self.flash = flash

    def reset(self):
        self.foreground = "white"
        self.underline = False
        self.italics = False
        self.background = "black"
        self.flash = False

    def isDefault(self):
        return (self.foreground == "white" and (not self.underline) and (not self.italics) and
                self.background == "black" and (not self.flash))

    def __eq__(self, other):
        return ( (self.foreground == other.foreground) and
                 (self.underline == other.underline) and
                 (self.italics == other.italics) and
                 (self.background == other.background) and
                 (self.flash == other.flash) )

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        return PenState(self.foreground, self.underline, self.italics, self.background, self.flash)

    def __str__(self):
        return "color=%s, underline=%d, italics=%d, background=%s flash=%d" % \
            (self.foreground, self.underline, self.italics, self.background, self.flash)


class Utf8Char(object):
    "UTF-8 character with styling and background."

    def __init__(self, uchar=' ', foreground="white", underline=False, italics=False, background="black", flash="flash"):
        self.uchar = uchar # utf-8 character
        self.penState = PenState(foreground, underline,italics, background, flash)

    def reset(self):
        self.uchar = ' '
        self.penState.reset()

    def is_used(self):
        return self.uchar != ' '  or not self.penState.isDefault()

    def get_uchar(self):
        return self.uchar

    def set_char(self, char, penState):
        self.uchar = char
        self.set_penstate(penState)

    def set_penstate(self, penState):
        self.penState = penState.copy()

    def __eq__(self, other):
        return ( (self.uchar == other.uchar) and ( self.penState == other.penState) )

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        return Utf8Char(self.uchar, self.penState.foreground, self.penState.underline,
                        self.penState.italics, self.penState.background, self.penState.flash)

    def isEmpty(self):
        return not self.is_used()


class Row(object):
    "A CEA-608 row consisting of NR_COLS instances of Utf8Char."
    def __init__(self):
        self.uchars = [Utf8Char() for _ in range(NR_COLS)]
        self.pos = 0
        self.is_used = False
        self.currPenState = PenState()

    def __eq__(self, other):
        equal = True
        for uc1, uc2 in zip(self.uchars, other.uchars):
            if uc1 != uc2:
                equal = False
                break
        return equal

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        r = Row()
        for i in range(len(r.uchars)):
            r.uchars[i] = self.uchars[i].copy()
        return r

    def isEmpty(self):
        empty = True
        for u in self.uchars:
            if not u.isEmpty():
                empty = False
                break
        return empty

    def set_cursor(self, abs_pos):
        "Set the cursor to a valid column."
        if abs_pos != self.pos:
            self.pos = abs_pos
        if self.pos < 0:
            logger.log("ERROR", "Negative cursor position %d" % self.pos)
            self.pos = 0
        if self.pos > NR_COLS:
            logger.log("ERROR", "Too large cursor position %d" % self.pos)
            self.pos = NR_COLS

    def move_cursor(self, rel_pos):
        "Move the cursor relative to current position."
        new_pos = self.pos + rel_pos
        if rel_pos > 1:
            for pos in range(self.pos + 1, new_pos+1):
                self.uchars[pos].set_penstate(self.currPenState)
        self.set_cursor(new_pos)

    def back_space(self):
        "Backspace, move one step back and clear character."
        self.move_cursor(-1)
        self.uchars[self.pos].set_char(' ', self.currPenState)

    def insert_char(self, byte):
        if byte >= 0x90: # Extended char
            self.back_space()
        uchar = get_char_from_byte(byte)
        if self.pos >= NR_COLS:
            logger.log("ERROR", "Cannot insert %02x (%s) at position %d. Skipping it!" % (byte, uchar,self.pos))
            return
        self.uchars[self.pos].set_char(uchar, self.currPenState)
        self.move_cursor(1)
        self.is_used = True

    def clear_from_pos(self, start_pos):
        self.is_used = False
        for c in self.uchars[0:start_pos]:
            if c.is_used():
                self.is_used = True
                break
        for c in self.uchars[start_pos:NR_COLS]:
            c.reset()

    def clear(self):
        self.clear_from_pos(0)
        self.pos = 0
        self.currPenState = PenState()

    def clear_to_end_of_row(self):
        self.clear_from_pos(self.pos)

    def get_utf8_string(self):
        utf8str = ''.join(c.uchar for c in self.uchars)
        if utf8str == " "*32:
            utf8str = ""
        return utf8str

    def setPen(self, foreground=None, underline=None, italics=None, background=None, flash=None):
        if foreground is not None:
            self.currPenState.foreground = foreground
        if underline is not None:
            self.currPenState.underline = underline
        if italics is not None:
            self.currPenState.italics = italics
        if background is not None:
            self.currPenState.background = background
        if flash is not None:
            self.currPenState.flash = flash


class CaptionScreen(object):
    "Representation of the screen which has 15 rows of 32 characters"

    def __init__(self):
        self.rows = [Row() for _ in range(NR_ROWS)] # Note that we use zero-based numbering (0-14)
        self.curr_row = NR_ROWS - 1
        self.nr_roll_up_rows = None
        self.reset()

    def reset(self):
        for row in self.rows:
            row.clear()
        self.curr_row = NR_ROWS - 1

    def __eq__(self, other):
        equal = True
        for r1, r2 in zip(self.rows, other.rows):
            if r1 != r2:
                equal = False
                break
        return equal

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        c = CaptionScreen()
        for i in range(len(c.rows)):
            c.rows[i] = self.rows[i].copy()
        return c

    def isEmpty(self):
        empty = True
        for r in self.rows:
            if not r.isEmpty():
                empty = False
                break
        return empty

    def back_space(self):
        row = self.rows[self.curr_row]
        row.back_space()

    def clear_to_end_of_row(self):
        row = self.rows[self.curr_row]
        row.delete_to_end_of_row()

    def insert_char(self, char):
        "Insert a character in the current row."
        row = self.rows[self.curr_row]
        row.insert_char(char)

    def setPen(self, foreground=None, underline=None, italics=None, background=None, flash=None):
        row = self.rows[self.curr_row]
        row.setPen(foreground, underline, italics, background, flash)

    def move_cursor(self, rel_pos):
        row = self.rows[self.curr_row]
        row.move_cursor(rel_pos)

    def set_cursor(self, abs_pos):
        logger.log("INFO", "set_cursor: %d" % abs_pos)
        row = self.rows[self.curr_row]
        row.set_cursor(abs_pos)

    def set_pac(self, pac_data):
        logger.log("INFO", "pac_data = %s" % pac_data)
        new_row = pac_data['row'] - 1
        if self.nr_roll_up_rows:
            if new_row < self.nr_roll_up_rows-1:
                new_row = self.nr_roll_up_rows-1
        self.curr_row = new_row
        row = self.rows[self.curr_row]
        if pac_data['indent'] is not None:
            indent = pac_data['indent']
            prev_pos = max(indent-1, 0)
            row.set_cursor(pac_data['indent'])
            pac_data['color'] = row.uchars[prev_pos].penState.foreground
        self.setPen(pac_data['color'], pac_data['underline'], pac_data['italics'], "black", flash=False)

    def set_bkg_data(self, bkg_data):
        "Set background/extra foreground, but first do back_space, and then insert space (backwards compatibility)."
        logger.log("INFO", "bkg_data = %s" % bkg_data)
        self.back_space()
        self.setPen(**bkg_data)
        self.insert_char(0x20) # Space

    def set_roll_up_rows(self, nr_rows):
        "Set the number of roll-up rows."
        self.nr_roll_up_rows = nr_rows

    def roll_up(self):
        "Roll up the rolls."
        if self.nr_roll_up_rows is None:
            logger.log("DEBUG", "roll_up but nr_roll_up_rows not set yet")
            return # Not properly setup
        logger.log("TEXT", self.get_display_text())
        top_row_index = self.curr_row + 1 - self.nr_roll_up_rows
        top_row = self.rows.pop(top_row_index)
        top_row.clear()
        self.rows.insert(self.curr_row, top_row)
        logger.log("INFO", "Rolling up")
        #logger.log("TEXT", self.get_display_text())

    def get_display_text(self):
        "Get all non-empty rows as UTF-8 text."
        display_text = []
        text = ""
        for nr, row in enumerate(self.rows):
            row_text = row.get_utf8_string()
            if row_text:
                display_text.append('Row %d: "%s"' % (nr+1, row_text))
        if display_text:
            text = "[%s]" % ", ".join(display_text)
        return text

    def get_text_and_format(self):
        return self.rows



class Cea608Channel(object):
    "A CEA608 captioning channel (two in each field)"

    modes = ("MODE_ROLL-UP", "MODE_POP-ON", "MODE_PAINT-ON", "MODE_TEXT")

    def __init__(self, channel=1, outputFilter=None, verbose=1):
        self.channel = channel
        self.verbose = verbose
        self.outputFilter = outputFilter
        self.displayed_memory = CaptionScreen()
        self.nondisplayed_memory = CaptionScreen()
        self.curr_roll_up_row = self.displayed_memory.rows[NR_ROWS-1]
        self.write_screen = self.displayed_memory
        self.last_cmd = None
        self.mode = None

    def set_pac(self, pac_data):
        "Set Preamble Address Code."
        self.write_screen.set_pac(pac_data)

    def set_bkg_data(self, bkg_data):
        "Set background attributes (or black fg)."
        self.write_screen.set_bkg_data(bkg_data)

    def set_mode(self, new_mode):
        "Set the CC mode."
        if not new_mode in self.modes:
            raise KeyError, "Mode %s not supported!"
        logger.log("INFO", "MODE=%s" % new_mode)
        if new_mode == self.mode:
            return
        self.mode = new_mode
        if self.mode == "MODE_POP-ON":
            self.write_screen = self.nondisplayed_memory
        else:
            self.write_screen = self.displayed_memory
            self.write_screen.reset()
        if self.mode != "MODE_ROLL-UP":
            self.displayed_memory.nr_roll_up_rows = None
            self.nondisplayed_memory.nr_roll_up_rows = None

    def insert_chars(self, chars):
        "Insert characters in the screen."
        for c in chars:
            self.write_screen.insert_char(c)
        screen = self.write_screen == self.displayed_memory and "DISP" or "NON-DISP"
        logger.log("INFO", "%s: %s" % (screen, self.write_screen.get_display_text()))
        if self.mode in ("MODE_PAINT-ON", "MODE_ROLL-UP"):
            logger.log("TEXT", "DISPLAYED: %s" % self.displayed_memory.get_display_text())
            self.outputDataUpdate()

# Here are Control Code commands corresponding to table
    def cc_RCL(self):
        "Resume Caption Loading"
        logger.log("DEBUG", "> RCL")
        self.set_mode("MODE_POP-ON")

    def cc_BS(self):
        "Backspace"
        logger.log("DEBUG", "> BS")
        if self.mode == "MODE_TEXT":
            return
        self.write_screen.back_space()
        self.outputDataUpdate()

    def cc_AOF(self):
        "Reserved (formerly Alarm Off)"
        pass

    def cc_AON(self):
        "Reserved (formerly Alarm On)"
        pass

    def cc_DER(self):
        "Delete to End of Row"
        logger.log("DEBUG", "> DER")
        self.write_screen.clear_to_end_of_row()
        self.outputDataUpdate()

    def cc_RU(self, nr_rows):
        "Roll-Up Captions-2,3,or 4 Rows"
        assert(2 <= nr_rows <= 4)
        logger.log("INFO", "ROLL-UP %d" % nr_rows)
        self.write_screen = self.displayed_memory
        self.set_mode("MODE_ROLL-UP")
        self.write_screen.set_roll_up_rows(nr_rows)

    def cc_FON(self):
        "Flash On"
        self.write_screen.setPen(flash=True)

    def cc_RDC(self):
        "Resume Direct Captioning"
        logger.log("DEBUG", "> RDC")
        self.set_mode("MODE_PAINT-ON")

    def cc_TR(self):
        "Text Restart in text mode."
        self.set_mode("MODE_TEXT")
        # Text mode not supported

    def cc_RTD(self):
        "Resume Text Display in Text mode"
        self.set_mode("MODE_TEXT")
        # Text mode not supported

    def cc_EDM(self):
        "Erase Displayed Memory"
        logger.log("DEBUG", "> EDM")
        self.displayed_memory.reset()
        self.outputDataUpdate()

    def cc_CR(self):
        "Carriage Return"
        logger.log("DEBUG", "> CR")
        self.write_screen.roll_up()
        self.outputDataUpdate()

    def cc_ENM(self):
        "Erase Non-Displayed Memory"
        logger.log("DEBUG", "> ENM")
        self.nondisplayed_memory.reset()

    def cc_EOC(self):
        "End of Caption (Flip Memories)"
        logger.log("DEBUG", "> EOC")
        if self.mode == "MODE_POP-ON":
            tmp = self.displayed_memory
            self.displayed_memory = self.nondisplayed_memory
            self.nondisplayed_memory = tmp
            self.write_screen = self.nondisplayed_memory
            logger.log("TEXT", "DISPLAYED: %s" % self.displayed_memory.get_display_text())
            logger.log("INFO", "NON-DISPLAYED: %s" % self.nondisplayed_memory.get_display_text())
        else:
            logger.log("INFO", "DISPLAYED: %s" % self.displayed_memory.get_display_text())
        self.outputDataUpdate()


    def cc_TO(self, nr_cols):
        "Tab Offset 1,2, or 3 columns"
        assert(1 <= nr_cols <= 3)
        logger.log("DEBUG", "Tab Offset - TO%d" % nr_cols)
        self.write_screen.move_cursor(nr_cols)

    def cc_MIDROW(self, second_byte):
        "Parse MIDROW command."
        underline = second_byte % 2 == 1
        italics = second_byte >= 0x2e
        if not italics:
            color_index = second_byte/2 - 0x10
            colors = ["white", "green", "blue", "cyan", "red", "yellow", "magenta"]
            color = colors[color_index]
        else:
            color = "white"
        self.write_screen.setPen(color, underline, italics, flash=False)

    def outputDataUpdate(self):
        if self.outputFilter:
            self.outputFilter.updateData(logger.time, self.displayed_memory)



PARITY_CHECK_TABLE = (0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0)

def odd_parity_check(byte):
    "Return True if byte has odd parity."
    high_nible = byte >> 4
    low_nibble = byte & 0xf
    return PARITY_CHECK_TABLE[high_nible] != PARITY_CHECK_TABLE[low_nibble]



class Cea608FieldProcessor(object):
    """Parse and process an CEA-608 field provided byte pairs via add_data.

    The data is sorted according to time, to get the right order."""

    def __init__(self, field=1, outputFilter1=None, outputFilter2=None):
        self.field = field
        self.caption_channels = [Cea608Channel(1, outputFilter1), Cea608Channel(2, outputFilter2)]
        self.current_channel = None
        self.last_cmd = None
        self.buffered_data = [] # Entries are (time, (list of byte pairs))
        self.data_counters = {'padding' : 0, 'char' : 0, 'cmd' : 0, 'other' : 0}
        self.start_time = None
        self.last_time = None
        self.outputFilter1 = outputFilter1
        self.outputFilter2 = outputFilter2

    def close(self):
        "Close files"
        if self.outputFilter1:
            self.outputFilter1.close()

        if self.outputFilter2:
            self.outputFilter2.close()

    def get_cc_summary(self):
        "Get summary of what data has been parsed."
        total_count = 0
        for k in self.data_counters:
            total_count += self.data_counters[k]
        data = self.data_counters.copy()
        if self.start_time and self.last_time > self.start_time:
            duration = (self.last_time - self.start_time)/90000.0
            data['bitrate'] = int(total_count * 16 / duration)
        else:
            data['bitrate'] = 0
        if total_count > 0:
            return {'std': "CEA-608", 'field' : self.field, 'data' : data}
        else:
            return None

    def add_data(self, data, time_data):
        "Add data as pair of bytes. time_data needs to be sortable."
        if self.start_time is None:
            self.start_time = time_data
        self.last_time = time_data
        logger.set_time(time_data)
        if (not odd_parity_check(data[0])) or (not odd_parity_check(data[1])):
            #print "WARNING: Bad parity data: (%02x, %02x)" % data
            return
        cleaned_data = (data[0] & 0x7f, data[1] & 0x7f)
        if cleaned_data == (0,0):
            self.data_counters['padding'] += 2
            return
        else:
            logger.log("DATA", "(%02x, %02x) [%02x, %02x]" % (data[0], data[1], data[0]&0x7f, data[1]&0x7f))

        cmd_found = self.parse_cmd(cleaned_data)
        if not cmd_found:
            cmd_found = self.parse_midrow(cleaned_data)
        if not cmd_found:
            cmd_found = self.parse_pac(cleaned_data)
        if not cmd_found:
            cmd_found = self.parse_background_attributes(cleaned_data)
        if not cmd_found:
            chars_found = self.parse_char(cleaned_data)
            if chars_found:
                if self.current_channel is not None:
                    ch = self.caption_channels[self.current_channel-1]
                    ch.insert_chars(chars_found)
                else:
                    logger.log("WARNING", "No channel found yet. TEXT-MODE?")
        if cmd_found:
            self.data_counters['cmd'] += 2
        elif chars_found:
            self.data_counters['char'] += 2
        else:
            self.data_counters['other'] += 2
            logger.log("WARNING", "Couldn't parse cleaned data (%02x,%02x)" % cleaned_data)

    def parse_cmd(self, data):
        "Parse and act on a command."
        a,b = data

        if not ( (a in (0x14, 0x1C) and (0x20 <= b <= 0x2F)) or (a in (0x17, 0x1F) and (0x21 <= b <= 0x23)) ):
            return False

        if data == self.last_cmd:
            self.last_cmd = None
            logger.log("DEBUG", "Repeated cmd (%x,%x)" % data)
            return True # Repeated commands are dropped (once)

        channel = None
        if a in (0x14, 0x17):
            channel = 1
        elif a in (0x1C, 0x1f):
            channel = 2
        ch = self.caption_channels[channel-1]

        if a in (0x14, 0x1C):
            # Follow CEA-608 Table F.1.1.4
            if b == 0x20:
                ch.cc_RCL()
            elif b == 0x21:
                ch.cc_BS()
            elif b == 0x22:
                ch.cc_AOF()
            elif b == 0x23:
                ch.cc_AON()
            elif b == 0x24:
                ch.cc_DER()
            elif b == 0x25:
                ch.cc_RU(2)
            elif b == 0x26:
                ch.cc_RU(3)
            elif b == 0x27:
                ch.cc_RU(4)
            elif b == 0x28:
                ch.cc_FON()
            elif b == 0x29:
                ch.cc_RDC()
            elif b == 0x2A:
                ch.cc_TR()
            elif b == 0x2B:
                ch.cc_RTD()
            elif b == 0x2C:
                ch.cc_EDM()
            elif b == 0x2D:
                ch.cc_CR()
            elif b == 0x2E:
                ch.cc_ENM()
            elif b == 0x2F:
                ch.cc_EOC()
        else: # a in (0x17, 0x1F):
            ch.cc_TO(b - 0x20)
        self.last_cmd = data
        self.current_channel = channel
        return True

    def parse_midrow(self, data):
        "Parse midrow styling command"
        a, b = data
        if a in (0x11, 0x19)  and 0x20 <= b <= 0x2f:
            if a == 0x11:
                channel = 1
            else:
                channel = 2
            if channel != self.current_channel:
                raise Exception("Mismatch channel in midrow parsing")
            ch = self.caption_channels[channel-1]
            ch.cc_MIDROW(b)
            logger.log("DEBUG", "MIDROW %x %x" % data)
            return True
        return False

    def parse_pac(self, data):
        "Parse Preable Access Codes (Table 53)."
        a, b = data
        if not ( ((0x11 <= a <= 0x17 or 0x19 <= a <= 0x1F) and (0x40 <= b <= 0x7F)) or
                (a in (0x10, 0x18) and (0x40 <= b <= 0x5F))):
            return False

        if data == self.last_cmd:
            self.last_cmd = None
            return True  # Repeated commands are dropped (once)

        if a <= 0x17:
            channel = 1
        else:
            channel = 2

        if 0x40 <= b <= 0x5F:
            if channel == 1:
                row = rows_low_ch1[a]
            else:
                row = rows_low_ch2[a]
        else: # 0x60 <= b <= 0x7F
            if channel == 1:
                row = rows_high_ch1[a]
            else:
                row = rows_high_ch2[a]
        pac_data = self.interpret_pac(row, b)
        ch = self.caption_channels[channel-1]
        ch.set_pac(pac_data)
        self.last_cmd = data
        self.current_channel = channel
        return True

    def interpret_pac(self, row, byte):
        "Interpret the second byte of the pac, and return the information."
        pac_index = byte
        color = 'None'
        italics = False
        indent = None
        if byte > 0x5F:
            pac_index = byte - 0x60
        else:
            pac_index = byte - 0x40
        underline = (pac_index & 1) == 1
        if pac_index <= 0xd:
            color = ['white', 'green', 'blue', 'cyan', 'red', 'yellow', 'magenta', 'white'][pac_index/2]
        elif pac_index <= 0xf:
            italics = True
            color = 'white'
        else:
            indent = ((pac_index-0x10)/2)*4
        #Note that we have a zero-offset for the row
        return {'color' : color, 'underline' : underline, 'italics': italics, 'indent' : indent, 'row' : row}

    def parse_char(self, data):
        "Return an array with 1 to 2 bytes corresponding to chars, if found. None otherwise."
        a, b = data
        chars = None
        if a >= 0x19:
            channel = 2
            char_1 = a - 8
        else:
            channel = 1
            char_1 = a
        if 0x11 <= char_1 <= 0x13:
            # Special character
            c = b
            if char_1 == 0x11:
                c = b + 0x50
            elif char_1 == 0x12:
                c = b + 0x70
            else:
                c = b + 0x90
            logger.log("INFO", "Special char %s in channel %d" % (byte_to_utf8[c], channel))
            chars = (c,)
        elif 0x20 <= a <= 0x7f:
            if b == 0:
                chars = (a,)
            else:
                chars = (a, b)
        if chars:
            logger.log("DEBUG", "Chars = %s" % ",".join(["%02x" % c for c in chars]))
        return chars

    def parse_background_attributes(self, data):
        "Parse extended background attributes as well as new foreground color black."
        a, b = data
        if not ((a in (0x10, 0x18) and 0x20 <= b <= 0x2f) or ((a in (0x17, 0x1f) and 0x2d <= b <= 0x2f))):
            return False
        data = {}
        if a in (0x10, 0x18):
            index = (b-0x20)/2
            data['background'] = background_colors[index]
            if b % 2 == 1:
                data['background'] = "%s_semi" % data['background']
        elif b == 0x2d:
            data['background'] = "transparent"
        else:
            data['foreground'] = "black"
            if b == 0x2f:
                data['underline'] = True
        channel = (a < 0x18) and 1 or 2
        ch = self.caption_channels[channel-1]
        ch.set_bkg_data(data)
        return True

if __name__ == '__main__':
    cea608 = Cea608FieldProcessor()
    data1 = [
0x94, 0x20, 0x94, 0x54, 0x6d, 0x61, 0xec, 0xe5, 0x20, 0x61, 0x6e, 0x6e, 0xef, 0x75, 0x6e, 0xe3, 0xe5, 0xf2, 0xba, 0x80, 0x94, 0x70, 0x4f, 0xce, 0x20, 0x54, 0xc8, 0x49, 0xd3, 0x20, 0x45, 0xd0, 0x49, 0xd3, 0x4f, 0xc4, 0x45, 0x20, 0x4f, 0x46, 0x94, 0xf8, 0x97, 0xa2, 0x91, 0xae, 0xd0, 0xc1, 0x57, 0xce, 0x20, 0xd3, 0x54, 0xc1, 0x52, 0xd3, 0xae, 0xae, 0xae, 0x80, 0x94, 0x20]

    data2 = [0x94, 0x2f, 0x94, 0xae, 0x94, 0x20, 0x94, 0xd0, 0x97, 0xa2, 0xad, 0x20, 0xd3, 0x54, 0xd5, 0x52, 0xc7, 0x49, 0xd3, 0x20, 0x52, 0xc1, 0x4c, 0x4c, 0xd9, 0xa7, 0xd3, 0x20, 0x43, 0x4f, 0xcd, 0x49, 0xce, 0xc7, 0x20, 0xd5, 0xd0, 0xae, 0x94, 0xf4, 0x97, 0xa1, 0xad, 0x20, 0x57, 0x45, 0xa7, 0x52, 0x45, 0x20, 0xc7, 0x4f, 0x49, 0xce, 0xc7, 0xae
    ]

    data3 = [0x94, 0x20, 0x94, 0x2f, 0x94, 0xae, 0x94, 0x20, 0x94, 0x54, 0xad, 0x20, 0x49, 0x20, 0x57, 0xc1, 0xce, 0x54, 0x20, 0x54, 0x4f, 0x20, 0xc7, 0x4f, 0xae, 0x80, 0x94, 0x70, 0xad, 0x20, 0x49, 0x20, 0x54, 0xc8, 0x4f, 0xd5, 0xc7, 0xc8, 0x54, 0x20, 0xd9, 0x4f, 0xd5, 0x52, 0x20, 0xc2, 0x49, 0xcb, 0x45, 0x20, 0x57, 0xc1, 0xd3, 0x20, 0xc2, 0x52, 0x4f, 0xcb, 0x45, 0xae]

    # Harry Potter Movie 00:00:26:02
    data4 = [0x94, 0x20, 0x94, 0x2f, 0x94, 0xae, 0x94, 0x20, 0x94, 0x54, 0x97, 0xa1, 0xad, 0x20, 0x49, 0x20, 0x4c, 0x4f, 0x4f, 0xcb, 0x20, 0x4c, 0x49, 0xcb, 0x45, 0x80, 0x94, 0x70, 0x97, 0xa1, 0x49, 0xa7, 0xcd, 0x20, 0x49, 0xce, 0x20, 0x54, 0xc8, 0x45, 0x94, 0xf4, 0x97, 0x23, 0x91, 0xae, 0xc8, 0xc1, 0x52, 0x52, 0xd9, 0x20, 0xd0, 0x4f, 0x54, 0x54, 0x45, 0x52, 0x94, 0x7c, 0x91, 0x20] #, 0xcd, 0x4f, 0xd6, 0x49, 0x45, 0xae]

    # 00:00:28:01
    data5 = [0x94, 0x20, 0x94, 0x2f, 0x94, 0xae, 0x94, 0x20, 0x94, 0xf4, 0x97, 0xa2, 0xad, 0x20, 0x5b, 0x67, 0xe9, 0x67, 0x67, 0xec, 0xe9, 0x6e, 0x67, 0x5d]

    data = data4# data1 + data2
    for i in range(0, len(data) / 2):
        cea608.add_data(data[2*i:2*i+2], 0)

