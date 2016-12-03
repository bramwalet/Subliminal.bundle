#!/usr/bin/env python
# flake8: noqa

"""
MP4 box parser
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


#pylint: disable=missing-docstring
#pylint: disable=invalid-name
#pylint: disable=expression-not-assigned
#pylint: disable=unused-variable

import base64
import binascii
import sys
import ts
import mp4

from Crypto.Cipher import AES
from Crypto.Util import Counter

SENC_GUID = 'A2394F525A9B4f14A2446C427C648DF4'


def decrypt_ctr(encrypted, key, iv):
    ctr = Counter.new(128, initial_value=long(iv.encode("hex"), 16))
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)
    return aes.decrypt(encrypted)


def decrypt_cbc(encrypted, key, iv):
    aes = AES.new(key, AES.MODE_CBC, iv)
    length = len(encrypted) - (len(encrypted) % 16)
    print 'length=', length, length % 16
    return aes.decrypt(encrypted[0:length])


def main():
    segment_file = sys.argv[1]
    
    key = None
    if len(sys.argv) == 3:
        key = binascii.unhexlify(sys.argv[2])

    with open(segment_file, 'rb') as f:
        segment = f.read()

    root = mp4.mp4(segment)
    print root.description()

    # Parse some boxes
    moof = root.find('moof')
    traf = moof.find('traf')
    tfdt = traf.find('tfdt')
    trun = traf.find('trun')
    nr_samples = trun.sample_count
    sample_info = [trun.sample_entry(i) for i in range(nr_samples)]
    sample_offset = moof.offset + trun.data_offset
    
    # Get IVs
    ivs = []
    sub_sample_vec = []
    uuids = traf.find_all('uuid')
    for uuid in uuids:
        if uuid.extended_type == binascii.unhexlify(SENC_GUID):
            data = uuid.fmap[uuid.offset+28:uuid.offset+uuid.size]
            senc = mp4.sampleEncryption_box(data, uuid.version, uuid.flags, iv_size=8)
            senc.decoration # Needed to set the 
            ivs = senc.ivs
            sub_sample_vec = senc.sub_sample_vec

    # Loop over samples
    cnt = 0
    for sample in sample_info:
        size = sample['size']
        sample_data = segment[sample_offset:sample_offset + size]
        
        # Decrypt if encrytped
        if ivs:
            iv = ivs[cnt]

            iv16 = binascii.unhexlify(iv) + '\x00\x00\x00\x00\x00\x00\x00\x00'
            print 'key_len=', len(key), ', iv_len=', len(iv16)
            print 'key=', binascii.hexlify(key), 'iv=', binascii.hexlify(iv16)

            if sub_sample_vec:
                # Sub-sample encryption (H264) - NOTE: some manual work needed.
                sub_samples = sub_sample_vec[cnt]
                pos = 0
                for sub_sample in sub_samples:
                    clear = sub_sample[0]
                    encrypted = sub_sample[1]
                    pos += clear
                    print 'clear=', clear, 'encrypted=', encrypted
                    decrypted_part = decrypt_ctr(sample_data[pos:pos+encrypted], key, iv16)
                    sample_data_2 = sample_data[0:pos]
                    sample_data_2 += decrypted_part
                    sample_data_2 += sample_data[pos+encrypted:]
                    sample_data = sample_data_2
                    pos += encrypted
            else:
                # Full sample encryption (AAC)
                decrypted = decrypt_ctr(sample_data, key, iv16)
                #decrypted = decrypt_cbc(sample_data, key, iv16)
                sample_data = decrypted
        
        # Display sample data
        print ''
        print 'sample size:', len(sample_data)
        print ts.dump_hex(sample_data, 16);
       
        sample_offset += size
        cnt += 1


if __name__ == '__main__':
    main()
