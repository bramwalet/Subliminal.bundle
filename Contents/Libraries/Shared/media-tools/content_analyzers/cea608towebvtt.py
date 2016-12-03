"""Filter that output WebVTT from CEA-608 data screens."""

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

from cea608 import PenState


class WebVTTWriter(object):
    "Write WebVTT from data provided from cea608 parser."
    
    def __init__(self, fileName, channel=1, combineConsecutiveRows=True):
        self.fileName = fileName
        self.channel = channel
        self.combineConsecutiveRows = combineConsecutiveRows
        self.fh = None
        self.lastscreen = None
        self.lasttime = None
        self.starttime = None
    
    def updateData(self, t, screen):
        "Update screen data, and possibly trigger cue output."
        time = self.transformTime(t)
        if self.lastscreen is None:
            if screen is not None:
                self.initFile(time, screen)
            else:
                return
        if screen != self.lastscreen:
            self.outputCue(time)
            self.lastscreen = screen.copy()
            self.lasttime = time
    
    def transformTime(self, time):
        "Transform from hh:mm:ss:fn or pts to hh:mm:ss.ms."
        try:
            parts = time.split(":")
            frameNr = int(parts[-1])
            ms = min(int(frameNr*1000/29.97), 999)
            newtime = "%s.%03d" % (":".join(parts[:-1]), ms)
        except AttributeError: # pts time
            ss = time/90000
            ms = int((time % 90000)/90.0)
            hh = ss/3600
            mm = ss/60
            ss -= hh*3600 + mm*60
            newtime = "%02d:%02d:%02d.%03d" % (hh, mm, ss, ms)
        return newtime
    
    def initFile(self, time, screen):
        "Init output file and add headers at the top."
        self.fh = open(self.fileName, "wb")
        self.fh.write("WEBVTT\nStyling=CEA608\nKind=Caption\nChannel=CC%d\n" % self.channel)
        self.lastscreen = screen.copy()
        self.lasttime = time
        
    def outputCue(self, endTime):
        "Write a cue if there is enough data. Consecutive rows are written in one cue if flag set."
        if self.lastscreen.isEmpty():
            return
        lastRowNr = -2 # Make sure that there is a jump in rowNr compared to lastRowNr
        for rowNr, row in enumerate(self.lastscreen.rows):
            if not row.isEmpty():
                if not self.combineConsecutiveRows or (rowNr != lastRowNr + 1): 
                    self.fh.write("\n%s --> %s line:%d\n" % (self.lasttime, endTime, rowNr+1))
                self.outputTextRow(row)
                self.fh.write("\n")
                lastRowNr = rowNr
    
    def outputTextRow(self, row):
        "Output a row of cue text"
        prevState = PenState()
        for c in row.uchars:
            new_c_attrs = False
            currState = c.penState
            # First close open contexts
            if (currState.foreground != prevState.foreground or currState.background != prevState.background
                or currState.flash != prevState.flash):
                if prevState.foreground != "white" or prevState.background != "black" or prevState.flash:
                    self.fh.write("</c>")
                new_c_attrs = True
            if currState.underline != prevState.underline and prevState.underline:
                    self.fh.write("</u>")
            if currState.italics != prevState.italics and prevState.italics:
                    self.fh.write("</i>")
            # Now open new contexts
            if currState.italics != prevState.italics:
                if currState.italics:
                    self.fh.write("<i>")
                prevState.italics = currState.italics
            if currState.underline != prevState.underline:
                if currState.underline:
                    self.fh.write("<u>")
            if new_c_attrs:
                if currState.foreground != "white" or currState.background != "black" or currState.flash:
                    attr_string_parts = []
                    bkg = currState.background
                    if currState.background == "transparent":
                        attr_string_parts.append("transparent")
                    else:
                        parts = bkg.split("_")
                        if len(parts) == 2 and parts[1] == "semi":
                            attr_string_parts.append("semi-transparent")
                        if bkg != "black": # This is black opaque which is default
                            attr_string_parts.append("bg_%s" % parts[0]) # Add color
                    if currState.foreground != "white":
                        attr_string_parts.append(currState.foreground)
                    if currState.flash:
                        attr_string_parts.append("blink")
                    self.fh.write("<c.%s>" % ".".join(attr_string_parts))
            self.fh.write(c.uchar)
            prevState = currState.copy()
        # End of line
        if currState.foreground != "white" or currState.background != "black":
            self.fh.write("</c>")
        if currState.underline:
            self.fh.write("</u>")
        if currState.italics:
            self.fh.write("</i>")
        
    def close(self):
        "Close the file"
        if self.fh is not None:
            self.fh.close()
            self.fh = None
