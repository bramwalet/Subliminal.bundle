"""Filter that output TTML from CEA-608 data screens."""

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
import xml.etree.ElementTree as ET
import sys
import re
import json
import stpp_creator

NS = "http://www.w3.org/ns/ttml"
NS_TTP = "http://www.w3.org/ns/ttml#parameter"
NS_TTS = "http://www.w3.org/ns/ttml#styling"
NS_TTM = "http://www.w3.org/ns/ttml#metadata"
NS_EBUTTS = "urn:ebu:style"
NS_EBUTTM = "urn:ebu:metadata"
NS_SMPTE = "http://www.smpte-ra.org/schemas/2052-1/2013/smpte-tt"
NS_SMPTE_M608 = "http://www.smpte-ra.org/schemas/2052-1/2013/smpte-tt#cea608"

def ns_tag(tag):
    return str(ET.QName(NS, tag))

def ttp_tag(tag):
    return str(ET.QName(NS_TTP, tag))

def tts_tag(tag):
    return str(ET.QName(NS_TTS, tag))

def ttm_tag(tag):
    return str(ET.QName(NS_TTM, tag))

def ebutts_tag(tag):
    return str(ET.QName(NS_EBUTTS, tag))

def ebuttm_tag(tag):
    return str(ET.QName(NS_EBUTTM, tag))

def smpte_tag(tag):
    return str(ET.QName(NS_SMPTE, tag))

def smpte_m608_tag(tag):
    return str(ET.QName(NS_SMPTE_M608, tag))
    

class TTMLWriter(object):
    "Write TTML from data provided from cea608 parser."
    
    def __init__(self, fileName, channel=1, segmentDuration = 0, combineConsecutiveRows=True):
        self.fileName = fileName
        self.channel = channel
        self.combineConsecutiveRows = combineConsecutiveRows
        self.pTagId = 0
        self.fh = None
        self.lastscreen = None
        self.lasttime = None
        self.starttime = None
        self.currentStyle = "baseStyle"
        self.segNr = 1
        self.pid = 0
        self.segmentDuration = segmentDuration
        self.segmentStart = 0
        self.segmentEnd = self.segmentDuration
        self.writeSegmentsOut = True if self.segmentDuration > 0 else False
        self.padding = "X"
        self.styleStates = { }
        self.spaceMatch = re.compile('^[ ]*$')
        self.currentStyle = "baseStyle"
        self.tt_doc = None
        self.tt_head_metadata = None
        self.tt_head_metadata_smpte = None
        self.tt_head_styling = None
        self.tt_head_layout = None
        self.tt_body = None
        self.regions = []
        self.fonts = "Menlo, Consolas, Cutive Mono, monospace"
        #self.fonts = "Menlo, Consolas, monospace"
        self.baseAttribs = { 'xml:id':'style_cea608_white_black', tts_tag('fontStyle'):'normal', tts_tag('fontFamily'):self.fonts, tts_tag('fontSize'):'90%', tts_tag('lineHeight'):'normal',  tts_tag('color'):'#ffffff', tts_tag('backgroundColor'):'#000000' }

        self.seenRegions = { }
        self.rgbColorMap = {
            'white':'#FFFFFFFF',
            'white_semi':'#FFFFFF88',
            'green':'#00FF00FF',
            'green_semi':'#00FF0088',
            'blue':'#0000FFFF',
            'blue_semi':'#0000FF88',
            'cyan':'#00FFFFFF',
            'cyan_semi':'#00FFFF88',
            'red':'#FF0000FF',
            'red_semi':'#FF000088',
            'yellow':'#FFFF00FF',
            'yellow_semi':'#FFFF0088',
            'magenta':'#FF00FFFF',
            'magenta_semi':'#FF00FF88',
            'black':'#000000FF',
            'black_semi':'#00000088',
            'transparent':'#00000000',
        }


        ET.register_namespace("", NS)
        ET.register_namespace("ttp", NS_TTP)
        ET.register_namespace("tts", NS_TTS)
        ET.register_namespace("ttm", NS_TTM)
        ET.register_namespace("ebuttm", NS_EBUTTM)
        ET.register_namespace("ebutts", NS_EBUTTS)
        ET.register_namespace("smpte", NS_SMPTE)
        ET.register_namespace("m608", NS_SMPTE_M608)

    def updateData(self, t, screen):
        "Update screen data, and possibly trigger cue output."
        time = self.transformTime(t)
        if self.lastscreen is None:
            if screen is not None:
                self.initFile(time, screen)
            else:
                return
        if screen != self.lastscreen:
            startTime = self.transformTimeToMS(self.lasttime)
            endTime = self.transformTimeToMS(time)


            self.outputCue(time)

            if not self.lastscreen.isEmpty() and self.writeSegmentsOut:
                #print startTime,endTime
                if endTime > self.segmentEnd:
                    while self.segmentEnd < endTime:
                        self.write_output(self.segmentStart, self.segmentEnd)
                        self.segmentStart = self.segmentEnd
                        self.segmentEnd += self.segmentDuration

            self.lastscreen = screen.copy()
            self.lasttime = time
    
    def transformTime(self, time):
        "Transform from hh:mm:ss:fn or pts to hh:mm:ss:ms."
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

    def transformTimeFromMS(self, time):
        t = int(time)
        hh = t / 3600000
        t -= hh * 3600000
        mm = t / 60000
        t -= mm * 60000
        ss = t / 1000
        t -= ss * 1000
        ms = t
        newtime = "%02d:%02d:%02d.%03d" % (hh, mm, ss, ms)
        return newtime

    def transformTimeToMS(self, time):
        "Transform from hh:mm:ss.ms to sss.sss"
        newtime = 0
        timems = time.split(".")
        parts = timems[0].split(":")

        newtime += int(parts[0]) * 3600000
        newtime += int(parts[1]) * 60000
        newtime += int(parts[2]) * 1000
        newtime += int(timems[1])
        return newtime
    
    def initFile(self, time, screen):
        "Init output file and add headers at the top."
        if self.writeSegmentsOut:
            print "Writing init file: '" + self.fileName + "_segment_init.mp4" + "'"
            self.fh = open(self.fileName + "_segment_init.mp4", "wb")
            self.fh.write(stpp_creator.create_init_segment())
            self.fh.close();
        self.fh = None
        self.lastscreen = screen.copy()
        self.lasttime = time

        # Create XML
        self.tt_doc = ET.Element(ns_tag('tt'), attrib={'xml:lang':'swe', 'xml:space':'preserve', ttp_tag('timeBase'):'media', ttp_tag('cellResolution'):'32 15'})
        self.tt_head = ET.SubElement(self.tt_doc, ns_tag('head'))
        self.tt_head_metadata = ET.SubElement(self.tt_head, ns_tag('metadata'))
        self.tt_head_metadata_smpte = ET.SubElement(self.tt_head_metadata, smpte_tag('information'), attrib = { 'origin':NS_SMPTE_M608, smpte_m608_tag('channel'):'CC'+str(self.channel), 'mode':'Preserved' } )

        # Add default style to styleStates
        self.styleStates['style_cea608_white_black'] = self.baseAttribs.copy()

    def checkIndent(self, text):
        line = ''
        for c in text:
            line += c.uchar

        line = line.decode('utf-8')
        l = len(line)

        ll = len(line.lstrip())

        return l-ll
        
    def outputCue(self, endTime):
        "Write a cue if there is enough data. Consecutive rows are written in one cue if flag set."
        if self.lastscreen.isEmpty():
            return

        self.pid += 1

        #print "-----------:",self.transformTimeToMS(self.lasttime)," -----------------:",self.transformTimeToMS(endTime)," -------------"

        currP = { 'start':self.lasttime, 'end':endTime, 'spans': [] }

        lastRowHasText = False
        lastRowIndentL = -1 
        currRegion = None
        for rowNr, row in enumerate(self.lastscreen.rows):
            line = ''
            prevPenState = PenState()
            self.currentStyle = "style_cea608_white_black"
            if not row.isEmpty():
                if not currRegion:
                    ri = self.checkIndent(row.uchars)
                    currRegion = { 'x':ri, 'y1':rowNr, 'y2':(rowNr + 1), 'p':[] };

                thisRowIndent = self.checkIndent(row.uchars)
                #print "Row:",rowNr,"indent:",thisRowIndent
                if thisRowIndent != lastRowIndentL and lastRowHasText:
                    currRegion['p'].append(currP)
                    currP = { 'start':self.lasttime, 'end':endTime, 'spans': [] }
                    currRegion['y2'] = rowNr
                    currRegion['name'] = "region_" + str(currRegion['x']) + "_" + str(currRegion['y1']) + "_" + str(currRegion['y2'])
                    if currRegion['name'] not in self.seenRegions:
                        self.regions.append(currRegion)
                        self.seenRegions[currRegion['name']] = currRegion
                    else:
                        existingRegion = self.seenRegions[currRegion['name']]
                        existingRegion['p'].extend(currRegion['p']);

                    currRegion = { 'x':thisRowIndent, 'y1':rowNr, 'y2':(rowNr + 1), 'p':[] };

                for c in row.uchars:
                    currPenState = c.penState
                    if (currPenState.foreground != prevPenState.foreground or 
                        currPenState.background != prevPenState.background or
                        currPenState.underline != prevPenState.underline or 
                        currPenState.italics != prevPenState.italics):

                        if len(line) > 0:
                            #print "State change in middle of line"
                            currP['spans'].append({'name':self.currentStyle, 'line':line.decode('utf-8').lstrip().rstrip(), 'row':rowNr})
                            #print "CP:",self.currentStyle,"line:",line.decode('utf-8').lstrip().rstrip()
                            line = ''
                        else:
                            #print "State change at begining of line"
                            pass
                        
                        currPenStateString = "style_cea608_" + str(currPenState.foreground) + "_" + str(currPenState.background)
                        if currPenState.underline:
                            currPenStateString += "_underline"
                        if currPenState.italics:
                            currPenStateString += "_italics"

                        if currPenStateString not in self.styleStates:
                            #print "State: " + currPenStateString
                            self.styleStates[currPenStateString] = self.baseAttribs.copy()
                            self.styleStates[currPenStateString]['xml:id'] = currPenStateString
                            self.styleStates[currPenStateString][tts_tag('color')] = self.colorFix(currPenState.foreground)
                            self.styleStates[currPenStateString][tts_tag('backgroundColor')] = self.colorFix(currPenState.background)
                            if currPenState.underline:
                                self.styleStates[currPenStateString][tts_tag('text-decoration')] = 'underline'
                            if currPenState.italics:
                                self.styleStates[currPenStateString][tts_tag('fontStyle')] = 'italic'

                        prevPenState = currPenState.copy()

                        self.currentStyle = currPenStateString


                    line += c.uchar

                if len(line.lstrip()) > 0:
                    #print "CP2:",self.currentStyle,"line:",line.decode('utf-8').lstrip().rstrip()
                    currP['spans'].append({'name':self.currentStyle, 'line':line.decode('utf-8').lstrip().rstrip(), 'row':rowNr})


                lastRowIndentL = thisRowIndent
                lastRowHasText = True
            else:
                lastRowIndentL = -1
                lastRowHasText = False
                if currRegion:
                    currRegion['p'].append(currP)
                    currP = { 'start':self.lasttime, 'end':endTime, 'spans': [] }
                    currRegion['y2'] = rowNr 
                    currRegion['name'] = "region_" + str(currRegion['x']) + "_" + str(currRegion['y1']) + "_" + str(currRegion['y2'])
                    if currRegion['name'] not in self.seenRegions:
                        self.regions.append(currRegion)
                        self.seenRegions[currRegion['name']] = currRegion
                    else:
                        existingRegion = self.seenRegions[currRegion['name']]
                        existingRegion['p'].extend(currRegion['p']);

                    currRegion = None
                
        if currRegion:
            currRegion['p'].append(currP)
            currRegion['y2'] = rowNr + 1
            currRegion['name'] = "region_" + str(currRegion['x']) + "_" + str(currRegion['y1']) + "_" + str(currRegion['y2'])
            if currRegion['name'] not in self.seenRegions:
                self.regions.append(currRegion)
                self.seenRegions[currRegion['name']] = currRegion
            else:
                existingRegion = self.seenRegions[currRegion['name']]
                existingRegion['p'].extend(currRegion['p']);

            currRegion = None

    def colorFix(self, color):
        if color in self.rgbColorMap:
            return self.rgbColorMap[color]
        else:
            return color

    def limitLow(self, t, l):
        tInSec = self.transformTimeToMS(t)
        if tInSec < l:
            return self.transformTimeFromMS(l)
        return  self.transformTimeFromMS(tInSec)

    def limitHigh(self, t, l):
        tInSec = self.transformTimeToMS(t)
        if tInSec > l:
            return self.transformTimeFromMS(l)
        return  self.transformTimeFromMS(tInSec)

    def write_output(self, inputTime, outputTime):
        if self.tt_doc is not None:
            outputName = self.fileName
            if self.writeSegmentsOut:
                outputName = self.fileName + "_segment_" + str(self.segNr) + ".m4s"
            
            print "Writing output to: '" + outputName + "'"

            self.fh = open(outputName, "wb")

            colWidth = 3.125
            lineHeight = 6.66

            
            if self.tt_head_styling is not None:
                self.tt_head.remove(self.tt_head_styling);
            if self.tt_head_layout is not None:
                self.tt_head.remove(self.tt_head_layout);
            if self.tt_body is not None:
                self.tt_doc.remove(self.tt_body);

            self.tt_head_styling = ET.SubElement(self.tt_head, ns_tag('styling'))
            self.tt_head_layout = ET.SubElement(self.tt_head, ns_tag('layout'))

            #ET.SubElement(self.tt_head_styling, ns_tag('style'), attrib = { 'xml:id':'bodyStyle', tts_tag('fontStyle'):'normal', tts_tag('fontFamily'):self.fonts, tts_tag('fontSize'):'70%', tts_tag('lineHeight'):'normal', tts_tag('color'):'#ffffff', tts_tag('textAlign'):'left' })
            ET.SubElement(self.tt_head_styling, ns_tag('style'), attrib = { 'xml:id':'bodyStyle', tts_tag('fontStyle'):'normal', tts_tag('fontFamily'):self.fonts, tts_tag('fontSize'):'90%', tts_tag('lineHeight'):'normal', tts_tag('color'):'#ffffff', tts_tag('textAlign'):'left' })

            #self.baseAttribs = { 'xml:id':'style_cea608_white_black', tts_tag('fontStyle'):'normal', tts_tag('fontFamily'):self.fonts, tts_tag('fontSize'):'70%', tts_tag('lineHeight'):'normal',  tts_tag('color'):'#ffffff', tts_tag('backgroundColor'):'#000000' }

            self.tt_body = ET.SubElement(self.tt_doc, ns_tag('body'), attrib = { 'style':'bodyStyle'})

            usedStyleState = { }

            if len(self.styleStates) and len(self.regions):
                for i in self.styleStates:
                    ss = self.styleStates[i]
                    element = ET.SubElement(self.tt_head_styling, ns_tag('style'), attrib = ss)

                    usedStyleState[ss['xml:id']] = { 'element':element, 'used':False }

                #self.styleStates = {}

                for r in self.regions:
                    region = None
                    regionDiv = None

                    if len(r['p']):
                        region = ET.SubElement(self.tt_head_layout, ns_tag('region'), attrib = 
                                    { 
                                        ns_tag('xml:id'):r['name'],
                                        tts_tag('overflow'):'visible',
                                        tts_tag('origin'):str(r['x'] * colWidth) + '% ' + str(r['y1'] * lineHeight) + '%',
                                        tts_tag('extent'):str(100.0 - (r['x'] * colWidth)) + '% ' + str((r['y2'] - r['y1']) * lineHeight) + '%'
                                    })

                        regionDiv = ET.SubElement(self.tt_body, ns_tag('div'), attrib = { 'region':r['name'] })

                        psToRemove = []

                        isRegionUsed = False

                        for p in r['p']:
                            #print p
                            if self.transformTimeToMS(p['end']) <= outputTime:
                                psToRemove.append(p)
                            if self.transformTimeToMS(p['start']) <= outputTime:
                                isRegionUsed = True
                                pTag = ET.SubElement(regionDiv, ns_tag('p'), attrib = { ns_tag('xml:id'):"p"+str(self.pTagId), ns_tag('begin'):self.limitLow(p['start'], inputTime), ns_tag('end'):self.limitHigh(p['end'],outputTime) })
                                self.pTagId += 1

                                lastSpanRow = 0
                                numSpans = len(p['spans'])
                                for i in range(0, numSpans):
                                    s = p['spans'][i]
                                    if i != 0 and lastSpanRow != s['row']:
                                        ET.SubElement(pTag, ns_tag('br'))
                                    if len(s['line']) > 0:
                                        lastSpanRow = s['row']
                                        usedStyleState[s['name']]['used'] = True
                                        ET.SubElement(pTag, ns_tag('span'), attrib = { ns_tag('style'):s['name'] }).text = s['line']
                                        #if i != (numSpans - 1):
                                        #    ET.SubElement(pTag, ns_tag('br'))

                        if not isRegionUsed:
                            if regionDiv is not None:
                                self.tt_body.remove(regionDiv)
                                regionDiv = None
                            if region is not None:
                                self.tt_head_layout.remove(region)
                                region = None

                        for p in psToRemove:
                            r['p'].remove(p)


                if len(self.tt_head_layout) == 0:
                    region = ET.SubElement(self.tt_head_layout, ns_tag('region'), attrib = 
                                    { 
                                        ns_tag('xml:id'):'region_empty',
                                        tts_tag('origin'):'0% 0%',
                                        tts_tag('extent'):'100% 100%'
                                    })
                    
                            
                #self.regions = []

                #print usedStyleState

                for s in usedStyleState:
                    style = usedStyleState[s]
                    if not style['used']:
                        self.tt_head_styling.remove(style['element'])

            else:
                "There are no styles or regions, create an empty tt tag"
                #self.tt_doc.remove(self.tt_head);
                #self.tt_doc.remove(self.tt_body);
                #del self.tt_doc.attrib[ttp_tag('cellResolution')]
                #del self.tt_doc.attrib[ttp_tag('timeBase')]
                #del self.tt_doc.attrib['xml:space']
                #del self.tt_doc.attrib['xml:lang']


            xmlstr = ET.tostring(self.tt_doc, encoding="utf8", method="xml")
            outputData = xmlstr
            if self.writeSegmentsOut:
                outputData = stpp_creator.create_media_segment(stpp_creator.TRACK_ID, self.segNr, self.segmentDuration, inputTime, xmlstr)
                self.segNr += 1

            self.fh.write(outputData)
            self.fh.close()
            self.fh = None
    
    def close(self):
        if not self.writeSegmentsOut:
            self.segmentStart = 0
            self.segmentEnd = 1000000
        self.write_output(self.segmentStart, self.segmentEnd)
        self.fh = None
