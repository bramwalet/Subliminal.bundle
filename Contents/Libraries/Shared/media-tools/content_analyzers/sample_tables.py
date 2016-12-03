"""
Utility file to handle sample table boxes in MP4 files
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

import mp4

def sample_to_chunk_and_index(stsc, idx):
    #print 'idx=', idx
    if stsc.array:
        result = stsc.get_unrolled(idx)
        #print result[0], result[1]
        return result
    
    delta = 0
    start_sample = 1
    count = 0
    for j in range(stsc.entry_count - 1):
        if j + 1 == stsc.entry_count:
            delta = 0
            break
        else:
            delta = (stsc.entry(j + 1)['first_chunk'] - stsc.entry(j)['first_chunk']) * stsc.entry(j)['samples_per_chunk']
        if idx >= start_sample and idx < start_sample + delta:
            break
        else:
            start_sample += delta
        count += 1
    
    chunk = stsc.entry(count)['first_chunk'] + (idx - start_sample) / stsc.entry(count)['samples_per_chunk']
    index = (idx - start_sample) % stsc.entry(count)['samples_per_chunk']
    #print chunk, index
    return chunk, index
    
def chunk_offset(stco, chunk):
    if 0 == chunk or stco.entry_count < chunk:
        return 0
    return stco.entry(chunk - 1)['chunk_offset']

def sample_size(stsz, idx):
    if stsz.sample_size:
        return stsz.sample_size
    elif idx and idx <= stsz.sample_count:
        return stsz.entry(idx - 1)['entry_size']
    return 0

def sample_time(stts, idx):
    if stts.array:
        return stts.array[idx]['time'], stts.array[idx]['delta']
    
    time = 0
    duration = 0
    last_sample = 0
    for i in range(stts.entry_count):
        duration = stts.entry(i)['sample_delta']
        if idx <= last_sample + stts.entry(i)['sample_count']: 
            time += (idx - last_sample - 1) * duration
            last_sample += stts.entry(i)['sample_count']
            return time, duration
        else:
            time += stts.entry(i)['sample_count'] * duration
            last_sample += stts.entry(i)['sample_count']
    return 0, 0

def sample_offset(ctts, idx):
    if not ctts:
        return 0
    if ctts.array:
        return ctts.array[idx]
    
    offset = 0
    last_sample = 0
    for i in range(ctts.entry_count):
        offset = ctts.entry(i)['sample_offset']
        if idx <= last_sample + ctts.entry(i)['sample_count']: 
            last_sample += ctts.entry(i)['sample_count']
            return offset
        else:
            last_sample += ctts.entry(i)['sample_count']
    return 0

def offset_from_sample(stbl, idx):
    chunk, index = sample_to_chunk_and_index(stbl.find('stsc'), idx)
    offset = chunk_offset(stbl.find('stco'), chunk)
    #print 'chunk:', chunk, 'index:', index, 'offset:', offset
    for i in range(idx - index, idx):
        d = sample_size(stbl.find('stsz'), i)
        offset += d
    return offset
