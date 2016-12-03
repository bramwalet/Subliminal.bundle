"""Routines for parsing and analyzing CEA-708 data."""

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

import ts
import scc

def log(msg):
    pass
    #print "Log: %s" % msg
        
class Cea708Parser(object):
    "Simple CEA-708 Closed Captioning parser, which simply gather info."
    
    def __init__(self):
        self.data_sorter = scc.DataSorter()
        self.dtvcc_data = ""
        self.dtvcc_size = 0
        self.pts_offset = None
        self.last_pts = None
        self.counters = {'padding' : 0, 'ctrl' : 0, 'char' : 0, 'cmd' : 0, 'latin' : 0}
    
    def get_cc_summary(self):
        "Get statistics about the CEA-708 data."
        total_count = 0
        for k in self.counters:
            total_count += self.counters[k]
        if total_count > 0:
            data = self.counters.copy()
            if self.pts_offset and self.last_pts > self.pts_offset:
                duration = (self.last_pts - self.pts_offset)/90000.0
                data['bitrate'] = int(total_count * 16 / duration)
            else:
                data['bitrate'] = 0
            return {'std' : "CEA-708", 'data' : data}
            
        else:
            return None

    def add_data(self, bytes, cc_type, pts_time):
        "Add a pair of bytes for a given pts_time."
        self.data_sorter.add_data(pts_time, (cc_type, bytes))
        self.process_data()
    
    def count_padding(self):
        "Count cc_valid == 0 (padding)"
        self.counters['padding'] += 1
        
    def process_data(self):
        data_list = self.data_sorter.retrieve_data(5)

        for data_line in data_list:
            pts_time, data = data_line
            if self.pts_offset is None:
                self.pts_offset = pts_time
            self.last_pts = pts_time
            for d in data:
                cc_type, bytes = d
                self.count(bytes[0])
                self.count(bytes[1])
                if cc_type == 3:
                    self.process_start_of_block(bytes)
                elif cc_type == 2:
                    self.process_bytes_in_block(bytes)
    
    def process_start_of_block(self, bytes):
        "Process the two bytes that start a block."
        a, b = bytes
        sequence_number = (a >> 6) & 0x3
        packet_size = a & 0x3f
        if packet_size == 0:
            self.dtvcc_size = 127
        else:
            self.dtvcc_size = 2 * packet_size - 1
        #self.counters['blocks'] += 1
        #self.counters['block_size'] += self.dtvcc_size
        self.dtvcc_data = chr(b)
            
    def process_bytes_in_block(self, bytes):
        "Process two bytes in a block."
        a, b = bytes
        self.dtvcc_data += chr(a)
        self.dtvcc_data += chr(b)
        if len(self.dtvcc_data) == self.dtvcc_size:
            self.parse_service_block(self.dtvcc_data)
    
    def count(self, byte):
        "Count the byte in the right bin."
        if byte < 0x20:
            self.counters['ctrl'] += 1
        elif byte < 0x80:
            self.counters['char'] += 1
        elif byte < 0xA0:
            self.counters['cmd'] += 1
        else:
            self.counters['latin'] += 1
    
    def parse_service_block(self, data, display=False):
        reader = ts.bitreader(data)
        service_number = ts.read_bits(reader, 3, '      service_number', display=display)
        block_size = ts.read_bits(reader, 5, '      block_size', display=display)
        if service_number == 0x7 and block_size != 0:
            ts.read_bits(reader, 2, '      null_fill', display=display)
            service_number = read_bits(reader, 6, '      extended_service_number', display=display)
        if service_number != 0:
            bytes_read = 0
            msg = ""
            for i in range(0, block_size):
                byte = ts.read_bits(reader, 8, '        block_data', display=False, to_hex=True)
                if byte < 0x20:
                    pass
                    #c = C0[byte]
                    #log(">> C0 = %02x" % byte)
                elif byte < 0x80:
                    msg += chr(byte) # G0[byte-32]
                    #log(">> text = %s" % chr(byte))
                elif byte < 0xA0:
                    pass
                    #log(">> C1 %02x" % byte)
                else:
                    pass
                    #log(">> G1 %02x" % byte)
            log("[CEA-708-TEXT] %s" % msg)
                    
