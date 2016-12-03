#!/usr/bin/env python

"""
MPEG2 Transport Stream parser
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

#pylint: disable=bad-whitespace
#pylint: disable=missing-docstring
#pylint: disable=line-too-long

import time
import struct
import socket
import select
import httplib
import binascii
import optparse
import urlparse
import datetime

class Logger(object):
    "Simple log class where output can be turned off."

    def __init__(self, silent=False):
        self.silent = silent

    def log(self, text):
        if not self.silent:
            print text

logger = Logger()
def log(text):
    logger.log(text)

try:
    import scc
except ImportError:
    log("Warning: Couldn't import scc. SCC extraction disabled.")
    scc = None

try:
    import cea708
except ImportError as e:
    print e
    log("Warning: Couldn't import cea708. Parsing disabled.")
    cea708 = None

FILTER = ''.join([(len(repr(chr(character))) == 3) and chr(character) or '.' for character in range(256)])
def dump_hex(src, length=8):
    result = []
    for i in xrange(0, len(src), length):
        s = src[i:i+length]
        hexa = ' '.join(["%02X"%ord(x) for x in s])
        printable = s.translate(FILTER)
        result.append("%04X   %-*s   %s\n" % (i, length*3, hexa, printable))
    return ''.join(result)

def dump_to_array(src, length=8):
    print 'data=[',
    l = 0
    for b in src:
        print '{0},'.format(hex(ord(b))),
        l += 1
        if l % length == 0:
            print '\n',
    print ']'

# TS format:    http://en.wikipedia.org/wiki/MPEG_transport_stream
# PAT/PMT:      http://en.wikipedia.org/wiki/Program_Specific_Information
# PES:          http://en.wikipedia.org/wiki/Packetized_elementary_stream
# Bitreader:    http://multimedia.cx/eggs/python-bit-classes

# PIDs
PAT_PID = 0x0000
CA_PID = 0x0001
SDT_PID = 0x0011
EIT_PID = 0x0012
#EIT_PID2 = 0x0012 # NOTE: set to 0x0080 to parse DT EIT
EIT_PID2 = 0x0080
STUFFING_PID = 0x1fff

# Stream Types
# See http://www.atsc.org/cms/standards/Code-Points-Registry-Rev-35.xlsx
STREAM_TYPE_MPEG1_VIDEO   = 0x01
STREAM_TYPE_MPEG2_VIDEO   = 0x02
STREAM_TYPE_MPEG1_AUDIO   = 0x03
STREAM_TYPE_MPEG2_AUDIO   = 0x04
STREAM_TYPE_PRIVATE       = 0x06
STREAM_TYPE_AUDIO_ADTS    = 0x0f
STREAM_TYPE_H264          = 0x1b
STREAM_TYPE_MPEG4_VIDEO   = 0x10
STREAM_TYPE_METADATA      = 0x15
STREAM_TYPE_AAC           = 0x11
STREAM_TYPE_MPEG2_VIDEO_2 = 0x80
STREAM_TYPE_AC3           = 0x81
STREAM_TYPE_PCM           = 0x83
STREAM_TYPE_SCTE35        = 0x86

# 0x06: // AC3 audio (ps)
# 0x81: // AC3 audio (ts)
# 0x83: // PCM audio

STREAM_TYPES = {
    STREAM_TYPE_MPEG1_VIDEO : 'MPEG1 video',
    STREAM_TYPE_MPEG2_VIDEO : 'MPEG2 video',
    STREAM_TYPE_MPEG2_VIDEO_2: 'MPEG2 video (2)',
    STREAM_TYPE_MPEG1_AUDIO : 'MPEG1 audio',
    STREAM_TYPE_MPEG2_AUDIO : 'MPEG2 audio',
    STREAM_TYPE_PRIVATE : 'Private stream',
    STREAM_TYPE_AUDIO_ADTS : 'Audio ADTS',
    STREAM_TYPE_H264 : 'H264 video',
    STREAM_TYPE_MPEG4_VIDEO : 'MPEG4 video',
    STREAM_TYPE_METADATA : 'Metadata',
    STREAM_TYPE_AAC : 'AAC',
    STREAM_TYPE_AC3 : 'AC3',
    STREAM_TYPE_PCM : 'PCM',
    STREAM_TYPE_SCTE35 : 'SCTE-35'
}

# Descriptors
VIDEO_STREAM_DESCRIPTOR = 0x02
AUDIO_STREAM_DESCRIPTOR = 0x03
DATA_STREAM_ALIGNMENT_DESCRIPTOR = 0x06
CA_DESCRIPTOR = 0x09
TELETEXT_SUBTITLE_DESCRIPTOR = 0x56
DVB_SUBTITLE_DESCRIPTOR = 0x59

invtab = [
    0x00, 0x80, 0x40, 0xc0, 0x20, 0xa0, 0x60, 0xe0,
    0x10, 0x90, 0x50, 0xd0, 0x30, 0xb0, 0x70, 0xf0,
    0x08, 0x88, 0x48, 0xc8, 0x28, 0xa8, 0x68, 0xe8,
    0x18, 0x98, 0x58, 0xd8, 0x38, 0xb8, 0x78, 0xf8,
    0x04, 0x84, 0x44, 0xc4, 0x24, 0xa4, 0x64, 0xe4,
    0x14, 0x94, 0x54, 0xd4, 0x34, 0xb4, 0x74, 0xf4,
    0x0c, 0x8c, 0x4c, 0xcc, 0x2c, 0xac, 0x6c, 0xec,
    0x1c, 0x9c, 0x5c, 0xdc, 0x3c, 0xbc, 0x7c, 0xfc,
    0x02, 0x82, 0x42, 0xc2, 0x22, 0xa2, 0x62, 0xe2,
    0x12, 0x92, 0x52, 0xd2, 0x32, 0xb2, 0x72, 0xf2,
    0x0a, 0x8a, 0x4a, 0xca, 0x2a, 0xaa, 0x6a, 0xea,
    0x1a, 0x9a, 0x5a, 0xda, 0x3a, 0xba, 0x7a, 0xfa,
    0x06, 0x86, 0x46, 0xc6, 0x26, 0xa6, 0x66, 0xe6,
    0x16, 0x96, 0x56, 0xd6, 0x36, 0xb6, 0x76, 0xf6,
    0x0e, 0x8e, 0x4e, 0xce, 0x2e, 0xae, 0x6e, 0xee,
    0x1e, 0x9e, 0x5e, 0xde, 0x3e, 0xbe, 0x7e, 0xfe,
    0x01, 0x81, 0x41, 0xc1, 0x21, 0xa1, 0x61, 0xe1,
    0x11, 0x91, 0x51, 0xd1, 0x31, 0xb1, 0x71, 0xf1,
    0x09, 0x89, 0x49, 0xc9, 0x29, 0xa9, 0x69, 0xe9,
    0x19, 0x99, 0x59, 0xd9, 0x39, 0xb9, 0x79, 0xf9,
    0x05, 0x85, 0x45, 0xc5, 0x25, 0xa5, 0x65, 0xe5,
    0x15, 0x95, 0x55, 0xd5, 0x35, 0xb5, 0x75, 0xf5,
    0x0d, 0x8d, 0x4d, 0xcd, 0x2d, 0xad, 0x6d, 0xed,
    0x1d, 0x9d, 0x5d, 0xdd, 0x3d, 0xbd, 0x7d, 0xfd,
    0x03, 0x83, 0x43, 0xc3, 0x23, 0xa3, 0x63, 0xe3,
    0x13, 0x93, 0x53, 0xd3, 0x33, 0xb3, 0x73, 0xf3,
    0x0b, 0x8b, 0x4b, 0xcb, 0x2b, 0xab, 0x6b, 0xeb,
    0x1b, 0x9b, 0x5b, 0xdb, 0x3b, 0xbb, 0x7b, 0xfb,
    0x07, 0x87, 0x47, 0xc7, 0x27, 0xa7, 0x67, 0xe7,
    0x17, 0x97, 0x57, 0xd7, 0x37, 0xb7, 0x77, 0xf7,
    0x0f, 0x8f, 0x4f, 0xcf, 0x2f, 0xaf, 0x6f, 0xef,
    0x1f, 0x9f, 0x5f, 0xdf, 0x3f, 0xbf, 0x7f, 0xff
]

def inv_char(char):
    return invtab[ord(char)]

def get_stream_type(stream_type):
    if stream_type in STREAM_TYPES.keys():
        return STREAM_TYPES.get(stream_type)
    return 'unknown'

def create_socket(port, host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    mreq = struct.pack("=4sl", socket.inet_aton(host), socket.INADDR_ANY)
    #sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return sock

class bitreader(object):
    def __init__(self, buffer):
        self.buffer = buffer
        self.bit_pos = 7
        self.byte = struct.unpack("B", self.buffer[0])[0]
        self.index = 1

    def get_bits(self, num_bits):
        num = 0
        mask = 1 <<self.bit_pos
        while num_bits:
            num_bits -= 1
            num <<= 1
            if self.byte & mask:
                num |= 1
            mask >>= 1
            self.bit_pos -= 1
            if self.bit_pos < 0:
                self.bit_pos = 7
                mask = 1 <<self.bit_pos
                if self.index < len(self.buffer):
                    self.byte = struct.unpack("B", self.buffer[self.index])[0]
                else:
                    self.byte = 0
                self.index += 1
        return num

    def step_bytes(self, bytes):
        data = self.buffer[self.index - 1: self.index - 1 + bytes]
        for i in range(bytes):
            self.get_bits(8)
        return data

    def trim(self):
        bits_to_trim = 7 - self.bit_pos
        self.get_bits(bits_to_trim)

    def tell(self):
        return self.index

    def seek(self, idx):
        self.index += idx

def ue(reader):
    leading_zero_bits = -1
    b = 0
    while not b:
        leading_zero_bits += 1
        b = reader.get_bits(1)
    return 2**leading_zero_bits - 1 + reader.get_bits(leading_zero_bits)

def print_bits(text, num, display, to_hex=False):
    if not display:
        return
    if to_hex:
        log('{0:40}: 0x{1:02x}'.format(text, num))
    else:
        log('{0:40}: {1}'.format(text, num))

def read_bits(reader, num_bits, text, display, to_hex=False):
    num = reader.get_bits(num_bits)
    print_bits(text, num, display, to_hex)
    return num

class frame(object):
    def __init__(self, data, sync, wall_clk, pts, dts, frame_type=''):
        self.data = data
        self.sync = sync
        self.wall_clk = wall_clk
        self.pts = pts
        self.dts = dts
        self.frame_type = frame_type

    def __str__(self):
        return 'frame_type={0} wall_clk={1:.4f} pts={2} ({3:.2f}) dts={4} ({5:.2f}) diff={6}'\
            .format(self.frame_type,
                    self.wall_clk,
                    self.pts,
                    self.pts / 90.0,
                    self.dts,
                    self.dts / 90.0,
                    self.pts - self.dts)

cc_map = {}

#
# TS packet parser
#
class ts_packet(object):
    def __init__(self, data, display=False, check_cc=False):
        self.reader = bitreader(data)
        self.data = data

        if display:
            log('')
            log('[TS PACKET]')

        self.sync_byte                      = read_bits(self.reader,  8, '  sync byte', display, to_hex = True)
        self.transport_error_indicator      = read_bits(self.reader,  1, '  transport error indicator', display)
        self.payload_unit_start_indicator   = read_bits(self.reader,  1, '  payload unit start indicator', display)
        self.transport_priority             = read_bits(self.reader,  1, '  transport priority', display)
        self.pid                            = read_bits(self.reader, 13, '  pid', display)
        self.scrambling_control             = read_bits(self.reader,  2, '  scrambling control', display)
        self.adaptation_field_exist         = read_bits(self.reader,  2, '  adaptation field exist', display)
        self.continuity_counter             = read_bits(self.reader,  4, '  continuity counter', display)

        global cc_map
        if not cc_map.has_key(self.pid):
            cc_map[self.pid] = -1

        if cc_map[self.pid] >= 0:
            cc_map[self.pid] = cc_map[self.pid] + 1
            if cc_map[self.pid] > 15:
                cc_map[self.pid] = 0

            if check_cc:
                if not self.continuity_counter == cc_map[self.pid]:
                    #print 'CC error:', self.continuity_counter, ' != ', cc_map[self.pid]
	                pass

        cc_map[self.pid] = self.continuity_counter

        if (self.adaptation_field_exist == 2) or (self.adaptation_field_exist == 3):
            tell_1 = self.reader.index
            self.adaptation_field_length            = read_bits(self.reader, 8, '   adaptation field length', display)
            if self.adaptation_field_length:
                self.discontinuity_indicator = read_bits(self.reader, 1, '   discontinuity indicator', display)
                self.random_access_indicator = read_bits(self.reader, 1, '   random access indicator', display)
                self.priority_indicator      = read_bits(self.reader, 1, '   priority indicator', display)
                self.pcr_flag                = read_bits(self.reader, 1, '   pcr flag', display)
                self.opcr_flag               = read_bits(self.reader, 1, '   opcr flag', display)
                self.splicing_point_flag       = read_bits(self.reader, 1, '   splicing point flag', display)
                self.transport_private_data_flag = read_bits(self.reader, 1, '   transport private data flag', display)
                self.adaptation_field_extension_flag = read_bits(self.reader, 1, '   adaptation field extension flag', display)
                if self.pcr_flag:
                    self.program_clock_reference_base       = read_bits(self.reader, 33, '   program clock reference base', display)
                    self.reserved_pcr                       = read_bits(self.reader,  6, '   reserved', display)
                    self.program_clock_reference_extension  = read_bits(self.reader,  9, '   program clock reference extension', display)
                    #log('PCR=', (self.program_clock_reference_base * 300 + self.program_clock_reference_extension) / 27000000.0)

                if self.opcr_flag:
                    self.original_program_clock_reference_base = read_bits(self.reader, 33, '   original program clock reference base', display)
                    self.reserved_opcr = read_bits(self.reader,  6, '   reserved', display)
                    self.original_program_clock_reference_extension = read_bits(self.reader,  9, '   original program clock reference extension', display)
                if self.splicing_point_flag:
                    self.splice_countdown = read_bits(self.reader, 8, '   splice countdown', display)
                if self.transport_private_data_flag:
                    self.transport_private_data_length = read_bits(self.reader, 8, '   transport private data length', display)
                    self.reader.step_bytes(self.transport_private_data_length)
                if self.adaptation_field_extension_flag:
                    #raise Exception('KALLE')
                    pass

            # calc stuffing
            tell_2 = self.reader.index
            self.num_stuffing = self.adaptation_field_length - (tell_2 - tell_1 - 1)
            self.reader.step_bytes(self.num_stuffing)

        self.payload = self.data[self.reader.index-1:188]
        self.header_len = 188 - len(self.payload)

    @property
    def has_adap(self):
        if (self.adaptation_field_exist == 2) or (self.adaptation_field_exist == 3):
            if self.adaptation_field_length > 0:
                return True
        return False

class pmt_info(object):
    def __init__(self, program_num, reserved, program_pid):
        self.program_num = program_num
        self.reserved = reserved
        self.program_pid = program_pid

#
# PAT parser
#
class pat(ts_packet):
    def __init__(self, data, display=False):
        ts_packet.__init__(self, data, display)

        if display:
            log('[PROGRAM ASSOCIATION TABLE]')

        self.pointer_field              = read_bits(self.reader, 8,  '  pointer field', display)
        if self.pointer_field:
            self.reader.step_bytes(self.pointer_field)

        self.table_id                   = read_bits(self.reader, 8,  '  table id', display)
        self.section_syntax_indicator   = read_bits(self.reader, 1,  '  section syntax indicator', display)
        self.marker                     = read_bits(self.reader, 1,  '  marker (0)', display)
        self.reserved_1                 = read_bits(self.reader, 2,  '  reserved', display)
        self.section_length             = read_bits(self.reader, 12, '  section length', display)
        self.transport_stream_id        = read_bits(self.reader, 16, '  transport stream id', display)
        self.reserved_2                 = read_bits(self.reader, 2,  '  reserved', display)
        self.version_number             = read_bits(self.reader, 5,  '  version number', display)
        self.current_next_indicator     = read_bits(self.reader, 1,  '  current next indicator', display)
        self.section_number             = read_bits(self.reader, 8,  '  section number', display)
        self.last_section_number        = read_bits(self.reader, 8,  '  last section number', display)

        self.pmt_info = []

        num_programs = (self.section_length - 5 - 4) / 4
        for i in range(num_programs):
            if display:
                log('  [PROGRAM]')
            program_num         = read_bits(self.reader, 16, '    program num', display)
            reserved            = read_bits(self.reader, 3,  '    reserved', display)
            program_map_pid     = read_bits(self.reader, 13, '    program map pid', display)
            #if program_num == 0:
                #log('    NOTE, this is the NETWOTK PID (NIT)')
            self.pmt_info.append(pmt_info(program_num, reserved, program_map_pid))
        self.crc32 = read_bits(self.reader, 32, '  crc32', display, to_hex = True)

class descriptor(object):
    def __init__(self, tag, data):
        self.tag = tag
        self.data = data

#
# PMT descriptor parser
#
def parse_descriptors(data, display=False):
    descriptors = []
    reader = bitreader(data)
    while reader.tell() < len(data):
        tag = reader.get_bits(8)
        length = reader.get_bits(8)
        d = reader.step_bytes(length)
        data_str = '0x' + ''.join(['%02x' % ord(c) for c in d])
        desc_reader = bitreader(d)

        if display:
            log('      [DESCRIPTOR] tag=0x{0:02x} length=0x{1:02x} data={2}'.format(tag, length, data_str))

        if tag == VIDEO_STREAM_DESCRIPTOR: #0x02
            if display:
                log('        type = video stream descriptor')
            read_bits(desc_reader,  1, '        multiple frame rate flag', display)
            read_bits(desc_reader,  4, '        frame rate code', display)
            f = read_bits(desc_reader,  1, '        MPEG 1 only flag', display)
            read_bits(desc_reader,  1, '        constrained parameter flag', display)
            read_bits(desc_reader,  1, '        still picture flag', display)
            if f == 0:
                read_bits(desc_reader,  8, '          profile and level indication', display)
                read_bits(desc_reader,  2, '          chroma format', display)
                read_bits(desc_reader,  1, '          frame rate extension flag', display)
                read_bits(desc_reader,  5, '          reserved', display)
        elif tag == AUDIO_STREAM_DESCRIPTOR: #0x03
            if display:
                log('        type = audio stream descriptor')
            read_bits(desc_reader,  1, '        free format flag', display)
            read_bits(desc_reader,  1, '        ID', display)
            f = read_bits(desc_reader,  2, '        layer', display)
            read_bits(desc_reader,  1, '        variable rate audio indicator', display)
            read_bits(desc_reader,  3, '        reserved', display)
        elif tag == DATA_STREAM_ALIGNMENT_DESCRIPTOR: #0x06
            if display:
                log('        type = data stream alignment descriptor')
            read_bits(desc_reader,  8, '        alignment type', display)
        elif tag == CA_DESCRIPTOR: #0x09
            log('        type = CA')
            read_bits(desc_reader,  16, '        CA system ID', display)
            read_bits(desc_reader,   3, '        reserved', display)
            read_bits(desc_reader,  13, '        CA PID', display)
        elif tag == 0x0a:
            if display:
                log('        type = ISO 639 LANGUAGE')
            language_1 = desc_reader.get_bits(8)
            language_2 = desc_reader.get_bits(8)
            language_3 = desc_reader.get_bits(8)
            if display:
                log('        language={0}{1}{2}'.format(chr(language_1), chr(language_2), chr(language_3)))
            read_bits(desc_reader,  8, '        audio type', display)
        elif tag == 0x52:
            if display:
                log('        type = stream identifier descriptor')
            read_bits(desc_reader,  8, '        component tag', display)
        elif tag == TELETEXT_SUBTITLE_DESCRIPTOR:
            # http://www.etsi.org/deliver/etsi_en/300400_300499/300468/01.03.01_60/en_300468v010301p.pdf
            if display:
                log('        type = teletext descriptor')
            while desc_reader.tell() < length:
                language_1 = desc_reader.get_bits(8)
                language_2 = desc_reader.get_bits(8)
                language_3 = desc_reader.get_bits(8)
                if display:
                    log('        language={0}{1}{2}'.format(chr(language_1), chr(language_2), chr(language_3)))
                read_bits(desc_reader,  5, '          teletext type', display)
                read_bits(desc_reader,  3, '          teletext magazine number', display)
                a = read_bits(desc_reader,  4, '          teletext page number 1', display=False)
                b = read_bits(desc_reader,  4, '          teletext page number 2', display=False)
                print_bits('          page number', 10 * a + b, display)
        elif tag == DVB_SUBTITLE_DESCRIPTOR:
            if display:
                log('        type = DVB SUBTITLE')
            language_1 = desc_reader.get_bits(8)
            language_2 = desc_reader.get_bits(8)
            language_3 = desc_reader.get_bits(8)
            if display:
                log('        language={0}{1}{2}'.format(chr(language_1), chr(language_2), chr(language_3)))
            subtitling_type = read_bits(desc_reader, 8, '        subtitling type', display)
            composition_page_id = read_bits(desc_reader, 16, '        composition page id', display)
            ancillary_page_id = read_bits(desc_reader, 16, '        ancillary page id', display)
        elif tag == 0x26:
            if display:
                log('        type = Metadata descriptor')
            maf = read_bits(desc_reader,  16, '        metadata application format', display)
            if maf == 0xffff:
                read_bits(desc_reader,  32, '        metadata application format identifier', display)
            metadata_format = read_bits(desc_reader,  8, '        metadata format', display)
            if metadata_format == 0xff:
                read_bits(desc_reader,  32, '        metadata format identifier', display)
            read_bits(desc_reader,  8, '        metadata service id', display)
            read_bits(desc_reader,  3, '        decoder config flags', display)
            read_bits(desc_reader,  1, '        DSM-CC flag', display)
            read_bits(desc_reader,  4, '        reserved', display)
        elif tag == 0x40:
            if display:
                log('        type = network type descriptor')

        elif tag == 0x41:
            if display:
                log('        type = service list descriptor')
            i = 0
            while i < len(d):
                read_bits(desc_reader,  16, '        service id', display)
                read_bits(desc_reader,  8, '        service type', display)
                i += 3

        elif tag == 0x4d:
            if display:
                log('        type = short event descriptor')
                log('        {0}'.format(d[5:]))
        elif tag == 0x4e:
            if display:
                log('        type = extended event descriptor')
                log('        {0}'.format(d[5:]))
        elif tag == 0x55:
            if display:
                log('        type = parental rating descriptor')
            i = 0
            while i < len(d):
                language_1 = desc_reader.get_bits(8)
                language_2 = desc_reader.get_bits(8)
                language_3 = desc_reader.get_bits(8)
                if display:
                    log('        language                        : {0}{1}{2}'.format(chr(language_1), chr(language_2), chr(language_3)))

                #read_bits(desc_reader,  24, '        country code', display)
                read_bits(desc_reader,  8, '        rating', display)
                i += 4
        elif tag == 0x68:
            if display:
                log('        type = DSNG descriptor')
        elif tag == 0x73:
            if display:
                log('        type = default authority descriptor')
                log('        {0}'.format(d[5:]))
        elif tag == 0x74:
            if display:
                log('        type = related content descriptor')
        elif tag == 0x8a:
            if display: # See http://www.atsc.org/cms/standards/Code-Points-Registry-Rev-35.xlsx
                log('        type = SCTE-35 Cue descriptor')

        descriptors.append(descriptor(tag, data[reader.tell() : reader.tell() + length]))

    if reader.tell() != 1 + len(data):
        log('Length error when parsing descriptors! has read {0} bytes of {1} available'.format(reader.tell(), len(data)))

    return descriptors

class pmt_stream(object):
    def __init__(self,
                 stream_type,
                 reserved_a,
                 elementary_pid,
                 reserved_b,
                 es_info_length,
                 es_description,
                 descriptors):
        self.stream_type = stream_type
        self.reserved_a = reserved_a
        self.elementary_pid = elementary_pid
        self.reserved_b = reserved_b
        self.es_info_length = es_info_length
        self.es_description = es_description
        self.descriptors = descriptors

#
# PMT parser
#
class pmt(ts_packet):
    def __init__(self, data, display=False):
        ts_packet.__init__(self, data, display)

        if display:
            log('[PROGRAM MAP TABLE]')

        self.pointer_field              = read_bits(self.reader, 8,  '  pointer field', display)
        if self.pointer_field:
            self.reader.step_bytes(self.pointer_field)

        self.table_id                   = read_bits(self.reader, 8,  '  table id', display)
        self.section_syntax_indicator   = read_bits(self.reader, 1,  '  section syntax indicator', display)
        self.marker                     = read_bits(self.reader, 1,  '  marker', display)
        self.reserved_1                 = read_bits(self.reader, 2,  '  reserved', display)
        self.section_length             = read_bits(self.reader, 12, '  section length', display)
        self.program_num                = read_bits(self.reader, 16, '  program num', display)
        self.reserved_2                 = read_bits(self.reader, 2,  '  reserved', display)
        self.version_number             = read_bits(self.reader, 5,  '  version', display)
        self.current_next_indicator     = read_bits(self.reader, 1,  '  current next indicator', display)
        self.section_number             = read_bits(self.reader, 8,  '  section number', display)
        self.last_section_number        = read_bits(self.reader, 8,  '  last section number', display)
        self.reserved_3                 = read_bits(self.reader, 3,  '  reserved', display)
        self.pcr_pid                    = read_bits(self.reader, 13, '  pcr pid', display)
        self.reserved_4                 = read_bits(self.reader, 4,  '  reserved', display)
        self.program_info_length        = read_bits(self.reader, 12, '  program info length', display)

        if self.program_info_length:
            self.reader.step_bytes(self.program_info_length)

        self.stream_list = []
        counter = 0
        num = self.section_length - 9 - self.program_info_length - 4
        while counter <  num:
            stream_type = self.reader.get_bits(8)
            if display:
                log('  [STREAM] - %s' % get_stream_type(stream_type))
                print_bits('    stream type', stream_type, display, to_hex = True)
            reserved_a      = read_bits(self.reader, 3,  '    reserved (7)', display)
            elementary_pid  = read_bits(self.reader, 13, '    elementary pid', display)
            reserved_b      = read_bits(self.reader, 4,  '    reserved', display)
            es_info_length  = read_bits(self.reader, 12, '    es info length', display)
            es_description = None
            descriptors = []
            counter += 5
            if es_info_length:
                es_description = self.data[self.reader.index - 1 : self.reader.index - 1 + es_info_length]
                descriptors = parse_descriptors(es_description, display)
                counter += es_info_length
                self.reader.step_bytes(es_info_length)
            self.stream_list.append(pmt_stream(stream_type,
                                               reserved_a,
                                               elementary_pid,
                                               reserved_b,
                                               es_info_length,
                                               es_description,
                                               descriptors))
        self.crc32 = read_bits(self.reader, 32, '  crc32', display, to_hex=True)

#
# NIT parser
# https://svn.baysse.fr/svn/pouchintv/docs/MPEG-2_Transport_Stream/49346_DVB.pdf
#
class nit(ts_packet):
    def __init__(self, data, display=False):
        ts_packet.__init__(self, data, display)

        if display:
            log('[NETWORK INFORMATION TABLE]')

        self.pointer_field              = read_bits(self.reader, 8,  '  pointer field', display)
        if self.pointer_field:
            self.reader.step_bytes(self.pointer_field)

        self.table_id                   = read_bits(self.reader, 8,  '  table id', display)
        self.section_syntax_indicator   = read_bits(self.reader, 1,  '  section syntax indicator', display)
        self.marker                     = read_bits(self.reader, 1,  '  reserved future use', display)
        self.reserved_1                 = read_bits(self.reader, 2,  '  reserved', display)
        self.section_length             = read_bits(self.reader, 12, '  section length', display)
        self.network_id                 = read_bits(self.reader, 16, '  network id', display)
        self.reserved_2                 = read_bits(self.reader, 2,  '  reserved', display)
        self.version_number             = read_bits(self.reader, 5,  '  version', display)
        self.current_next_indicator     = read_bits(self.reader, 1,  '  current next indicator', display)
        self.section_number             = read_bits(self.reader, 8,  '  section number', display)
        self.last_section_number        = read_bits(self.reader, 8,  '  last section number', display)
        self.reserved_3                 = read_bits(self.reader, 4,  '  reserved future use', display)
        self.network_descriptors_length = read_bits(self.reader, 12, '  network descriptors length', display)

        # For now, skip network descriptors
        if self.network_descriptors_length:
            description = self.data[self.reader.index - 1 : self.reader.index - 1 + self.network_descriptors_length]
            descriptors = parse_descriptors(description)
            self.reader.step_bytes(self.network_descriptors_length)

        self.reserved_4                   = read_bits(self.reader, 4,  '  reserved future use', display)
        self.transport_stream_loop_length = read_bits(self.reader, 12, '  transport stream loop length', display)

        self.stream_list = []
        counter = 0
        num = self.transport_stream_loop_length
        while counter <  num:
            if display:
                log('  [TRANSPORT STREAM] ')
            read_bits(self.reader, 16, '    transport stream id', display)
            read_bits(self.reader, 16, '    original network id', display)
            read_bits(self.reader, 4,  '    reserved for future use', display)
            tlen = read_bits(self.reader, 12,  '    transport descriptors length', display)
            counter += 6

            if tlen:
                description = self.data[self.reader.index - 1 : self.reader.index - 1 + tlen]
                descriptors = parse_descriptors(description)
                self.reader.step_bytes(tlen)
                counter += tlen

        self.crc32 = read_bits(self.reader, 32, '  crc32', display, to_hex = True)

#
# EIT parser
# en_300468v011101p section 5.2.4
#
class eit(ts_packet):
    def __init__(self, data, display=False):
        ts_packet.__init__(self, data, display)

        if display:
            log('[EVENT INFORMATION TABLE]')

        self.pointer_field              = read_bits(self.reader, 8,  '  pointer field', display)
        if self.pointer_field:
            self.reader.step_bytes(self.pointer_field)

        self.table_id                   = read_bits(self.reader, 8,  '  table id', display, to_hex=True)
        self.section_syntax_indicator   = read_bits(self.reader, 1,  '  section syntax indicator', display)
        self.marker                     = read_bits(self.reader, 1,  '  reserved future use', display)
        self.reserved_1                 = read_bits(self.reader, 2,  '  reserved', display)
        self.section_length             = read_bits(self.reader, 12, '  section length', display)
        self.service_id                 = read_bits(self.reader, 16, '  service id', display)
        self.reserved_2                 = read_bits(self.reader, 2,  '  reserved', display)
        self.version_number             = read_bits(self.reader, 5,  '  version', display)
        self.current_next_indicator     = read_bits(self.reader, 1,  '  current next indicator', display)
        self.section_number             = read_bits(self.reader, 8,  '  section number', display)
        self.last_section_number        = read_bits(self.reader, 8,  '  last section number', display)
        self.transport_stream_id        = read_bits(self.reader, 16, '  transport stream id', display)
        self.original_network_id        = read_bits(self.reader, 16, '  original network id', display)
        self.segment_last_section_number = read_bits(self.reader, 8,  '  segment last section number', display)
        self.last_table_id              = read_bits(self.reader, 8,  '  last table id', display, to_hex=True)

        done = False
        if self.section_length < 16:
            done = True
        while not done:
            event_id = read_bits(self.reader, 16,  '    event id', display)
            start_time = read_bits(self.reader, 40,  '    start time', display)
            duration = read_bits(self.reader, 24,  '    duration', display)
            running_status = read_bits(self.reader, 3,  '    running status', display)
            free_CA_mode = read_bits(self.reader, 1,  '    free CA mode', display)
            descriptors_loop_length = read_bits(self.reader, 12,  '    descriptors loop length', display)

            tlen = descriptors_loop_length
            description = self.data[self.reader.index - 1 : self.reader.index - 1 + tlen]
            descriptors = parse_descriptors(description)
            self.reader.step_bytes(tlen)

            done = True

class SCTE35(ts_packet):
    "SCTE-35 cue packet parser."

    def __init__(self, data, display=False):
        ts_packet.__init__(self, data, display)
        if display:
            log('[SCTE-35 CUE PACKET] payload_length = %d' % len(self.payload))
            log(dump_hex(self.payload, 16))
        # Parse according to section 7.2 in SCTE35 2013 standard
        self.first_byte               = read_bits(self.reader, 8, ' first_byte', display)
        # One byte of zero, then
        self.table_id                 = read_bits(self.reader, 8, ' table_id', display, to_hex=True)
        self.section_syntax_indicator = read_bits(self.reader, 1, ' section_syntax_indicator', display)
        self.private_indicator        = read_bits(self.reader, 1, ' private_indicator', display)
        reserved                      = read_bits(self.reader, 2, ' reserved', display)
        self.section_length           = read_bits(self.reader, 12, ' section_length', display)
        self.protocol_version         = read_bits(self.reader, 8, ' protocol_version', display)
        self.encrypted_packet         = read_bits(self.reader, 1, ' encrypted_packet', display)
        self.encryption_algorithm     = read_bits(self.reader, 6, ' encryption_algorithm', display)
        self.pts_adjustment           = read_bits(self.reader, 33, ' pts_adjustment', display)
        self.cw_index                 = read_bits(self.reader, 8, ' cw_index', display)
        self.tier                     = read_bits(self.reader, 12, ' tier', display)
        self.splice_command_length    = read_bits(self.reader, 12, ' splice_command_length', display)
        self.splice_command_type      = read_bits(self.reader, 8, ' splice_command_type', display)
        self.duration = -1
        self.splice_time_pts = -1
        # In one of the following methods we should read self.splice_command_length - 1 bytes
        # It actually says that the splice_command_type should not be included in the standard, but that doesn't agree
        # with the sample we got from RJIL.

        if self.splice_command_type == 0x00:
            self.splice_null(self.splice_command_length-1)
        elif self.splice_command_type == 0x04:
            self.splice_schedule(self.splice_command_length-1)
        elif self.splice_command_type == 0x05:
            self.splice_insert(self.splice_command_length-1)
        elif self.splice_command_type == 0x06:
            self.time_signal(self.splice_command_length-1)
        elif self.splice_command_type == 0x07:
            self.bandwidth_reservation(self.splice_command_length-1)
        elif self.splice_command_type == 0xff:
            self.private_command(self.splice_command_length-1)
        else: #Reserved types
            log("ERROR: SCTE splice_command_type = %d not known" % splice_command_type)

        self.descriptor_loop_length = read_bits(self.reader, 16, ' descriptor_loop_length', display)
        # There are this many byte of descriptor data
        if self.descriptor_loop_length > 0:
            self.splice_descriptor(self.descriptor_loop_length, display)
        if self.encrypted_packet:
            self.encrypted_crc_32 = read_bits(self.reader, 32, ' E_CRC_32', display, to_hex=True)
        self.crc_32               = read_bits(self.reader, 32, ' CRC_32', display, to_hex=True)

    def splice_null(self, nr_bytes):
        data = read_bits(self.reader, 8*nr_bytes, " splice_null_data", True)
        log("SCTE35: splice_null(%d)" % nr_bytes)

    def splice_schedule(self, nr_bytes):
        log("SCTE35: splice_schedule(%d)" % nr_bytes)

    def splice_insert(self, nr_bytes):
        display = True
        log("SCTE35: splice_insert(%d)" % nr_bytes)
        splice_event_id = read_bits(self.reader, 32, ' splice_event_id', display)
        splice_event_cancel_indicator = read_bits(self.reader, 1, ' splice_event_cancel_indidator', display)
        reserved = read_bits(self.reader, 7, ' reserved', display)
        if splice_event_cancel_indicator == 0:
            out_of_network_indicator = read_bits(self.reader, 1, ' out_of_network_indicator', display)
            program_splice_flag = read_bits(self.reader, 1, ' program_splice_flag', display)
            duration_flag = read_bits(self.reader, 1, ' duration_flag', display)
            splice_immediate_flag = read_bits(self.reader, 1, ' splice_immediate_flag', display)
            reserved = read_bits(self.reader, 4, ' reserved', display)
            if program_splice_flag == 1 and splice_immediate_flag == 0:
                self.splice_time(display)
            if program_splice_flag == 0:
                component_count = read_bits(self.reader, 8, ' component_count', display)
                for i in range(component_count):
                    component_tag = read_bits(self.reader, 8, ' out_of_network_indicator', display)
                    if splice_immediate_flag == 0:
                        self.splice_time(display)
        if duration_flag == 1:
            self.break_duration(display )
        unique_program_id = read_bits(self.reader, 16, ' unique_program_id', display)
        avail_num = read_bits(self.reader, 8, ' avail_num', display)
        avails_expected = read_bits(self.reader, 8, ' avails_expected', display)

    def time_signal(self, nr_bytes):
        log("SCTE35: time_signal(%d)" % nr_bytes)

    def bandwidth_reservation(self, nr_bytes):
        log("SCTE35: bandwidth_reservation(%d)" % nr_bytes)

    def private_command(self, nr_bytes):
        log("SCTE35: private_command(%d)" % nr_bytes)

    def splice_time(self, display):
        log("SCTE35: splice_time")
        time_specified_flag = read_bits(self.reader, 1, ' time_specified_flag', display)
        if time_specified_flag == 1:
            reserved = read_bits(self.reader, 6, ' reserved', display)
            pts_time = read_bits(self.reader, 33, ' pts_time', display)
            self.splice_time_pts = pts_time
        else:
            reserved = read_bits(self.reader, 7, ' reserved', display)

    def break_duration(self, display):
        log("SCTE35: break_duration")
        auto_return = read_bits(self.reader, 1, ' auto_return', display)
        reserved = read_bits(self.reader, 6, ' reserved', display)
        self.duration = read_bits(self.reader, 33, ' duration', display)

    def splice_descriptor(self, length, display):
        log("SCTE35: splice_descriptor")
        splice_descriptor_tag = read_bits(self.reader, 8, ' splice_descriptor_tag', display)
        descriptor_length = read_bits(self.reader, 8, ' descriptor_length', display)
        assert descriptor_length == length - 2
        identifier = read_bits(self.reader, 32, ' identifier', display, to_hex=True)
        for i in range(descriptor_length-4):
            data = read_bits(self.reader, 8, ' private_byte', display)


    def __str__(self):
        return "Type = %x, time=%d, duration=%d" % (self.splice_command_type,
                                                    self.splice_time_pts,
                                                    self.duration)

#
# PES parser
#
class pes(object):
    def __init__(self, data, display=False):
        self.reader = bitreader(data)
        self.data = data
        self.pts = 0.0
        self.dts = 0.0

        if display:
            log('')
            log('[PACKETIZED ELEMENTARY STREAM]')

        self.packet_start_prefix    = read_bits(self.reader, 24, '  packet start prefix', display)
        self.stream_id              = read_bits(self.reader, 8,  '  stream id', display)
        self.pes_packet_length      = read_bits(self.reader, 16, '  pes packet length', display)

        # check if we have optional pes header
        self.marker_bits                = read_bits(self.reader, 2,  '  marker bits (2)', display)
        self.scrambling_control         = read_bits(self.reader, 2,  '  scrambling control', display)
        self.priority                   = read_bits(self.reader, 1,  '  priority', display)
        self.data_alignment_indicator   = read_bits(self.reader, 1,  '  data alignment indicator', display)
        self.copyright                  = read_bits(self.reader, 1,  '  copyright', display)
        self.original_or_copy           = read_bits(self.reader, 1,  '  original or copy', display)
        self.pts_dts_indicator          = read_bits(self.reader, 2,  '  pts dts indicator', display)
        self.escr_flag                  = read_bits(self.reader, 1,  '  escr flag', display)
        self.es_rate_flag               = read_bits(self.reader, 1,  '  es rate flag', display)
        self.dsm_trick_mode_flag        = read_bits(self.reader, 1,  '  dsm trick mode flag', display)
        self.additional_copy_info_flag  = read_bits(self.reader, 1,  '  additional copy info flag', display)
        self.crc_flag                   = read_bits(self.reader, 1,  '  pes crc flag', display)
        self.extension_flag             = read_bits(self.reader, 1,  '  pes extension flag', display)
        self.pes_header_length          = read_bits(self.reader, 8,  '  pes header length', display)

        pos_1 = self.reader.tell()

        if self.pts_dts_indicator == 0x02:
            self.pts_dts_marker_1   = read_bits(self.reader,  4, '   marker (2)', display)
            self.pts_a              = read_bits(self.reader,  3, '   pts 1(3)', display)
            self.pts_dts_marker_2   = read_bits(self.reader,  1, '   marker', display)
            self.pts_b              = read_bits(self.reader, 15, '   pts 2(3)', display)
            self.pts_dts_marker_3   = read_bits(self.reader,  1, '   marker', display)
            self.pts_c              = read_bits(self.reader, 15, '   pts 3(3)', display)
            self.pts_dts_marker_4   = read_bits(self.reader,  1, '   marker', display)
            self.pts = (self.pts_a << 30) + (self.pts_b << 15) + (self.pts_c)
            #log('   pts: %s' % (int(self.pts) / 90000.0))
        elif self.pts_dts_indicator == 0x03:
            self.pts_dts_marker_5   = read_bits(self.reader,  4, '   marker (3)', display)
            self.pts_a              = read_bits(self.reader,  3, '   pts 1(3)', display)
            self.pts_dts_marker_6   = read_bits(self.reader,  1, '   marker', display)
            self.pts_b              = read_bits(self.reader, 15, '   pts 2(3)', display)
            self.pts_dts_marker_7   = read_bits(self.reader,  1, '   marker', display)
            self.pts_c              = read_bits(self.reader, 15, '   pts 3(3)', display)
            self.pts_dts_marker_8   = read_bits(self.reader,  1, '   marker', display)
            self.pts_dts_marker_9   = read_bits(self.reader,  4, '   marker (1)', display)
            self.dts_a              = read_bits(self.reader,  3, '   dts 1(3)', display)
            self.pts_dts_marker_10  = read_bits(self.reader,  1, '   marker', display)
            self.dts_b              = read_bits(self.reader, 15, '   dts 2(3)', display)
            self.pts_dts_marker_11  = read_bits(self.reader,  1, '   marker', display)
            self.dts_c              = read_bits(self.reader, 15, '   dts 3(3)', display)
            self.pts_dts_marker_12  = read_bits(self.reader,  1, '   marker', display)
            self.pts = (self.pts_a << 30) + (self.pts_b << 15) + (self.pts_c)
            self.dts = (self.dts_a << 30) + (self.dts_b << 15) + (self.dts_c)
            #log('   pts: %s' % (int(self.pts) / 90000.0))
            #log('   dts: %s' % (int(self.dts) / 90000.0))

        pos_2 = self.reader.tell()
        #log('pos1=%s, pos2=%s, len=%s' % (pos_1, pos_2, self.pes_header_length))

        # Stuffing
        if pos_2 - pos_1 < self.pes_header_length:
            num_stuff = self.pes_header_length - (pos_2 - pos_1)
            self.reader.step_bytes(num_stuff)

        # parse further...
        self.payload_offset = self.reader.index - 1
        self.header_len = self.reader.index - 1
        #print 'PES Header Lengths:', 9 + self.pes_header_length, self.header_len
        #log(dump_hex(self.payload[0:10*16], 16))

    def add_data(self, data):
        self.data += data

    @property
    def payload(self):
        return self.data[self.payload_offset:]

    @property
    def size(self):
        return len(self.data) - 6

#
# TS Importer Observer interface
#
class observer(object):
    def on_pat(self, pat):
        pass
    def on_pmt(self, importer, pmt):
        pass
    def on_pes(self, pid, pes):
        pass
    def flush(self):
        pass
    def get_scte35_pids(self):
        return set()

#
# TS importer
#
class ts_importer(object):
    def __init__(self, observer, options, log_cc=False):
        self.preflight_packets = 0
        self.has_pat = False
        self.has_pmt = False
        self.has_nit = False
        self.pmt_pid = -1
        self.nit_pid = -1
        self.observer = observer
        self.options = options
        self.log_cc = log_cc
        self.pids = {}
        self.scte35_pids = set()

        self.num_packets = 0
        self.num_bytes = 0
        self.num_stuffing_packets = 0
        self.pid_counter = {}
        self.packet_errors = 0

        self.first_pts = 0
        self.last_pts = 0

        self.eit_data = ''

    # Use the preflight for vod to get pat and pmt
    def preflight(self, data):
        offset = 0
        pids = {}
        while offset < len(data) and ord(data[offset]) == 0x47:
            packet = ts_packet(data[offset:offset+188], display=False, check_cc=False)
            #log(dump_hex(packet.data, 16))

            if not pids.has_key(packet.pid):
                pids[packet.pid] = 0
            pids[packet.pid] += 1
            self.preflight_packets += 1

            if packet.pid == PAT_PID:
                self._handle_pat(packet)
            elif packet.pid == self.pmt_pid:
                self._handle_pmt(packet)
                #return True
            elif packet.pid == self.nit_pid:
                self._handle_nit(packet)
                #return True
            elif packet.pid == EIT_PID or packet.pid == EIT_PID2:
                self._handle_eit(packet)
            offset += 188

            if self.has_pmt and self.preflight_packets > 100:
                return True

        log('pids found: %s' % pids)
        raise Exception('Could not find pat/pmt during preflight')

    def observe_pid(self, pid):
        if not self.pids.has_key(pid):
            self.pids[pid] = None

    def add_data(self, data):
        offset = 0
        while offset + 188 <= len(data) and ord(data[offset]) == 0x47:
            packet = ts_packet(data[offset:offset+188], display=self.options['verbose'] >= 3, check_cc=True)
            #log(dump_hex(packet.data, 16))

            if not self.pid_counter.has_key(packet.pid):
                #Break into packets
                self.pid_counter[packet.pid] = {}
                self.pid_counter[packet.pid]['num_packets'] = 0
                self.pid_counter[packet.pid]['num_bytes'] = 0
                self.pid_counter[packet.pid]['ts_header_bytes'] = 0
                self.pid_counter[packet.pid]['pes_header_bytes'] = 0
                self.pid_counter[packet.pid]['payload_bytes'] = 0
            pes_header_len = 0

            if packet.transport_error_indicator:
                self.packet_errors += 1
            elif packet.pid == PAT_PID:
                self._handle_pat(packet)
            elif packet.pid == CA_PID:
                #log('TODO: CA packet')
                pass
            elif packet.pid == STUFFING_PID:
                self.num_stuffing_packets += 1
            #elif packet.pid == SDT_PID:
            #    log('TODO: SDT packet')
            elif packet.pid == self.pmt_pid:
                self._handle_pmt(packet)
            elif packet.pid == self.nit_pid:
                self._handle_nit(packet)
            elif packet.pid in self.scte35_pids:
                self._handle_scte35(packet)
            elif packet.pid in self.pids.keys():
                if len(packet.payload) > 3 and \
                   ord(packet.payload[0]) == 0x00 and \
                   ord(packet.payload[1]) == 0x00 and \
                   ord(packet.payload[2]) == 0x01 and \
                   ord(packet.payload[3]) == 0xBE:
                    log('Zero data (00 00 01 BE) for pid {0}'.format(packet.pid))
                    pass
                elif packet.payload_unit_start_indicator == 1:
                    # Send old pes if any
                    if self.pids[packet.pid]:
                        if self.pids[packet.pid].pes_packet_length:
                            if self.pids[packet.pid].pes_packet_length != self.pids[packet.pid].size:
                                log('LENGTH ERROR, pid={0} should be {1} but is {2}'.format(packet.pid, self.pids[packet.pid].pes_packet_length, len(self.pids[packet.pid].data) - 6))
                        self.observer.on_pes(packet.pid, self.pids[packet.pid])

                    # Create new pes
                    p = pes(packet.payload, display=self.options['verbose'] >= 2)
                    self.pid_counter[packet.pid]['pes_header_bytes'] += p.header_len
                    if self.first_pts == 0:
                        self.first_pts = p.pts
                    self.last_pts = p.pts

                    pes_header_len = p.header_len
                    if p.pes_packet_length:
                        if p.pes_packet_length == p.size:
                            self.observer.on_pes(packet.pid, p)
                            p = None
                    self.pids[packet.pid] = p

                elif self.pids[packet.pid]:
                    self.pids[packet.pid].add_data(packet.payload)

            self.pid_counter[packet.pid]['num_packets'] += 1
            self.pid_counter[packet.pid]['num_bytes'] += 188
            self.pid_counter[packet.pid]['ts_header_bytes'] += packet.header_len
            self.pid_counter[packet.pid]['payload_bytes'] += 188 - packet.header_len - pes_header_len
            self.num_packets += 1
            self.num_bytes += 188
            offset += 188

    def flush(self):
        for pid in self.pids:
            pes = self.pids[pid]
            if pes:
                self.observer.on_pes(pid, pes)
        self.observer.flush()

    def print_cc_summary(self, video, data):
        print "CC in %s video stream" % video
        for d in data:
            print "  Format: %s" % d['format']
            if d.has_key('field'):
                print "    Standard: %s, field=%d" % (d['std'], d['field'])
            else:
                print "    Standard: %s" % d['std']
            print "    Data: bitrate=%(bitrate)d, #chars=%(char)d, #padding=%(padding)d" % d['data']

    def report(self):
        duration = (self.last_pts - self.first_pts) / 90000.0

        log('')
        log('############################################')
        log('Statistics')
        log('Num packets: %d' % self.num_packets)
        log('Num bytes: %d' % self.num_bytes)
        log('Num stuffing packets: %d' % self.num_stuffing_packets)
        log('Duration: %.2f sec' % duration)
        log('First PTS: %.2f sec' % self.first_pts)
        log('Last PTS: %.2f sec' % self.last_pts)
        log('Transport errors: %s' % self.packet_errors)

        log('')
        log('pids found:')
        tot_header_bytes = 0
        tot_bytes = 0
        for k,v in self.pid_counter.iteritems():
            log(' pid={0} {1}'.format(k, v))
            tot_header_bytes += v['ts_header_bytes']
            tot_header_bytes += v['pes_header_bytes']
            tot_bytes += v['num_bytes']

        log('')
        fraction = 0.0
        if tot_bytes:
            fraction = (100.0 * tot_header_bytes) / tot_bytes

        log('TS + PES header bytes: {0}({1}) = {2:.2}%'.format(tot_header_bytes, tot_bytes, fraction))

        if tot_bytes:
            for pid in self.pids:
                if self.pid_counter.has_key(pid):
                    bytes = self.pid_counter[pid]['payload_bytes']
                    log('Bitrate for pid {0}: {1:.2f} kbps'.format(pid, bytes * 8.0 / duration / 1000.0))
            log('Total bitrate: {0:.2f} kbps'.format(tot_bytes * 8.0 / duration / 1000.0))
            log('############################################')

        if self.log_cc:
            mpeg_video_cc = self.observer.mpeg_video_parser.get_cc_summary()
            h264_cc = self.observer.h264_parser.get_cc_summary()
            if mpeg_video_cc:
                self.print_cc_summary("MPEG2", mpeg_video_cc)
            if h264_cc:
                self.print_cc_summary("H.264", h264_cc)

    def _handle_pat(self, packet):
        if self.has_pat:
            return
        pat_packet = pat(packet.data, display=self.options['verbose'] >= 2)
        self.observer.on_pat(pat_packet)
        for info in pat_packet.pmt_info:
            if info.program_num == 0x00:
                self.nit_pid = info.program_pid
                self.has_pat = True
            else:
                self.pmt_pid = info.program_pid
                self.has_pat = True
                return

    def _handle_pmt(self, packet):
        #if self.has_pmt:
        #    return
        pmt_packet = pmt(packet.data, display=self.options['verbose'] >= 2)
        self.observer.on_pmt(self, pmt_packet)
        self.has_pmt = True
        self.scte35_pids = self.observer.get_scte35_pids()

    def _handle_nit(self, packet):
        if self.has_nit:
            return
        nit_packet = nit(packet.data, display=self.options['verbose'] >= 2)
        self.has_nit = True

    def _handle_eit(self, packet):
        if packet.payload_unit_start_indicator:
            if self.eit_data:
                eit_packet = eit(self.eit_data, display=self.options['verbose'] >= 2)
            self.eit_data = packet.data
        elif self.eit_data:
            self.eit_data += packet.payload

    def _handle_scte35(self, packet):
        scte35 = SCTE35(packet.data, display=self.options['verbose'] >= 2)
        print "SCTE35 parsed: %s" % scte35

#
# MPEG audio parser
#
class mpeg_audio_parser(object):
    def __init__(self, display=False):
        self.display = display

    def add_pes(self, data, pts, dts):
        self.data = data
        self.pts = pts
        self.dts = dts
        self.offset = 0

        if self.display:
            log('')
            log('[MPEG AUDIO PES] pts={0} dts={1}'.format(pts, dts))

        time_now = datetime.datetime.utcnow()
        t = time.mktime(time_now.timetuple()) + time_now.microsecond / 1000000.0
        return [frame(data, True, t, self.pts, self.dts, 'A')]

#
# MPEG video parser
#
class mpeg_video_parser(object):
    def __init__(self, display=False, cc_basename=None):
        self.display = display
        atsc_base = cc_basename and cc_basename + "_ATSC" or None
        scte_base = cc_basename and cc_basename + "_SCTE" or None
        self.ATSC_parser = ATSCParser(display, atsc_base)
        self.SCTE_parser = SCTEParser(display, scte_base)

        self.codes = {0x00 : self.parse_picture_header,
                      0xb2 : self.parse_user_data,
                      0xb3 : self.parse_sequence_header,
                      0xb5 : self.parse_extension_header,
                      0xb8 : self.parse_gop_header}

    def get_cc_summary(self):
        cc_data = []
        atsc_cc = self.ATSC_parser.get_cc_summary()
        if atsc_cc:
            cc_data.extend(atsc_cc)
        scte_cc = self.SCTE_parser.get_cc_summary()
        if scte_cc:
            cc_data.extend(scte_cc)
        return cc_data

    def add_pes(self, data, pts, dts):
        self.data = data
        self.pts = pts
        self.dts = dts
        self.offset = 0

        if self.display:
            log('')
            log('[MPEG VIDEO PES] pts={0} dts={1}'.format(pts, dts))
        code, valid = self.next_startcode()
        frames = []
        while valid:
            if self.codes.has_key(code):
                parse_method = self.codes[code]
                tmp_frame = parse_method()
                if tmp_frame:
                    frames.append(tmp_frame)

            code, valid = self.next_startcode()
        return frames

    def next_startcode(self):
        while self.offset + 3 < len(self.data):
            if ord(self.data[self.offset + 0]) == 0x00 and \
               ord(self.data[self.offset + 1]) == 0x00 and \
               ord(self.data[self.offset + 2]) == 0x01:
                code = ord(self.data[self.offset + 3])
                self.offset += 4
                return code, True
            else:
                self.offset += 1
        return None, False

    def parse_picture_header(self):
        print_bits('  [PICTURE HEADER]', 0x0100, self.display, to_hex = True)
        reader = bitreader(self.data[self.offset : self.offset + 4])
        read_bits(reader,  10, '    temporal sequence number', self.display)
        frame_type = read_bits(reader,  3, '    frame type', self.display)
        read_bits(reader,  16, '    vbv delay', self.display)

        data = self.data[self.offset : self.offset + 4]
        sync = True
        frame_type_str = 'I'
        if frame_type == 2:
            frame_type_str = 'P'
            sync = False
        elif frame_type == 3:
            frame_type_str = 'B'
            sync = False

        time_now = datetime.datetime.utcnow()
        t = time.mktime(time_now.timetuple()) + time_now.microsecond / 1000000.0
        return frame(data, sync, t, self.pts, self.dts, frame_type_str)

    def parse_sequence_header(self):
        print_bits('  [SEQUENCE HEADER]', 0x01b3, self.display, to_hex = True)
        reader = bitreader(self.data[self.offset : self.offset + 8])
        read_bits(reader,  12, '    horizontal size', self.display)
        read_bits(reader,  12, '    vertical size', self.display)
        read_bits(reader,  4, '    aspect ratio', self.display)
        read_bits(reader,  4, '    frame rate', self.display)
        read_bits(reader,  18, '    bit rate', self.display)
        read_bits(reader,  1, '    marker (1)', self.display)
        read_bits(reader,  10, '    vbv buffer size', self.display)
        read_bits(reader,  1, '    constrainded parameter flag', self.display)
        read_bits(reader,  1, '    load intra quantizer matrix', self.display)
        read_bits(reader,  1, '    load non-intra quantizer matrix', self.display)

    def parse_extension_header(self):
        print_bits('  [EXTENSION HEADER]', 0x01b5, self.display, to_hex = True)

    def parse_gop_header(self):
        print_bits('  [GOP HEADER]', 0x01b8, self.display, to_hex = True)
        reader = bitreader(self.data[self.offset : self.offset + 4])
        read_bits(reader,  1, '    drop frame flag', self.display)
        read_bits(reader,  5, '    hour', self.display)
        read_bits(reader,  6, '    minute', self.display)
        read_bits(reader,  1, '    marker (1)', self.display)
        read_bits(reader,  6, '    second', self.display)
        read_bits(reader,  6, '    frame', self.display)
        read_bits(reader,  1, '    closed GOP', self.display)
        read_bits(reader,  1, '    broken GOP', self.display)
        read_bits(reader,  5, '    marker (0)', self.display)

    def parse_user_data(self):
        """Parse user data, and look for ATSC CC information in particular."""
        print_bits('  [user_data]', 0x01b2, display=self.display, to_hex = True)
        reader = bitreader(self.data[self.offset:])
        first_byte = read_bits(reader, 8, '    user_data_type_code', display=self.display, to_hex=True)
        if first_byte != 0x3:
            user_identifier = read_bits(reader, 24, '    user identifier_3', display=self.display, to_hex=True)
            if first_byte == 0x47 and int(user_identifier) == 0x413934:
                self.ATSC_parser.parse(reader, self.pts)
        else:
            self.SCTE_parser.parse(reader, self.pts)

def bit(command, num):
    return (command >> num) & 0x01

def EBSPtoRBSP(streamBuffer, end_bytepos, begin_bytepos):
    d = ''
    for i in range(0, begin_bytepos):
        d += streamBuffer[i]

    count = 0
    if end_bytepos < begin_bytepos:
        return end_bytepos

    j = begin_bytepos
    for i in range(begin_bytepos, end_bytepos):
        use_this = True
        # starting from begin_bytepos to avoid header information
        # in NAL unit, 0x000000, 0x000001 or 0x000002 shall not occur at any byte-aligned position
        if count == 2 and ord(streamBuffer[i]) < 0x03:
            return -1
        if count == 2 and ord(streamBuffer[i]) == 0x03:
            #check the 4th byte after 0x000003, except when cabac_zero_word is used, in which case the last three bytes of this NAL unit must be 0x000003
            if (i < end_bytepos-1) and (ord(streamBuffer[i+1]) > 0x03):
                return -1
            #if cabac_zero_word is used, the final byte of this NAL unit(0x03) is discarded, and the last two bytes of RBSP must be 0x0000
            if i == end_bytepos - 1:
                return j

            use_this = False
            count = 0

        if use_this:
            d += streamBuffer[i]
            #streamBuffer[j] = streamBuffer[i]
            if ord(streamBuffer[i]) == 0x00:
                count += 1
            else:
                count = 0
            j += 1

    return j, d

def RBSPtoSODB(streamBuffer, last_byte_pos):
    # find trailing 1
    bitoffset = 0
    ctr_bit = int(ord(streamBuffer[last_byte_pos - 1])) & (0x01 << bitoffset)   # set up control bit
    while ctr_bit == 0:
        # find trailing 1 bit
        bitoffset += 1
        if bitoffset == 8:
            if last_byte_pos == 0:
                raise "PELLE"
            last_byte_pos -= 1
            bitoffset = 0
        ctr_bit = int(ord(streamBuffer[last_byte_pos - 1])) & (0x01 << (bitoffset))

    # We keep the stop bit for now
    return last_byte_pos

class SEIParser(object):
    "Parser of SEI NAL unit."

    def __init__(self, display=False, cc_basename=None):
        self.display = display
        self.cc_basename = cc_basename
        self.ATSC_parser = ATSCParser(display, cc_basename)

    def get_cc_summary(self):
        cc_data = self.ATSC_parser.get_cc_summary()
        if cc_data:
            cc_data['format'] = 'ATSC'
        return cc_data

    def parse(self, nal_data, pts):
        "Parse SEI NAL unit."

        #log('nal_data: %d' % len(nal_data))
        length, nal_data_2 = EBSPtoRBSP(nal_data, len(nal_data), 5)
        #log('length=%d' %  len(nal_data_2))
        length2 = RBSPtoSODB(nal_data_2, length)

        reader = bitreader(nal_data_2[5:])

        if self.display:
            log('[H264 SEI] ({0} bytes) pts={1}'.format(len(nal_data), pts))
        #log(dump_hex(nal_data, 16))
        #log(dump_hex(nal_data_2, 16))

        tmp_byte = reader.get_bits(8)
        while True:
            # h264_2005.pdf
            # 7.3.2.3.1 Supplemental enhancement information message syntax

            # read payload type
            payload_type = 0

            while tmp_byte == 0xff:
                payload_type += 255
                tmp_byte = reader.get_bits(8)
            payload_type += tmp_byte

            # read payload size
            payload_size = 0
            tmp_byte = reader.get_bits(8)
            while tmp_byte == 0xff:
                payload_size += 255
                tmp_byte = reader.get_bits(8)
            payload_size += tmp_byte

            if self.display:
                #log('')
                log('  SEI payload type={0} size={1}'.format(payload_type, payload_size))

            if payload_size == 0:
                import sys
                log("ERROR: Payload size = 0 in SEI Parser")
                break

            sei_payload = reader.step_bytes(payload_size)
            if payload_type == 4:
                self.parse_sei_payload_4(sei_payload, pts)

            tmp_byte = reader.get_bits(8)
            #log('tmp_byte=%s' % hex(tmp_byte))
            if tmp_byte == 0x80:
                break

    def parse_sei_payload_4(self, payload, pts):
        # a_72_part_1.pdf
        # 6.4.2 Caption, AFD and Bar Data
        reader = bitreader(payload)
        read_bits(reader, 8, '    country code (0xb5)', display=self.display, to_hex=True)
        read_bits(reader, 16, '    provider code (0x31)', display=self.display, to_hex = True)
        user_identifier = read_bits(reader, 32, '    user identifier', display=self.display, to_hex=True)
        if int(user_identifier) == 0x44544731:
            if self.display:
                log('      [AFD Data]')

            read_bits(reader, 1, '      zero', display=self.display)
            aff = read_bits(reader, 1, '      active_format_flag', display=self.display)
            read_bits(reader, 6, '      reserved', display=self.display)
            if aff == 1:
                read_bits(reader, 4, '        reserved', display=self.display)
                read_bits(reader, 4, '        active_format (area of interest)', display=self.display)

        elif int(user_identifier) == 0x47413934:
            self.ATSC_parser.parse(reader, pts)

class UserDataParser(object):
    "Baseclass for user data, and Closed Captioning in particular"

    def __init__(self, display=False, cc_basename=None):
        self.display = display
        self.cc_basename = cc_basename
        if scc is not None:
            self.cc_writers = (scc.SccWriter(self.cc_basename, 0),
                               scc.SccWriter(self.cc_basename, 1))
        self.format = None

    def has_pts_offset(self):
        return self.cc_writers[0].has_pts_offset() and self.cc_writers[1].has_pts_offset()

    def set_pts_offset(self, pts_offset):
        self.cc_writers[0].set_pts_offset(pts_offset)
        self.cc_writers[1].set_pts_offset(pts_offset)

    def parse(self, reader, pts_time):
        "Must be overridden by subclass."

    def get_cc_summary(self):
        field_data = []
        for i,cw in enumerate(self.cc_writers):
            cw.close() #To get the last data written
            cc = cw.get_cc_summary()
            if cc:
                cc['field'] = i + 1
                cc['format'] = self.format
                field_data.append(cc)
        return field_data

class ATSCParser(UserDataParser):
    "Parser of ATSC user data, and Closed Captioning in particular."

    def __init__(self, display=False, cc_basename=None):
        UserDataParser.__init__(self, display, cc_basename)
        if cea708:
            self.cea708_parser = cea708.Cea708Parser()
        else:
            self.cea708_parser = None
        self.format = "ATSC"

    def get_cc_summary(self):
        cc_summary = UserDataParser.get_cc_summary(self)
        if cc_summary:
            for field in cc_summary:
                field['format'] = 'ATSC'
        else:
            cc_summary = []
        if cea708:
            cea708_summary = self.cea708_parser.get_cc_summary()
            if cea708_summary:
                cea708_summary['format'] = 'ATSC'
                cc_summary.append(cea708_summary)
        return cc_summary

    def calc_time(self, pts_time):
        pts_time -= 900000
        ss = pts_time/90000
        fr = int(29.97*(pts_time % 90000)/90000.0)
        hh = ss/3600
        mm = ss/60
        ss -= hh*3600 + mm*60
        newtime = "%02d:%02d:%02d:%02d" % (hh, mm, ss, fr)
        return newtime

    def parse(self, reader, pts_time):
        "Parse data using provided reader."
        if self.display:
            log('      [ATSC User Data]')

        texts = []

        # a_53-Part-4-2009.pdf
        # Table 6.8 ATSC_user_data Syntax
        # Table 6.10 Captioning Data Syntax
        type_code = read_bits(reader, 8, '      user data type code', display=self.display)
        if int(type_code) == 3:
            # CEA-708 [1], Table 2.
            # http://en.wikipedia.org/wiki/CEA-708

            # (Standard: CEA-708: 4.4)
            # http://www.scribd.com/doc/56413155/CEA-708-D

            read_bits(reader, 1, '      process em data flag', display=self.display)
            read_bits(reader, 1, '      process cc data flag', display=self.display)
            read_bits(reader, 1, '      additional data flag', display=self.display)
            cc_count = read_bits(reader, 5, '      cc count', display=self.display)
            read_bits(reader, 8, '      em data', display=self.display)

            text = ''
            property = ''
            #print "\npts_time=%s cc_count = %d " % (self.calc_time(pts_time), cc_count),
            for i in range(0, cc_count):
                if self.display:
                    log('      cc_data_pkt')
                read_bits(reader, 5, '        marker bits (0x1f)', display=self.display, to_hex=True)
                cc_valid = read_bits(reader, 1, '        cc valid', display=self.display)
                cc_type = read_bits(reader, 2, '        cc type', display=self.display)
                cc_data_1 = read_bits(reader, 8, '        cc_data_1', display=self.display, to_hex=True)
                cc_data_2 = read_bits(reader, 8, '        cc_data_2', display=self.display, to_hex=True)
                cc_data = (cc_data_1, cc_data_2)
                #print " (%02x, %02x)" % cc_data,
                #print "(%02c,%02c)" % ((cc_data_1 & 0x7f), (cc_data_2 & 0x7f))

                # cc_type 0 : NTSC_CC_FIELD_1
                # cc_type 1 : NTSC_CC_FIELD_2
                # cc_type 2 : DTVCC_PACKET_DATA
                # cc_type 3 : DTVCC_PACKET_START

                if cc_valid == 0:
                # cc_valid == 0 means padding. Can also be used with cc_type to end DTVCC data
                    if self.display:
                        log('          [CEA-708 cc_valid == 0 (padding)]')
                    if self.cea708_parser:
                        self.cea708_parser.count_padding()
                elif cc_type == 0 or cc_type == 1:
                    # CEA-608, aka line21
                    # http://en.wikipedia.org/wiki/EIA-608
                    if self.display:
                        log('          [CEA-608 PACKET DATA type=%d] (%02x, %02x)' % (cc_type, cc_data_1, cc_data_2))
                    self.cc_writers[cc_type].add_data(cc_data, pts_time)
                elif cc_type == 2 or cc_type == 3:
                    if self.display:
                        log('          [CEA-708 PACKET DATA type=%d] (%02x, %02x)' % (cc_type, cc_data_1, cc_data_2))
                    if self.cea708_parser:
                        self.cea708_parser.add_data(cc_data, cc_type, pts_time)

            read_bits(reader, 8, '      marker bits (0xff)', display=self.display, to_hex=True)

            if len(text):
                texts.append([property, ' - ' + text])

        # log(parsed data)
        if self.display:
            for t in texts:
                log('{0} {1}'.format(t[0], t[1]))

class SCTEParser(UserDataParser):
    "Parser for SCTE-20 data that may contain CEA-608 Closed Captioning."

    def __init__(self, display=False, cc_basename=None):
        UserDataParser.__init__(self, display, cc_basename)
        self.format = "SCTE"

    def parse(self, reader, pts_time):
        "Parse data using provided reader."
        reserved = read_bits(reader, 7, '    reserved_bits', display=self.display)
        if reserved & 0x17 == 0: # Check the 6 LSB =0
            vbi_data_flag = read_bits(reader, 1, '    vbi_data_flag', display=self.display)
            if vbi_data_flag:
                if self.display:
                    log('      [SCTE-20 User Data]')
                cc_count = read_bits(reader, 5, '    cc_count', display=self.display)
                for i in range(cc_count):
                    cc_priority = read_bits(reader, 2, '    cc_priority', display=self.display)
                    field_number = read_bits(reader, 2, '    field_number', display=self.display)
                    line_offset = read_bits(reader, 5, '    line_offset', display=self.display)
                    cc_data_1 = read_bits(reader, 8, '    cc_data_1', display=self.display, to_hex=True)
                    cc_data_2 = read_bits(reader, 8, '    cc_data_2', display=self.display, to_hex=True)
                    marker_bit = read_bits(reader, 1, '    marker_bit', display=self.display)
                    cc_bits_1 = invtab[cc_data_1]
                    cc_bits_2 = invtab[cc_data_2]
                    if 1<= field_number <= 2:
                        if self.cc_writers:
                            self.cc_writers[field_number-1].add_data((cc_bits_1, cc_bits_2), pts_time)
                    else:
                        log("WARNING: Cannot handle 608 field_number=%d" % field_number)
                non_real_time_video_count = read_bits(reader, 4, '    non_real_time_video_count', display=self.display)

#
# H264 parser
#
class h264_parser(object):
    def __init__(self, display=False, cc_basename=None):
        self.display = display
        self.construction_frame = None
        self.data = ''
        self.times = []
        self.sei_parser = SEIParser(display, cc_basename)

    def get_cc_summary(self):
        return self.sei_parser.ATSC_parser.get_cc_summary()

    def next_start_code(self, data, offset):
        while offset + 5 < len(data):
            code = (ord(data[offset]) == 0x00) and \
                   (ord(data[offset + 1]) == 0x00) and \
                   (ord(data[offset + 2]) == 0x00) and \
                   (ord(data[offset + 3]) == 0x01)
            code2 = (ord(data[offset]) == 0x00) and \
                    (ord(data[offset + 1]) == 0x00) and \
                    (ord(data[offset + 2]) == 0x01)
            if code == 1:
                return offset, 4
            elif code2 == 1:
                return offset, 3
            offset += 1
        return -1, 0

    def print_nal_unit_types(self, data):
        offset = 0
        while offset + 5 < len(data):
            code = (ord(data[offset]) == 0x00) and \
                   (ord(data[offset + 1]) == 0x00) and \
                   (ord(data[offset + 2]) == 0x00) and \
                   (ord(data[offset + 3]) == 0x01)
            if code == 1:
                print 'Nal Unit Type=', ord(data[offset + 4]) & 0x1f
            offset += 1

    def add_pes(self, data, pts, dts, flush=False):
        if self.sei_parser and not self.sei_parser.ATSC_parser.has_pts_offset():
            self.sei_parser.ATSC_parser.set_pts_offset(pts)
        #self.print_nal_unit_types(data)

        self.data += data
        if pts > -1:
            self.times.append([pts, dts])
        if len(self.times) > 2:
            self.times.remove(self.times[0])
            log('TOO MANY PTS, DTS, REMOVE FIRST')
        #log('pes size={0} pts={1} times={2}'.format(len(data), pts, len(self.times)))
        #log(dump_hex(data, 16))

        # Calculate offsets to all start codes
        start_codes = []
        offset, offset_len = self.next_start_code(self.data, 0)
        while offset >= 0:
            start_codes.append([offset, offset_len])
            offset, offset_len = self.next_start_code(self.data, offset + 2)

        if len(start_codes) == 0:
            return []

        # Calculate length of all nal units
        lengths = []
        for i in range(len(start_codes) - 1):
            length = start_codes[i + 1][0] - start_codes[i][0]
            lengths.append(length)
        if flush:
            lengths.append(len(self.data) - start_codes[-1][0])

        #log('start codes %s' % start_codes)
        #log('lengths %s' % lengths)

        # Extract frames
        sps_pps = ''
        frames = []
        last_pos = 0
        for i in range(len(lengths)):
            tmp = start_codes[i][1]
            nal_data = self.data[start_codes[i][0] : start_codes[i][0] + lengths[i]]
            nal_type = ord(nal_data[tmp]) & 0x1f
            last_pos += len(nal_data)

            if tmp == 3:
                nal_data = nal_data[0] + nal_data

            #log('got nal type=%d with size=%d' %(nal_type, len(nal_data))

            #self.pts_dts_indicator
            sync = False
            if nal_type == 6:
                # SEI
                self.sei_parser.parse(nal_data, pts)
            elif nal_type == 7:
                # SPS
                if self.display:
                    text = binascii.b2a_base64(nal_data[4:])
                    log('[SPS]: %s' % text)
                    sps_pps = sps_pps + text.strip() + ' '
            elif nal_type == 8:
                # PPS
                if self.display:
                    text = binascii.b2a_base64(nal_data[4:])
                    log('[PPS]:%s' % text)
                    sps_pps = sps_pps + text.strip() + ' '
            elif nal_type == 9:
                # Delimiter
                pass
            elif nal_type == 1 or nal_type == 5:
                if nal_type == 5:
                    sync = True

                reader = bitreader(nal_data[5:])
                first_mb_in_slice = ue(reader)
                slice_type = ue(reader)
                pic_parameter_set_id = ue(reader)
                frame_num = read_bits(reader, 2, 'frame_num', display=False)

                if self.display:
                    log('')
                    log('[H264 SLICE] (%d bytes)' % len(nal_data))
                    log('  nal unit type          : %s' % nal_type)
                    log('  first mb in slice      : %s' % first_mb_in_slice)
                    log('  slice type             : %s' % slice_type)
                    log('  pic parameter set id   : %s' % pic_parameter_set_id)
                    log('  frame num              : %s' % frame_num   )

                if first_mb_in_slice == 0:
                    # pts/dts
                    time_data = self.times[0]
                    self.times.remove(time_data)
                    pts_i = time_data[0]
                    dts_i = time_data[1]

                    if self.display:
                        log('  pts                    :%s (%.3fs)' % (pts_i, pts_i / 90000.0))
                        log('  dts                    :%s (%.3fs)' % (dts_i, dts_i / 90000.0))

                    # if we have a complete frame, store it
                    if self.construction_frame:
                        frames.append(self.construction_frame)
                        self.construction_frame = None

                    # frame type
                    frame_type = 'unknown'
                    if slice_type == 0 or slice_type == 5:
                        frame_type = 'P'
                    elif slice_type == 1 or slice_type == 6:
                        frame_type = 'B'
                    elif slice_type == 2 or slice_type == 7:
                        frame_type = 'I'

                    time_now = datetime.datetime.utcnow()
                    t = time.mktime(time_now.timetuple()) + time_now.microsecond / 1000000.0

                    # create new frame
                    self.construction_frame = frame(nal_data, sync, t, pts_i, dts_i, frame_type)
                elif self.construction_frame:
                    self.construction_frame.data += nal_data
                    #log('appending {0} bytes to frame, tot size={1}'.format(len(nal_data), len(self.construction_frame.data)))
            elif nal_type == 12:
                # Filler data
                pass
            else:
                log('Unknown NAL type={0}'.format(nal_type))

        if len(lengths):
            pos = last_pos + start_codes[0][0]
            self.data = self.data[pos:]

        if sps_pps:
            print ''
            print '[SPS/PPS]', sps_pps

        return frames

    def flush(self):
        frames = self.add_pes('', 0, 0, flush=True)
        if self.construction_frame:
            frames.append(self.construction_frame)
        return frames

SampleRates = {0 : 96000,
               1 : 88200,
               2 : 64000,
               3 : 48000,
               4 : 44100,
               5 : 32000,
               6 : 24000,
               7 : 22050,
               8 : 16000,
               9 : 12000,
               10 : 11025,
               11 : 8000,
               12 : 7350}

#
# AAC parser - ADTS
#
class aac_parser_adts(object):
    def __init__(self, display=False):
        self.display = display
        self.data = ''

    def add_pes(self, data, pts, dts):
        self.data += data
        frames = []

        done = False
        while not done:
            if len(self.data) < 7:
                break

            aac_frame_len = ((ord(self.data[3]) & 0x3) << 11) + (ord(self.data[4]) << 3) + ((ord(self.data[5]) & 0xe0) >> 5)
            if aac_frame_len == 0:
                # Check why this happens
                log("WARNING: aac_frame_len == 0, but %d data bytes remain" % len(self.data))
                break
            if len(self.data) >= aac_frame_len:
                frame_data = self.data[0:aac_frame_len]
                self.parse_frame(frame_data, pts, dts)
                time_now = datetime.datetime.utcnow()
                t = time.mktime(time_now.timetuple()) + time_now.microsecond / 1000000.0
                frames.append(frame(frame_data[7:], True, t, pts, dts, 'audio'))
                self.data = self.data[aac_frame_len:]
            else:
                break

        return frames

    def parse_frame(self, data, pts, dts):
        if self.display:
            log('')
            log('[AAC ADTS frame] {0} bytes pts={1} dts={2}'.format(len(data), pts, dts))

        #with open('sample_he_v2.aac', 'w') as f:
        #    f.write(data)
        #    exit(-1)

        # Table 1.A.5 in subpart 1 (page 108)
        # adts_frame()

        reader = bitreader(data)
        read_bits(reader,  12, '  sync word', self.display, to_hex = True)
        read_bits(reader, 1, '  id', self.display)
        read_bits(reader, 2, '  layer', self.display)
        protection_absent = read_bits(reader, 1, '  protection absent', self.display)
        aot = read_bits(reader, 2, '  profile object type', self.display)
        read_bits(reader, 4, '  sample frequency index', self.display)
        read_bits(reader, 1, '  private bit', self.display)
        read_bits(reader, 3, '  channel configuration', self.display)
        read_bits(reader, 1, '  original/copy', self.display)
        read_bits(reader, 1, '  home', self.display)

        #read_bits(reader, 2, '  emphasis', self.display)

        read_bits(reader, 1, '  copyright identification bit', self.display)
        read_bits(reader, 1, '  copyright identification start', self.display)
        aac_len = read_bits(reader, 13, '  aac frame length', self.display)
        read_bits(reader, 11, '  adts buffer fullnes', self.display)
        num_rows = read_bits(reader, 2, '  number of raw data blocks in frame', self.display)

        if protection_absent == 0:
            read_bits(reader, 16, '  crc', self.display)

        for i in range(0, num_rows + 1):
            #print '    raw data block'
            id_syn_ele = -1

            # Table 4.3 in subpart 4 (page 13)
            # raw_data_block()
            while id_syn_ele != 7:
                id_syn_ele = read_bits(reader, 3, '  id_syn_ele', self.display)
                element_instance_tag = read_bits(reader, 4, '  element_instance_tag', self.display)

                # Table 4.5 in subpart 4 (page 14)
                # channel_pair_element()

                if id_syn_ele == 1:
                    #print 'Channel Pair Element'
                    common_window = read_bits(reader, 1, '  common_window', self.display)
                    if common_window:
                        #print '    ics_info()'
                        ics_reserved_bit = read_bits(reader, 1, '    ics_reserved_bit', self.display)
                        window_sequence = read_bits(reader, 2, '    window_sequence', self.display)
                        window_shape = read_bits(reader, 1, '    window_shape', self.display)

                        if window_sequence == 2:
                            read_bits(reader, 4, '    max_sfb', self.display)
                            read_bits(reader, 7, '    scale_factor_grouping', self.display)
                        else:
                            read_bits(reader, 6, '    max_sfb', self.display)
                            predictor_data_present = read_bits(reader, 1, '    predictor_data_present', self.display)
                            if predictor_data_present:
                                #print 'Not supported A'
                                break
                                #if aot == 1:
                                #    predictor_reset = read_bits(reader, 1, '    predictor_reset', self.display)
                                #    if predictor_reset:
                                #        print 'ERROR A'
                                #    break

                            ms_mask_present = read_bits(reader, 2, '    ms_mask_present', self.display)
                            if ms_mask_present == 1:
                                #print 'Not supported B'
                                break

                            # Individual channel stream
                            # Table 4.50
                            read_bits(reader, 8, '    global_gain', self.display)

                elif id_syn_ele == 5:
                    #print 'Program Config Element'
                    read_bits(reader, 2, '    object_type', self.display)
                    break

                elif id_syn_ele == 6:
                    #print 'Fill Element'
                    count = read_bits(reader, 4, '    count', self.display)
                    if count == 15:
                        count = count + read_bits(reader, 8, '    esc_count', self.display) - 1
                    for j in range(count):
                        extension_type = read_bits(reader, 4, '    extension_type', self.display)
                        read_bits(reader, 4, '    align', self.display)
                        break
                    break

                else:
                    #print 'Unsupported element'
                    break

#
# AAC parser - LATM
#
class aac_parser_latm(object):
    def __init__(self, display=False):
        self.display = display
        self.data = ''
        self.sampling_frequency_index = 0

    def add_pes(self, data, pts, dts):

        self.data += data
        frames = []

        reader = bitreader(self.data)
        done = False
        while not done:
            if len(self.data) < 2:
                break

            if self.display:
                log('')
                log('[AAC LATM frame] {0} bytes pts={1} dts={2}'.format(len(data), pts, dts))

            sync_word = read_bits(reader, 11, '  sync word', self.display, to_hex=True)
            if sync_word != 0x2b7:
                log('Bad sync word, clear buffer')
                data = ''
                break

            audio_mux_length_bytes = read_bits(reader, 13, '  audio mux length bytes', self.display)
            if audio_mux_length_bytes > len(self.data):
                break

            audio_mux_data = reader.step_bytes(audio_mux_length_bytes)
            self.data = self.data[audio_mux_length_bytes+3:]
            f, pos = self.parse_audio_mux_element(audio_mux_data, pts, dts)
            frames += f
            if pos!= len(data) - 2:
                raise Exception('Bad AAC LATM frame data')

        return frames

    def require(self, a, b, desc):
        if a != b:
            msg = 'Pase Failure, {0} != {1} for {2}'.format(str(a), str(b), desc)
            raise Exception(msg)

    def parse_audio_mux_element(self, data, pts, dts):
        if self.display:
            log('    [Audio Mux Element]')
        reader = bitreader(data)
        use_same_stream_mux = read_bits(reader, 1, '    use same stream mux', self.display)
        num_sub_frames = 0
        if not use_same_stream_mux:
            num_sub_frames = self.parse_stream_mux_config(reader)

        frames = []
        time_now = datetime.datetime.utcnow()
        t = time.mktime(time_now.timetuple()) + time_now.microsecond / 1000000.0
        offset = 0
        for i in range(0, num_sub_frames+1):
            if self.display:
                log('      [Subframe {0}]'.format(i))
            length = self.parse_patyload_length_info(reader)
            frame_data = self.parse_patyload_mux(reader, length)

            # Create audio frame
            frames.append(frame(frame_data, True, t, pts + offset, dts, 'audio'))
            offset += (1024 * 90000) / SampleRates[self.sampling_frequency_index]

        #log('data at pos', reader.tell())
        return frames, reader.tell()

    def parse_stream_mux_config(self, reader):
        num_sub_frames = 0
        if self.display:
            log('      [Stream Mux Config]')
        audio_mux_version = read_bits(reader, 1, '        audio mux version', self.display)
        self.require(audio_mux_version, 0, 'audio mux version')
        audio_mux_version_a = 0
        if audio_mux_version == 1:
            audio_mux_version_a = read_bits(reader, 1, '        audio mux version A', self.display)
        if audio_mux_version_a == 0:
            if audio_mux_version == 1:
                log('TODO A')
                return

            all_streams_same_time_framing = read_bits(reader, 1, '        all streams same time framing', self.display)
            num_sub_frames = read_bits(reader, 6, '        num sub frames', self.display)
            num_program = read_bits(reader, 4, '        num program', self.display)
            num_layers = read_bits(reader, 3, '        num layers', self.display)

            self.require(all_streams_same_time_framing, 1, 'all streams same time framing')
            self.require(num_program, 0, 'num programs')
            self.require(num_layers, 0, 'num layers')
            self.parse_audio_specific_config(reader)

            frame_length_type = read_bits(reader, 3, '      frame length type', self.display)
            self.require(frame_length_type, 0, 'frame length type')
            if frame_length_type == 0:
                latm_buffer_fullnes = read_bits(reader, 8, '      latm buffer fullnes', self.display)

            other_data_present = read_bits(reader, 1, '      other data present', self.display)
            if other_data_present:
                while True:
                    other_data_len_esc = read_bits(reader, 1, '      other data len esc', self.display)
                    other_data_len_tmp = read_bits(reader, 8, '      other data len tmp', self.display)
                    if other_data_len_esc == 0:
                        break
            crc_check_present = read_bits(reader, 1, '      crc check present', self.display)
            self.require(crc_check_present, 0, 'crc check present')

        return num_sub_frames

    def parse_audio_specific_config(self, reader):
        if self.display:
            log('      [Audio Specific Config]')
        audio_object_type = read_bits(reader, 5, '        audio object type', self.display)
        self.sampling_frequency_index = read_bits(reader, 4, '        sampling frequency index', self.display)
        read_bits(reader, 4, '        channel configuration', self.display)
        self.require(audio_object_type, 2, 'audio object type')
        self.parse_ga_specific_config(reader)

    def parse_ga_specific_config(self, reader):
        if self.display:
            log('      [GA Specific Config]')
        read_bits(reader, 1, '        frame length flag', self.display)
        dep = read_bits(reader, 1, '        depends on core coder', self.display)
        self.require(dep, 0, 'depends on core coder')
        ext = read_bits(reader, 1, '        extension flag', self.display)
        self.require(ext, 0, 'extension flag')

    def parse_patyload_length_info(self, reader):
        # Assuming:
        #   all_streams_same_time_framing = 1
        #   frame_length_type = 0
        length = 0
        while True:
            tmp = read_bits(reader, 8, '        tmp', self.display)
            length += tmp
            if tmp != 255:
                break
        return length

    def parse_patyload_mux(self, reader, length):
        # Assuming:
        #   all_streams_same_time_framing = 1
        #   frame_length_type = 0
        return reader.step_bytes(length)

def hamming_8_4(value, bits):
    result = 0
    for i in range(0, bits, 2):
        pos = bits - 2 - i
        b = bit(value, pos)
        #log('pos', pos, 'bit', b, 'exp', (2 ** (i/2)))
        result += 2 ** (i/2) * b
    return result

#
# AC3 parser
#
class ac3_parser(object):
    def __init__(self, display=False):
        self.display = display
        self.data = ''

    def add_pes(self, data, pts, dts):
        frames = []

        #log(dump_hex(data, 16))

        reader = bitreader(data)
        read_bits(reader,  16, '  sync word', self.display, to_hex = True)

        time_now = datetime.datetime.utcnow()
        t = time.mktime(time_now.timetuple()) + time_now.microsecond / 1000000.0
        frames.append(frame(data, True, t, pts, dts, 'audio AC3'))

        return frames

#
# TeleText EBU Parser
#
def parse_teletext_ebu(data, display):
    reader = bitreader(data)

    read_bits(reader,  2, '  reserved future use', display)
    read_bits(reader,  1, '  field parity', display)
    read_bits(reader,  5, '  line offset', display)
    fc = read_bits(reader,  8, '  framing code', display, to_hex = True)

    # ets_300706e01p.pdf
    # 7.1.2	Packet address
    d = read_bits(reader,  16, '  magazine number and packet number', display=False)
    magazine_number = bit(d, 14) + 2 * bit(d, 12) + 4 * bit(d, 10)
    packet_number = bit(d, 8) + 2 * bit(d, 6) + 4 * bit(d, 4) + 8 * bit(d, 2) + 16 * bit(d, 0)
    print_bits('  magazine number', magazine_number, display)
    print_bits('  packet number', packet_number, display)

    if packet_number <= 25:
        payload_len = 40
        if packet_number == 0:
            payload_len = 32
            # ets_300706e01p.pdf
            # 9.3.1	Page header
            #prefix = reader.step_bytes(5)
            X = read_bits(reader, 8, '    page number units', display)
            Y = read_bits(reader, 8, '    page number tens', display)
            page_number_units = hamming_8_4(X, 8)
            page_number_tens = hamming_8_4(Y, 8)
            page_number = 10 * page_number_tens + page_number_units
            print_bits('    page number=', page_number, display)
            read_bits(reader, 8, '    subcode s1', display)
            read_bits(reader, 8, '    subcode s2 + c4', display)
            read_bits(reader, 8, '    subcode s3', display)
            read_bits(reader, 8, '    subcode s4 + c5, c6', display)
            read_bits(reader, 8, '    control bits c7 - c10', display)
            read_bits(reader, 8, '    control bits c11  c14', display)

        payload = reader.step_bytes(payload_len)
        #print dump_hex(payload, 16)

        d2 = []
        for i in range(0, len(payload)):
            char = invtab[ord(payload[i])] & 0x7f
            if char < 32 or char > 122:
                d2.append(0x20)
            else:
                d2.append(char)

            #d2.append(invtab[ord(payload[i])])

        data_str = ''.join(['%s' % chr(c & 0x7f) for c in d2])
        if display:
            log('  data ({0} bytes) = {1}'.format(len(data_str), data_str))
            #print dump_hex(data_str, 16)

        return {'data': data_str, 'language' : 'unknown'}

    else:
        if display:
            log('TODO: page enhancement data packets')

    return None

#
# TeleText subtitle parser
#
def parse_teletext_subtitle(data, display=False):
    reader = bitreader(data)

    #display = True

    if display:
        log('')
        log('[TELETEXT]')
    # dvt-txt_a041.pdf
    # 4.3 Syntax for PES data field
    data_identifier = read_bits(reader,  8, '  data identifier', display, to_hex = True)

    frames = []
    while reader.tell() < len(data):
        if display:
            log('')
            log('[TELETEXT UNIT]')
        read_bits(reader,  8, '  data unit id', display, to_hex = True)
        dul = read_bits(reader,  8, '  data unit length', display, to_hex=True)

        data_field = reader.step_bytes(dul)

        frame = parse_teletext_ebu(data_field, display)
        if frame:
            frames.append(frame)

    return frames

#
# DVB subtitle parser
# en300743.v1.2.1.pdf section 7
#
class parse_dvb_subtitle(object):
    def __init__(self, data, display=False):
        self.display = display
        reader = bitreader(data)

        log('')
        log('[DVB SUBTITLING]')
        data_identifier = read_bits(reader,  8, '  data identifier', display, to_hex = True)
        subtitle_stream_id = read_bits(reader,  8, '  subtitle stream id', display)

        byte = reader.get_bits(8)
        while byte == 0x0f:
            segment_type = reader.get_bits(8)
            page_id = reader.get_bits(16)
            segment_length = reader.get_bits(16)
            payload = reader.step_bytes(segment_length)
            byte = reader.get_bits(8)

            # parse segment types
            parser = None
            log('')
            if segment_type == 0x10:
                log('  [PAGE COMPOSITION SEGMENT]')
                parser = self._parse_page_composition_segment
            elif segment_type == 0x11:
                log('  [REGION COMPOSITION SEGMENT]')
                parser = self._parse_region_composition_segment
            elif segment_type == 0x12:
                log('  [CLUT DEFINITION SEGMENT]')
                parser = self._parse_CLUT_definition_segment
            elif segment_type == 0x13:
                log('  [OBJECT DATA SEGMENT]')
                parser = self._parse_object_data_segment
            else:
                log('  [DVB SUBTITLING SEGMENT]')

            print_bits('    segment type', segment_type, self.display, to_hex = True)
            print_bits('    page id', page_id, self.display)
            print_bits('    segment length', segment_length, self.display)

            if parser:
                parser(payload)

    def _parse_page_composition_segment(self, payload):
        reader = bitreader(payload)
        read_bits(reader, 8, '    page time out', self.display)
        read_bits(reader, 4, '    page version number', self.display)
        read_bits(reader, 2, '    page state', self.display)
        read_bits(reader, 2, '    reserved', self.display)

        while reader.tell() < len(payload):
            log('')
            read_bits(reader, 8, '      region id', self.display)
            read_bits(reader, 8, '      reserved', self.display)
            read_bits(reader, 16, '      region horizontal address', self.display)
            read_bits(reader, 16, '      region vertical address', self.display)

        if reader.tell() != len(payload) + 1:
            log('segment length error', reader.tell(), len(payload))

    def _parse_region_composition_segment(self, payload):
        reader = bitreader(payload)
        read_bits(reader, 8, '    region id', self.display)
        read_bits(reader, 4, '    region version number', self.display)
        read_bits(reader, 1, '    page fill flag', self.display)
        read_bits(reader, 3, '    reserved', self.display)
        read_bits(reader, 16, '    region width', self.display)
        read_bits(reader, 16, '    region height', self.display)
        read_bits(reader, 3, '    region level of compatibility', self.display)
        read_bits(reader, 3, '    region depth', self.display)
        read_bits(reader, 2, '    reserved', self.display)
        read_bits(reader, 8, '    CLUT id', self.display)
        read_bits(reader, 8, '    region 8-bit pixel code', self.display)
        read_bits(reader, 4, '    region 4-bit pixel code', self.display)
        read_bits(reader, 2, '    region 2-bit pixel code', self.display)
        read_bits(reader, 2, '    reserved', self.display)

        while reader.tell() < len(payload):
            log('')
            read_bits(reader,  16, '      object id', self.display)
            object_type = read_bits(reader,   2, '      object type', self.display)
            read_bits(reader,   2, '      object provider flag', self.display)
            read_bits(reader,  12, '      object horizontal position', self.display)
            read_bits(reader,   4, '      reserved', self.display)
            read_bits(reader,  12, '      object vertical position', self.display)

            if object_type == 0x01 or object_type == 0x02:
                read_bits(reader,  8, '      foreground pixel code', self.display)
                read_bits(reader,  8, '      background pixel code', self.display)

        if reader.tell() != len(payload) + 1:
            log('segment length error', reader.tell(), len(payload))

    def _parse_CLUT_definition_segment(self, payload):
        reader = bitreader(payload)
        read_bits(reader,  8, '    CLUT id', self.display)
        read_bits(reader,  4, '    CLUT version number', self.display)
        read_bits(reader,  4, '    reserved', self.display)

        while reader.tell() < len(payload):
            log('')
            read_bits(reader,  8, '      CLUT entry id', self.display)
            read_bits(reader,  1, '      2-bit entry CLUT flag', self.display)
            read_bits(reader,  1, '      4-bit entry CLUT flag', self.display)
            read_bits(reader,  1, '      8-bit entry CLUT flag', self.display)
            read_bits(reader,  4, '      reserved', self.display)
            full_range_flag = read_bits(reader,  1, '      full range flag', self.display)

            if full_range_flag == 1:
                read_bits(reader,  8, '      Y-value', self.display)
                read_bits(reader,  8, '      Cr-value', self.display)
                read_bits(reader,  8, '      Cb-value', self.display)
                read_bits(reader,  8, '      T-value', self.display)
            else:
                read_bits(reader,  6, '      Y-value', self.display)
                read_bits(reader,  4, '      Cr-value', self.display)
                read_bits(reader,  4, '      Cb-value', self.display)
                read_bits(reader,  2, '      T-value', self.display)

        if reader.tell() != len(payload) + 1:
            log('segment length error', reader.tell(), len(payload))

    def _parse_object_data_segment(self, payload):
        reader = bitreader(payload)
        read_bits(reader,  16, '    object id', self.display)
        read_bits(reader,   4, '    object version number', self.display)
        ocm = read_bits(reader,   2, '    object coding method', self.display)
        read_bits(reader,   1, '    non modifying colour flag', self.display)
        read_bits(reader,   1, '    reserved', self.display)

        if ocm == 0x00:
            read_bits(reader,   16, '    top field data block length', self.display)
            read_bits(reader,   16, '    bottom field data block length', self.display)
            num_bytes = len(payload) - reader.tell() + 1
            print_bits('    image bytes', num_bytes, self.display, to_hex = False)
        elif ocm == 0x01:
            num = read_bits(reader,   8, '    number of codes', self.display)
            for i in range(0, num):
                read_bits(reader,   8, '    character code', self.display)

def read_id3_size(size):
    a = size & 0x7f
    size >>= 8
    b = size & 0x7f
    size >>= 8
    c = size & 0x7f
    size >>= 8
    d = size & 0x7f

    return a + (b << 7) + (c << 14) + (d << 21)

#
# ID3 parser
#
#id3_num = 0

class frame_id3:
    def __init__(self):
        self.identifier = ''
        self.size = 0

class id3_parser(object):
    def __init__(self, data, pts, dts, display=False):
        self.frames = []
        self.display = display
        reader = bitreader(data)

        log('')
        log('[Metadata] size={0} pts={1} dts={2}'.format(len(data), pts, dts))

        #global id3_num
        #id3name = 'id3_{0}'.format(id3_num)
        #with open(id3name, 'w') as f:
        #    f.write(data)
        #id3_num += 1

        #log(data)
        #log(dump_hex(data, 16))

        identifier = reader.step_bytes(3)
        read_bits(reader,  8, '  major version', display)
        read_bits(reader,  8, '  minor version', display)
        read_bits(reader,  8, '  flags', display)
        size = read_bits(reader,  32, '  size', display)

        size2 = read_id3_size(size)
        log('  size={0} means {1}'.format(size, size2))

        if size > 1000000:
            print 'BAD ID3 size'
            return

        while reader.tell() < len(data):
            frame = self.id3_frame(reader, display)
            self.frames.append(frame)
        #d = reader.step_bytes(size)
        #log('data=%s' % d)

    def id3_frame(self, reader, display):
        frame = frame_id3()
        frame.identifier = reader.step_bytes(4)
        log('  frame identifier %s' % frame.identifier)
        frame.size = read_bits(reader,  32, '    size', display)
        size2 = read_id3_size(size)
        log('    size={0} means {1}'.format(size, size2))
        read_bits(reader,  16, '    flags', display)
        d = reader.step_bytes(frame.size)

        #for c in d:
        #    print ord(c)

        if frame.identifier == 'PRIV':
            pos = d.find('\0')
            if pos >= 0:
                log('    owner=%s' % d[0:pos])
                log('    data=%s' % d[pos+1:])
            else:
                log('    data=%s' % d)
        else:
            log('    data=%s' % d)
        #log(dump_hex(d, 16))
        return frame

#
# Metadata parser
#
class metadata_parser(object):
    def __init__(self, data, pts, dts, display=False):
        self.display = display
        reader = bitreader(data)

        log('')
        log('[Metadata] size={0} pts={1} dts={2}'.format(len(data), pts, dts))
        log(data)

        log(dump_hex(data, 16))

        #while reader.tell() < len(data):
        #self.read_section(reader, display)

    def read_section(self, reader, display):
        read_bits(reader,  8, '  table id', display)
        read_bits(reader,  1, '  section syntax indicator', display)
        read_bits(reader,  1, '  private indicator', display)
        read_bits(reader,  1, '  random access indicator', display)
        read_bits(reader,  1, '  decoder config flag', display)
        read_bits(reader,  12, '  metadata section length', display)
        read_bits(reader,  8, '  metadata service id', display)
        read_bits(reader,  8, '  reserved', display)
        read_bits(reader,  2, '  section fragment indication', display)
        read_bits(reader,  5, '  version number', display)
        read_bits(reader,  1, '  current next indicator', display)
        read_bits(reader,  8, '  section number', display)
        read_bits(reader,  8, '  last section number', display)

    def read_au_cell(self, reader, display):
        read_bits(reader,  8, '  metadata service id', display)
        read_bits(reader,  8, '  sequence number', display)
        read_bits(reader,  2, '  cell fragment indication', display)
        read_bits(reader,  1, '  decoder config flag', display)
        read_bits(reader,  1, '  random access indicator', display)
        read_bits(reader,  4, '  reserved', display)
        length = read_bits(reader,  16, '  AU cell data length', display)
        bytes = reader.step_bytes(length)

#
# Parser observer
#
class parser_observer(observer):
    def __init__(self, options={}):
        self.mpeg_video_pid = -1
        self.mpeg_audio_pid = -1
        self.h264_pid = -1
        self.aac_pid = -1
        self.ac3_pid = -1
        self.teletext_pid = -1
        self.dvb_pid = -1
        self.metadata_pid = -1
        self.scte35_pids = set()
        self.options = options

        # If video data should be logged
        if options.has_key('video'):
            self.video_display = options['video']
        else:
            self.video_display = False

        # If audio data should be logged
        if options.has_key('audio'):
            self.audio_display = options['audio']
        else:
            self.audio_display = False

        # If text data should be logged
        if options.has_key('text'):
            self.text_display = options['text']
        else:
            self.text_display = False

        if options.has_key('cc'):
            cc_basename = options['cc']
        else:
            cc_basename = None

        # Create some codec parsers
        self.h264_parser = h264_parser(display=self.video_display, cc_basename=cc_basename)
        self.mpeg_video_parser = mpeg_video_parser(display=self.video_display, cc_basename=cc_basename)
        self.aac_parser = aac_parser_adts(display=self.audio_display)
        self.ac3_parser = ac3_parser(display=self.audio_display)
        self.mpeg_audio_parser = mpeg_audio_parser(display=self.audio_display)

    def on_pat(self, pat):
        pass

    def on_pmt(self, importer, pmt):
        for stream in pmt.stream_list:
            if stream.stream_type in (STREAM_TYPE_MPEG1_VIDEO, STREAM_TYPE_MPEG2_VIDEO, STREAM_TYPE_MPEG2_VIDEO_2):
                self.mpeg_video_pid = stream.elementary_pid
                importer.observe_pid(stream.elementary_pid)
            if stream.stream_type == STREAM_TYPE_MPEG1_AUDIO or stream.stream_type == STREAM_TYPE_MPEG2_AUDIO:
                self.mpeg_audio_pid = stream.elementary_pid
                importer.observe_pid(stream.elementary_pid)
            if stream.stream_type == STREAM_TYPE_H264:
                self.h264_pid = stream.elementary_pid
                importer.observe_pid(stream.elementary_pid)
                #pass
            elif stream.stream_type == STREAM_TYPE_AAC or stream.stream_type == STREAM_TYPE_AUDIO_ADTS:
                self.aac_pid = stream.elementary_pid
                importer.observe_pid(stream.elementary_pid)
                #pass
            #elif stream.stream_type == STREAM_TYPE_PRIVATE:
            #    self.ac3_pid = stream.elementary_pid
            #    importer.observe_pid(stream.elementary_pid)
            #    #pass
            elif stream.stream_type == STREAM_TYPE_METADATA:
                self.metadata_pid = stream.elementary_pid
                importer.observe_pid(stream.elementary_pid)
            elif stream.stream_type == STREAM_TYPE_SCTE35:
                self.scte35_pids.add(stream.elementary_pid)
                importer.observe_pid(stream.elementary_pid)
            elif stream.stream_type == STREAM_TYPE_PRIVATE:
                for desc in stream.descriptors:
                    if desc.tag == TELETEXT_SUBTITLE_DESCRIPTOR:
                        self.teletext_pid = stream.elementary_pid
                        importer.observe_pid(stream.elementary_pid)
                        #pass
                    elif desc.tag == DVB_SUBTITLE_DESCRIPTOR:
                        if self.dvb_pid == -1:
                            self.dvb_pid = stream.elementary_pid
                            importer.observe_pid(stream.elementary_pid)

    def on_pes(self, pid, pes):
        if pid == self.mpeg_video_pid:
            frames = self.mpeg_video_parser.add_pes(pes.payload, pes.pts, pes.dts)
            if self.options['verbose'] > 0:
                for frame in frames:
                    log(frame)
        if pid == self.mpeg_audio_pid:
            frames = self.mpeg_audio_parser.add_pes(pes.payload, pes.pts, pes.dts)
            if self.options['verbose'] > 0:
                for frame in frames:
                    log(frame)
        if pid == self.h264_pid:
            frames = self.h264_parser.add_pes(pes.payload, pes.pts, pes.dts)
            if self.options['verbose'] > 0:
                for frame in frames:
                    log(frame)
        elif pid == self.aac_pid:
            frames = self.aac_parser.add_pes(pes.payload, pes.pts, pes.dts)
            if self.options['verbose'] > 0:
                for frame in frames:
                    log(frame)
        elif pid == self.ac3_pid:
            frames = self.ac3_parser.add_pes(pes.payload, pes.pts, pes.dts)
            if self.options['verbose'] > 0:
                for frame in frames:
                    log(frame)
        elif pid == self.teletext_pid:
            frames = parse_teletext_subtitle(pes.payload, display=self.text_display)
            #from cavena import parse_teletext_subtitle_cavena
            #frames = parse_teletext_subtitle_cavena(pes.payload, pes.pts, pid)

        elif pid == self.dvb_pid:
            parse_dvb_subtitle(pes.payload, display=self.text_display)
            #pass
        elif pid == self.metadata_pid:
            id3_parser(pes.payload, pes.pts, pes.dts, display=self.text_display)
            #pass

    def flush(self):
        frames = self.h264_parser.flush()
        if self.options['verbose'] > 0:
            for frame in frames:
                log(frame)

    def get_scte35_pids(self):
        return self.scte35_pids

#
# Key frame observer
#
class key_frame_observer(observer):
    def __init__(self):
        self.key_frames = []
        self.data_file = None
        self.h264_parser = h264_parser(display=False)

    def on_pat(self, pat):
        pass

    def on_pmt(self, importer, pmt):
        for stream in pmt.stream_list:
            if stream.stream_type == 0x1b:
                if stream.elementary_pid != pmt.pcr_pid:
                    raise Exception('Video pid must have PCR')
                importer.observe_pid(stream.elementary_pid)

    def on_pes(self, pid, pes):
        frames = self.h264_parser.add_pes(pes.payload, pes.pts, pes.dts)
        for frame in frames:
            if frame.sync:
                log(frame)
                if self.data_file:
                    self.key_frames.append(frame)
                    if len(self.key_frames) > 10:
                        self.key_frames.pop(0)
                        file = open(self.data_file, "wb")
                        for key_frame in self.key_frames:
                            file.write(str(key_frame) + '\n')

def handle_http(url, importer):
    parts = urlparse.urlsplit(url)
    conn = httplib.HTTPConnection(parts.netloc, timeout=10)
    conn.set_debuglevel(3)
    conn.connect()
    conn.request('GET', parts.path)
    data = conn.getresponse().read()
    importer.preflight(data)
    global cc_map
    cc_map.clear()
    importer.add_data(data)
    importer.flush()

def handle_file(filename, nr_bytes_to_read, importer):
    with open(filename, 'rb') as f:
        bytes = 188*100000
        #f.read(24)
        if nr_bytes_to_read > 0:
            bytes = min(bytes, nr_bytes_to_read)
        data = f.read(bytes)
        nr_bytes_to_read -= len(data)
        try:
            importer.preflight(data)
        except Exception, e:
            print 'preflight error:', e
            importer.report()
            return

        num_bytes = len(data)
        importer.add_data(data)

        done = False
        while not done:
            if nr_bytes_to_read >= 0:
                bytes = min(bytes, nr_bytes_to_read)
            data = f.read(bytes)
            num_bytes += len(data)
            nr_bytes_to_read -= len(data)
            importer.add_data(data)
            if nr_bytes_to_read == 0 or len(data) != bytes:
                done = True
        importer.flush()
        #print 'bytes read=', num_bytes, 'packets read=', num_bytes / 188

def handle_udp(host, port, importer):
    sock = create_socket(int(port), host)
    in_list = [sock]
    out_list = []
    except_list = []
    log('Start sampling on host={0} port={1}'.format(host, port))
    while True:
        (in_, out_, exc_) = select.select(in_list, out_list, except_list, 1.0)
        for fd in in_:
            if fd == sock:
                data = sock.recv(1500)
                importer.add_data(data)

def main():
    parser = optparse.OptionParser(usage='%prog [options] <file path>|<http url>|<multicast address> <multicast port>')
    parser.add_option('-v', '--verbose', help='increase verbosity', action='count', default=0)
    parser.add_option('-o', '--observer', help='type of observer [default: %default]', default='parser')
    if scc:
        parser.add_option('-C', help="log CC statistics", action='store_true', default=False, dest='log_cc')
        parser.add_option('-c', '--CC', help='extract CEA-608 captions to file, and turns on logging - => auto filename.', action="store", dest="cc", default="")
    parser.add_option('-V', '--video', help='display video details', action='store_true', default=False, dest='video')
    parser.add_option('-A', '--audio', help='display audio details', action='store_true', default=False, dest='audio')
    parser.add_option('-T', '--text', help='display text/metadata details', action='store_true', default=False, dest='text')
    parser.add_option('-s', '--silent', help='silent (suppress log printout)', action='store_true', default=False, dest='silent')
    parser.add_option('-p', '--packets', help='max nr TS packets to parse [default: %default]', action='store', default=-1, dest='max_nr_packets')

    # parse and validate options
    (opts, args) = parser.parse_args()

    obs = None
    options = {}
    log_cc = False
    if scc:
        options['cc'] = opts.cc
        if opts.cc == "-":
            options['cc'] = args[0].split(".")[0]
        log_cc = options['cc']
        if opts.log_cc:
            log_cc = True

    options['video'] = opts.video
    options['audio'] = opts.audio
    options['text'] = opts.text
    options['verbose'] = opts.verbose
    max_nr_packets = int(opts.max_nr_packets)

    if max_nr_packets > 0:
        nr_bytes_to_read = 188*max_nr_packets
    else:
        nr_bytes_to_read = -1

    if opts.observer == 'parser':
        obs = parser_observer(options)
    else:
        obs = key_frame_observer()
    importer = ts_importer(obs, options, log_cc)

    logger.silent = opts.silent

    # File/HTTP
    if len(args) == 1:
        uri = args[0]
        data = None
        if uri.find('http') == 0:
            handle_http(uri, importer)
            importer.report()
        else:
            handle_file(uri, nr_bytes_to_read, importer)
            importer.report()

    # Socket
    elif len(args) >= 2:
        host = args[0]
        port = args[1]
        data_file = None
        if len(args) == 3:
            data_file = args[2]
            obs.data_file = data_file
        handle_udp(host, port, importer)
        importer.report()

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        print e

