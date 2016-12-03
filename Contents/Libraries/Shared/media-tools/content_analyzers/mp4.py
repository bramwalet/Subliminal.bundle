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
import bisect
import functools

import struct
from struct import unpack

VERBOSE = 0
REGISTERED_BOXES = {}

FILTER = ''.join([(len(repr(chr(character))) == 3) and chr(character) or '.' for character in range(256)])


def str_to_uint32(string4):
    "4-character string to unsigned int32."
    return unpack(">I", string4)[0]


def dump_hex(src, length=8):
    """ dump_hex """
    result = []
    for i in xrange(0, len(src), length):
        row = src[i:i+length]
        hexa = ' '.join(["%02X" % ord(row_char) for row_char in row])
        printable = row.translate(FILTER)
        result.append("%04X   %-*s   %s\n" % (i, length * 3, hexa, printable))
    return ''.join(result)


def parse_generator(data, fmt=''):
    """ parse_generator """
    offset = 0
    ret = None
    while offset < len(data):
        if fmt:
            ret = struct.unpack_from(fmt, data, offset)
            offset += struct.calcsize(fmt)
        fmt = (yield ret) or fmt


def match_attribute(obj, crit):
    """ match_attribute """
    key, value = crit.split('=')
    obj_value = getattr(obj, key)
    # print(' - - testing %s == %s' % (str(value), str(obj_value)))
    return str(obj_value) == value


def match_box(obj, criteria='xxxx'):
    """ match_box """
    # print('match_box(%s, %s)' % (obj.path, criteria))
    if len(criteria) == 4:
        return obj.type == criteria
    elif criteria.find('[') != -1:
        # assume 'atom[attr=val]' notation
        return obj.type == criteria[:4] and match_attribute(obj, criteria[5:-1])


class box(object):
    def __init__(self, fmap, box_type, size, offset, parent=None):
        self.fmap = fmap
        self.type = box_type
        self.size = size
        self.offset = offset
        # self.size, self.type = struct.unpack('>i4s', fmap[offset:offset+8])
        self.children = []
        self.parent = parent
        if VERBOSE > 2:
            print ' - parsed \'%s\' offset:%d size:%d' % (box_type, offset, size)

    @property
    def endpos(self):
        return self.offset + self.size

    @property
    def childpos(self):
        return self.offset + 8

    @property
    def is_container(self):
        return self.type in ['root',
                             'moov',
                             'moof',
                             'trak',
                             'traf',
                             'tfad',
                             'mvex',
                             'mdia',
                             'minf',
                             'dinf',
                             'stbl',
                             'mfra',
                             'udta',
                             #'meta',
                             'stsd',
                             'sinf',
                             'schi',
                             'encv',
                             'enca',
                             'avc1',
                             'hev1',
                             'hvc1',
                             'mp4a',
                             'ec_3',
                             'vttc'] or self.__class__ == mp4

    @property
    def is_unparsed(self):
        return self.is_container and not self.children and self.size >= 16

    @property
    def root(self):
        root = self
        while root.parent:
            root = root.parent
        return root

    @property
    def path(self):
        if self.parent:
            path = '.'.join((self.parent.path, self.type))
        else:
            path = ''

        if path.startswith('.'):
            path = path[1:]

        return path

    def find_all(self, path):
        return self.find(path, return_first=False)

    def find(self, path, return_first=True):
        # print('%s Searching for: %s\n' % (str(self), path))
        queue = [(self, path.split('.'))]
        matches = []
        while queue:
            obj, parts = queue.pop(0)
            # print('testing %s[%d:%d]' % (obj.path, obj.offset, obj.endpos))
            # check if children are parsed
            if obj.is_unparsed:
                # print(' - parsing children')
                obj.parse_children(recurse=False)

            # matching child?
            if parts[0]:
                matching_children = filter(functools.partial(match_box, criteria=parts[0]), obj.children)
            else:
                matching_children = [obj.parent]

            if matching_children:
                # print('found %d matching children' % (len(matching_children)))
                if len(parts) == 1:
                    matches += matching_children

                    if return_first:
                        return matches[0]
                else:
                    new_items = [(child, parts[1:]) for child in matching_children]
                    queue = new_items + queue
                    # for child in matching_children:
                    #     queue.append((child, parts[1:]))

        # print(' = matches [%s]' % (', '.join([obj.path for obj in matches])))
        return matches

    def parse_children(self, stops=None, recurse=True):
        if not self.is_container:
            return

        if not stops:
            stops = []

        next_offset = self.childpos
        end_offset = self.offset + self.size

        while True:
            box_class = box
            size, box_type = struct.unpack('>i4s', self.fmap[next_offset:next_offset+8])

            #print 'type=', box_type, 'len=', size

            # Need to set allowed characters for some boxes
            if box_type == 'ac-3':
                box_type = 'ac_3'
            elif box_type == 'ec-3':
                box_type = 'ec_3'

            if size == 1:   # Extended size
                size = struct.unpack('>Q', self.fmap[next_offset+8:next_offset+16])[0]
            if size > self.size or size < 8:
                print 'WARNING: Box \'%s\' in \'%s\' at offset %d has faulty size %d (> %d or < 8)' % \
                    (box_type, self.path, next_offset, size, self.size - 7)
                #raise Exception
                return

            box_class_name = '%s_box' % box_type.replace(' ', '_')
            if box_class_name in REGISTERED_BOXES.keys():
                box_class = REGISTERED_BOXES[box_class_name]
                # debug_msg_exit('%s_box' % box_type + ':' + globals()['%s_box' % box_type].__name__)
            else:
                #print 'no box:', box_class_name
                pass

            new_box = box_class(self.fmap, box_type, size, next_offset, self)
            self.children += [new_box]
            #next_offset = new_box.endpos
            next_offset += size

            if recurse and new_box.is_container:
                new_box.parse_children(stops, recurse)

            for stop in stops:
                # print 'Testing box.type == "moov": %s (%s)' % (str(stop(new_box)), new_box.type)
                if stop(new_box):
                    return

            if next_offset >= end_offset:
                break

    def description(self):
        ret = '\'%s\' [%d:%d] %s\n' % (self.type, self.offset, self.size, \
            hasattr(self, 'decoration') and self.decoration or '')
        for child in self.children:
            ret += ' - ' + child.description().replace('\n', '\n - ')[:-3]
        return ret

    def __str__(self):
        old = object.__str__(self)
        return old.replace('object at', '\'%s\' [%d:%d] object at' % (self.path, self.offset, self.size))


class full_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)
        if self.type == 'uuid':
            self.extended_type = self.fmap[self.offset+8:self.offset+24]
            self.version = struct.unpack('B', self.fmap[self.offset+24:self.offset+25])[0]
            self.flags = struct.unpack('>i', '\x00'+self.fmap[self.offset+25:self.offset+28])[0]
        else:
            self.version = struct.unpack('B', self.fmap[self.offset+8:self.offset+9])[0]
            self.flags = struct.unpack('>i', '\x00'+self.fmap[self.offset+9:self.offset+12])[0]

    def description(self):
        return '\'%s\' [%d:%d] ver:%d flags:0x%x %s\n' % \
            (self.type, self.offset, self.size, self.version, self.flags, \
            hasattr(self, 'decoration') and self.decoration or '')


class bridged_box(object):
    def __init__(self, start, end):
        assert start.fmap == end.fmap

        self.start = start
        self.end = end
        self.fmap = start.fmap
        self.offset = start.offset
        self.size = end.offset + end.size - start.offset
        self.type = '%s->%s' % (start.type, end.type)


class mp4(box):
    def __init__(self, fmap, size=0, stops=None, recurse=True, offset=0, key=None, encrypted=False):
        self.key = key
        self.encrypted = encrypted

        if not stops:
            stops = []

        if not size:
            size = len(fmap)
        box.__init__(self, fmap, 'root', size, offset)
        if recurse:
            self.parse_children(stops=stops, recurse=recurse)

    def get_video_info(self):
        box_ = self.find('moov.trak.mdia.minf.vmhd')
        if not box_:
            return None, 0
        timescale = box_.parent.parent.find('mdhd').timescale
        track = box_.parent.parent.parent.find('tkhd').track_id
        return track, timescale

    def get_audio_info(self):
        box_ = self.find('moov.trak.mdia.minf.smhd')
        if not box:
            return None, 0
        timescale = box_.parent.parent.find('mdhd').timescale
        track = box_.parent.parent.parent.find('tkhd').track_id
        return track, timescale

    def get_timed_text_info(self):
        box_ = self.find('moov.trak.mdia.minf.nmhd')
        if not box:
            return None, 0
        timescale = box_.parent.parent.find('mdhd').timescale
        track = box_.parent.parent.parent.find('tkhd').track_id
        return track, timescale

    @property
    def childpos(self):
        return self.offset


class moov_box(box):
    def __init__(self, fmap, box_type, size, offset, parent=None):
        box.__init__(self, fmap, box_type, size, offset, parent)


class mvhd_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.creation_time = i.send(self.version and '>Q' or '>I')[0]
        self.modification_time = i.send(self.version and '>Q' or '>I')[0]
        self.timescale = i.send('>I')[0]
        self.duration = i.send(self.version and '>Q' or '>I')[0]
        self.decoration = 'tscale:%d dur:%.3f creation=%s modification=%s' % \
            (self.timescale, self.duration / float(self.timescale), self.creation_time, self.modification_time)


class pssh_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        #print dump_hex(self.fmap[self.offset+32:self.offset+self.size-32])

        self.system_id = ''.join(["%02X" % ord(x) for x in self.fmap[self.offset+12:self.offset+28]])
        o = 28

        self.kids = []
        if self.version > 0:
            KID_count = struct.unpack('>I', self.fmap[self.offset+o:self.offset+o+4])[0]
            o += 4
            for k in range(KID_count):
                kid = ''.join(["%02X"%ord(x) for x in self.fmap[self.offset+o:self.offset+o+16]])
                o += 16
                self.kids.append(kid)

        self.data_size = struct.unpack('>I', self.fmap[self.offset+o:self.offset+o+4])[0]
        o += 4

    @property
    def decoration(self):
        return 'sys_id:{0} kids:{1} size:{2}'.format(str(self.system_id), \
            ','.join(kid for kid in self.kids), self.data_size)

    def description(self):
        ret = full_box.description(self)
        for child in self.children:
            ret += ' - ' + child.description().replace('\n', '\n - ')[:-3]
        return ret

    # NOTE: Uncomment this code if PSSH should be parsed as a box container
    @property
    def childpos(self):
        return self.offset+32


class saiz_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)

    @property
    def default_sample_info_size(self):
        offset = 12
        if self.flags and 1:
            offset += 8

        return struct.unpack('>B', self.fmap[self.offset+offset:self.offset+offset+1])[0]

    @property
    def sample_count(self):
        offset = 13
        if self.flags and 1:
            offset += 8

        return struct.unpack('>I', self.fmap[self.offset+offset:self.offset+offset+4])[0]

    def sample_info_size(self, index):
        if self.default_sample_info_size != 0:
            return self.default_sample_info_size

        info_offset_base = 17
        if self.flags and 1:
            info_offset_base += 8

        sample_offset = self.offset + info_offset_base + index

        return struct.unpack('>B', self.fmap[sample_offset:sample_offset+1])[0]

    @property
    def decoration(self):
        base = '#samples: {0} default size: {1}'.format(self.sample_count, self.default_sample_info_size)
        entries = ['\n']

        if VERBOSE > 1:
            if self.default_sample_info_size == 0:
                for i in range(self.sample_count):
                    sample_info_size = self.sample_info_size(i)
                    entries.append(' - #{index:03d} sample info size:{0:3d}\n'.format(sample_info_size, index=i))

        return base + ''.join(entries)[:-1]


class saio_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

    @property
    def entry_count(self):
        offset = 12
        if self.flags and 1:
            offset += 8

        return struct.unpack('>I', self.fmap[self.offset+offset:self.offset+offset+4])[0]

    def entry_offset(self, index):
        offset = 16
        if self.flags and 1:
            offset += 8
            offset += index * 8
            return struct.unpack('>Q', self.fmap[self.offset+offset:self.offset+offset+8])[0]
        else:
            offset += index * 4
            return struct.unpack('>I', self.fmap[self.offset+offset:self.offset+offset+4])[0]

    @property
    def decoration(self):
        base = '#entries: {0}'.format(self.entry_count)
        entries = ['\n']

        if VERBOSE > 1:
            for i in range(self.entry_count):
                offset = self.entry_offset(i)
                entries.append(' - #{0:03d} offset:{1:d}\n'.format(i, offset))

        return base + ''.join(entries)[:-1]


class sbgp_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        #print 'sbgp'
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

    @property
    def grouping_type(self):
        return self.fmap[self.offset+12:self.offset+16]

    @property
    def entries(self):
        return struct.unpack('>I', self.fmap[self.offset+16:self.offset+20])[0]

    def group_entry(self, index):
        base_offset = 20 + (self.version and 4 or 0)
        entry_offset = base_offset + 8 * index
        if entry_offset > self.size:
            return 0, 0

        offset = self.offset + entry_offset
        sample_count = struct.unpack('>I', self.fmap[offset:offset+4])[0]
        group_description_index = struct.unpack('>I', self.fmap[offset+4:offset+8])[0]

        return sample_count, group_description_index

    @property
    def decoration(self):
        base = 'grouping:%s #entries:%d' % (self.grouping_type, self.entries)
        entries = ['\n']

        if VERBOSE > 1:
            for i in range(self.entries):
                data = self.group_entry(i)
                entries.append(' - #{index:03d} sample count:{0:3d} group descr index:{1:3d}\n'.format(*data, index=i))

        return base + ''.join(entries)[:-1]


class sgpd_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        #print 'sgpd'
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

    @property
    def grouping_type(self):
        return self.fmap[self.offset+12:self.offset+16]

    @property
    def entries(self):
        o = (self.version and 4 or 0)
        return struct.unpack('>I', self.fmap[self.offset+o+16:self.offset+o+20])[0]

    def entry(self, index):
        base_offset = 20 + (self.version and 4 or 0)
        entry_offset = base_offset + 20 * index
        if entry_offset > self.size:
            return 0, 0, ''

        offset = self.offset + entry_offset

        is_encrypted = struct.unpack('>i', '\x00'+self.fmap[offset:offset+3])[0]
        iv_size = struct.unpack('>b', self.fmap[offset+3:offset+4])[0]

        kid = self.fmap[offset+4:offset+20]

        return is_encrypted, iv_size, kid

    def entry_data(self, index):
        base_offset = 20 + (self.version and 4 or 0)
        entry_offset = base_offset + 20 * index
        if entry_offset > self.size:
            return ''

        offset = self.offset + entry_offset
        return self.fmap[offset:offset+20]

    @property
    def decoration(self):
        base = 'grouping:%s #entries:%d' % (self.grouping_type, self.entries)
        entries = ['\n']

        if VERBOSE > 1:
            for i in range(self.entries):
                is_enc, iv_size, kid = self.entry(i)
                entry = ' - #{0:03d} enc:{1}'.format(i, is_enc)
                if is_enc != 0:
                    entry = entry + ' iv size:{0} kid:{1}'.format(iv_size, ''.join(["%02X"%ord(x) for x in kid]))
                entries.append(entry + '\n')

        return base + ''.join(entries)[:-1]


class senc_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.sample_count = i.send('>I')[0]
        self.samples = []
        def_iv_size = 8
        for j in range(0, self.sample_count):
            iv = i.send('>Q')[0]
            iv_2 = hex(iv)
            self.samples.append(iv_2)

            # TODO: subsamples

    @property
    def decoration(self):
        base = '#samples: {0}'.format(self.sample_count)
        entries = ['\n']

        if VERBOSE > 1:
            for i in range(self.sample_count):
                sample = self.samples[i]
                entries.append(' - #{index:03d} iv:{0}\n'.format(sample, index=i))
        return base + ''.join(entries)[:-1]


class genc_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        self._sample_map = {}
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

    def _init_sample_map_from_sbgp(self, tenc):
        sbgp = self.get_sibling('sbgp')
        if not sbgp:
            return
        sgpd = self.get_sibling('sgpd')

        entry_index = 0
        for i in range(sbgp.entries):
            count, group_index = sbgp.group_entry(i)
            if group_index == 0:
                # No group. Use default tenc values
                enc = tenc.is_encrypted
                iv_size = tenc.iv_size
                kid = tenc.key_id
            else:
                # group defined. use values from sgpd
                enc, iv_size, kid = sgpd.entry(group_index-1)

            for sample_index in range(count):
                self._sample_map[entry_index + sample_index] = (enc, iv_size, kid)
            entry_index += count

    def _init_sample_map(self):
        self._sample_map = {}

        tfhd = self.get_sibling('tfhd')
        tenc = self.get_tenc_for_track_id(tfhd.track_id)

        self._init_sample_map_from_sbgp(tenc)

        saiz = self.get_sibling('saiz')

        #saio = self.get_sibling('saio')
        #moof = self.get_ancestor('moof')
        #sample_offset = moof.offset + saio.entry_offset(0)

        for i in range(saiz.sample_count):
            #sample_info_size = saiz.sample_info_size(i)
            if not i in self._sample_map:
                self._sample_map[i] = (tenc.is_encrypted, tenc.iv_size, tenc.key_id)
            #sample_offset += sample_info_size

    def sample_encrypted_info(self, index):
        if index in self._sample_map:
            is_enc, iv_size, kid = self._sample_map[index]
            return is_enc, iv_size, kid

        return (0, 0, '')

    def get_sibling(self, type_):
        box_list = self.parent.children
        #pindex = self.parent.children.index(self)
        # print('my index of parent: %d' % (pindex))
        for box_ in box_list:
            if box_.type == type_:
                return box_
        return None

    def get_ancestor(self, type_):
        p = self
        while p.parent:
            p = p.parent
            if p.type == type_:
                return p
        return None

    def get_tenc_for_track_id(self, track_id):
        trak_boxes = self.root.find_all('moov.trak')
        for box_ in trak_boxes:
            tkhd = box_.find('tkhd')
            if tkhd.track_id == track_id:
                return box_.find('mdia.minf.stbl.stsd.sinf.schi.tenc')
        return None

    @property
    def decoration(self):
        self._init_sample_map()
        saiz = self.get_sibling('saiz')
        saio = self.get_sibling('saio')
        tfhd = self.get_sibling('tfhd')
        #tenc = self.get_tenc_for_track_id(tfhd.track_id)
        moof = self.get_ancestor('moof')

        sample_offset = moof.offset + saio.entry_offset(0)

        base = ' #aux data: {0}'.format(saiz.sample_count)
        entries = ['\n']

        if VERBOSE > 1:
            for i in range(saiz.sample_count):
                sample_info_size = saiz.sample_info_size(i)
                #sample_data = self.fmap[sample_offset:sample_offset+sample_info_size]
                is_encrypted, iv_size, kid = self.sample_encrypted_info(i)
                entry = ' - index:{0:03d} enc: {1}'.format(i, is_encrypted)
                if is_encrypted != 0:
                    iv = self.fmap[sample_offset:sample_offset+iv_size]
                    entry = entry + ' iv:0x{0} kid:{1}'.format(''.join(["%02X"%ord(x) for x in iv]), \
                        ''.join(["%02X"%ord(x) for x in kid]))
                    if sample_info_size > iv_size:
                        a = sample_offset + iv_size
                        b = a + 2
                        sub_sample_count = struct.unpack('>h', self.fmap[a : b])[0]
                        entry = entry + ' #sub samples:{0}'.format(sub_sample_count)
                        for s in range(sub_sample_count):
                            sub_sample_offset = sample_offset+iv_size+2+s*6
                            off = sub_sample_offset
                            clear_data_size = struct.unpack('>H', self.fmap[off:off + 2])[0]
                            encrypted_data_size = struct.unpack('>I', self.fmap[off + 2 : off + 6])[0]
                            entry = entry + '\n - - sub sample:{0:03d} clear chunk:{1} encrypted chunk:{2}'\
                                .format(s, clear_data_size, encrypted_data_size)
                entries.append(entry + '\n')
                sample_offset += sample_info_size

        return base + ''.join(entries)[:-1]


class SampleEntry(box):
    def __init__(self, *args):
        box.__init__(self, *args)

    @property
    def data_reference_index(self):
        return struct.unpack('>H', self.fmap[self.offset+14:self.offset+16])[0]


def getDescriptorLen(i):
    tmp = i.send('>B')[0]
    len_ = 0
    while tmp & 0x80:
        len_ = ((len_ << 7) | (tmp & 0x7f))
        tmp = i.send('>B')[0]

    len_ = ((len_ << 7) | (tmp & 0x7f))

    return len_


class esds_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)

        self.cfg = ''

        i = parse_generator(self.fmap[self.offset+8:self.offset+self.size])
        i.next() # prime
        vf = i.send('>I')[0]
        tag1 = i.send('>B')[0]

        if tag1 == 3:
            l = getDescriptorLen(i)
            i.send('>B')[0]
            i.send('>B')[0]
            i.send('>B')[0]

            tag2 = i.send('>B')[0]

            if tag2 == 4:
                l = getDescriptorLen(i)

                obj_type = i.send('>B')[0]
                stream_type = i.send('>B')[0]

                i.send('>B')[0]
                i.send('>B')[0]

                i.send('>I')[0]
                i.send('>I')[0]
                i.send('>B')[0]

                tag3 = i.send('>B')[0]

                if tag3 == 5:

                    l = getDescriptorLen(i)
                    cfg = []
                    for p in range(0, l):
                        X = i.send('>B')[0]
                        cfg.append(X)

                    cfg_str = '0x' + ''.join(['%02x' % c for c in cfg])
                    self.cfg = cfg_str

                    self.decoration = 'cfg={0}, obj_type={1}, stream_type={2}'\
                        .format(cfg_str, obj_type, stream_type)


class mp4a_box(SampleEntry):
    def __init__(self, *args):
        SampleEntry.__init__(self, *args)
        self.channels = struct.unpack('>h', self.fmap[self.offset+24:self.offset+26])[0]
        self.sample_size = struct.unpack('>h', self.fmap[self.offset+26:self.offset+28])[0]
        self.sample_rate = struct.unpack('>I', self.fmap[self.offset+32:self.offset+36])[0] >> 16
        self.decoration = 'index:{0} channels:{1} sample size:{2} sample rate:{3}'\
            .format(self.data_reference_index, self.channels, self.sample_size, self.sample_rate)

    @property
    def childpos(self):
        return self.offset+36


class ac_3_box(SampleEntry):
    def __init__(self, *args):
        SampleEntry.__init__(self, *args)
        channels = struct.unpack('>h', self.fmap[self.offset+24:self.offset+26])[0]
        sample_size = struct.unpack('>h', self.fmap[self.offset+26:self.offset+28])[0]
        sample_rate = struct.unpack('>I', self.fmap[self.offset+32:self.offset+36])[0] >> 16
        self.decoration = 'index:{0} channels:{1} sample size:{2} sample rate:{3}'\
            .format(self.data_reference_index, channels, sample_size, sample_rate)

    @property
    def childpos(self):
        return self.offset+36


class ec_3_box(SampleEntry):
    def __init__(self, *args):
        SampleEntry.__init__(self, *args)
        channels = struct.unpack('>h', self.fmap[self.offset+24:self.offset+26])[0]
        sample_size = struct.unpack('>h', self.fmap[self.offset+26:self.offset+28])[0]
        sample_rate = struct.unpack('>I', self.fmap[self.offset+32:self.offset+36])[0] >> 16
        self.decoration = 'index:{0} channels:{1} sample size:{2} sample rate:{3}'\
            .format(self.data_reference_index, channels, sample_size, sample_rate)

    @property
    def childpos(self):
        return self.offset+36


class dac3_box(SampleEntry):
    def __init__(self, *args):
        SampleEntry.__init__(self, *args)
        self.dec_info = self.fmap[self.offset+8:self.offset+self.size]
        self.dec_info_hex = ''.join(['%02x' % ord(c) for c in self.dec_info])
        self.decoration = 'dec_info={0}'.format(self.dec_info_hex)


class dec3_box(SampleEntry):
    def __init__(self, *args):
        SampleEntry.__init__(self, *args)
        self.dec_info = self.fmap[self.offset+8:self.offset+self.size]
        self.dec_info_hex = ''.join(['%02x' % ord(c) for c in self.dec_info])
        self.decoration = 'dec_info={0}'.format(self.dec_info_hex)


class enca_box(mp4a_box):
    def __init__(self, *args):
        mp4a_box.__init__(self, *args)


class mp4v_box(SampleEntry):
    def __init__(self, *args):
        SampleEntry.__init__(self, *args)
        width = struct.unpack('>h', self.fmap[self.offset+32:self.offset+34])[0]
        height = struct.unpack('>h', self.fmap[self.offset+34:self.offset+36])[0]
        self.decoration = 'index:{0} width:{1} height:{2}'\
            .format(self.data_reference_index, width, height)


class avcx_box(SampleEntry):
    def __init__(self, *args):
        SampleEntry.__init__(self, *args)
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

        self.width = struct.unpack('>h', self.fmap[self.offset+32:self.offset+34])[0]
        self.height = struct.unpack('>h', self.fmap[self.offset+34:self.offset+36])[0]
        res_hori = struct.unpack('>I', self.fmap[self.offset+36:self.offset+40])[0]
        res_vert = struct.unpack('>I', self.fmap[self.offset+40:self.offset+44])[0]
        frame_count = struct.unpack('>h', self.fmap[self.offset+48:self.offset+50])[0]
        compressor = str(self.fmap[self.offset+50:self.offset+82])
        depth = struct.unpack('>h', self.fmap[self.offset+82:self.offset+84])[0]

        self.decoration = 'index:{0} width:{1} height:{2} hori_res:{3:x} vert_res:{4:x} compressor:{5} depth={6:x}'\
            .format(self.data_reference_index, self.width, self.height, res_hori, res_vert, compressor, depth)

    @property
    def childpos(self):
        return self.offset+86


class avc1_box(avcx_box):
    def __init__(self, *args):
        avcx_box.__init__(self, *args)


class avc3_box(avcx_box):
    def __init__(self, *args):
        avcx_box.__init__(self, *args)


class hev1_box(avcx_box):
    def __init__(self, *args):
        avcx_box.__init__(self, *args)


class hvc1_box(avcx_box):
    def __init__(self, *args):
        avcx_box.__init__(self, *args)

class encv_box(avc1_box):
    def __init__(self, *args):
        # look at format box to see which box to parse here
        #mp4v_box.__init__(self, *args)
        avc1_box.__init__(self, *args)
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])


class avcC_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+8:self.offset+self.size])
        i.next() # prime

        self.version = i.send('>B')[0]
        self.profile_ind = i.send('>B')[0]
        self.profile_compat = i.send('>B')[0]
        self.level = i.send('>B')[0]
        self.dummy1 = i.send('>B')[0]
        tmp1 = i.send('>B')[0]

        numSps = tmp1 & 0x1f
        sps_vec = []

        for j in range(0, numSps):
            spsSize = i.send('>H')[0]
            for k in range(0, spsSize):
                x = i.send('>B')[0]
                sps_vec.append(x)

        sps_bin_str = ''.join(['%02x' % c for c in sps_vec])
        spsb64 = base64.b64encode(binascii.a2b_hex(sps_bin_str))

        tmp2 = i.send('>B')[0]
        numPps = tmp2 & 0x1f
        pps_vec = []

        for j in range(0, numPps):
            ppsSize = i.send('>H')[0]
            for k in range(ppsSize):
                x = i.send('>B')[0]
                pps_vec.append(x)

        pps_bin_str = ''.join(['%02x' % c for c in pps_vec])
        ppsb64 = base64.b64encode(binascii.a2b_hex(pps_bin_str))

        self.decoration = 'profile={0}, {1}, level={2}, sps/pps:{3} {4}'\
            .format(self.profile_ind,
                    self.profile_compat,
                    self.level,
                    spsb64,
                    ppsb64)

        self.sps = sps_bin_str
        self.pps = pps_bin_str
        self.sps_bytes = sps_vec
        self.pps_bytes = pps_vec


def read_hex(reader, bytes):
    vec = []
    for i in range(bytes):
        vec.append(reader.send('>B')[0])
    hex_str = ''.join(['%02x' % c for c in vec])
    return hex_str


class hvcC_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+8:self.offset+self.size])
        i.next() # prime

        self.c = {}
        self.c['configuration_version'] = i.send('>B')[0]

        tmp = i.send('>B')[0]

        self.c['general_profile_space'] = (tmp >> 6) & 3
        self.c['general_tier_flag'] = (tmp >> 5) & 1
        self.c['general_profile_idc'] = tmp & 0x1f

        self.c['general_profile_compatibility_flags'] = read_hex(i, 4)
        self.c['general_constraint_indicator_flags'] = read_hex(i, 6)

        self.c['general_level_idc'] = i.send('>B')[0]

        tmp = i.send('>H')[0]
        self.c['min_spatial_segmentation_idc'] = tmp & 0xfff

        tmp = i.send('>B')[0]
        self.c['parallelismType'] = tmp & 0x3

        tmp = i.send('>B')[0]
        self.c['chromaFormat'] = tmp & 3

        tmp = i.send('>B')[0]
        self.c['bitDepthLumaMinus8'] = tmp & 7

        tmp = i.send('>B')[0]
        self.c['bitDepthChromaMinus8'] = tmp & 7

        self.c['avgFrameRate'] = i.send('>H')[0]

        tmp = i.send('>B')[0]

        self.c['constantFrameRate'] = (tmp >> 6) & 0x3
        self.c['numTemporalLayers'] = (tmp >> 3) & 0x7
        self.c['temporalIdNested'] = (tmp >> 2) & 0x1
        self.c['lengthSizeMinusOne'] = (tmp & 0x3)

        num_arrays = i.send('>B')[0]
        self.c['num_arrays'] = num_arrays
        self.c['array'] = []

        for j in range(num_arrays):
            tmp = i.send('>B')[0]
            a = {}
            a['array_completeness'] = (tmp >> 7) & 1
            a['NAL_unit_type'] = (tmp & 0x3f)
            a['NAL_units'] = []

            num_nal_units = i.send('>H')[0]
            for k in range(num_nal_units):
                nal_unit_length = i.send('>H')[0]
                nal_unit = read_hex(i, nal_unit_length)
                a['NAL_units'].append({'NAL_unit' : nal_unit})

            self.c['array'].append(a)

    def _print(self, x, indent):
        s = ''
        for k, v in x.iteritems():
            if type(v) == type([]):
                for i in v:
                    s += ''.ljust(indent) + k + ' size=' + str(len(v)) + '\n'
                    s += self._print(i, indent + 2)
            else:
                s = s + ''.ljust(indent) + '{0} = {1} \n'.format(k, v)
        return s

    @property
    def decoration(self):
        indent = 0
        try:
            return '\n' + self._print(self.c, indent)
        except Exception as e:
            return e


class stsd_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        self.decoration = '#entries:%d' % (self.entry_count)

    @property
    def entry_count(self):
        return struct.unpack('>I', self.fmap[self.offset+12:self.offset+16])[0]

    @property
    def childpos(self):
        return self.offset+16

    def description(self):
        ret = full_box.description(self)
        for child in self.children:
            ret += ' - ' + child.description().replace('\n', '\n - ')[:-3]
        return ret


class sinf_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)


class frma_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)
        self.decoration = 'data format:%s' % (self.fmap[self.offset + 8 : self.offset + 12])


class schm_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        type = self.fmap[self.offset+12:self.offset+16]
        major_version = struct.unpack('>H', self.fmap[self.offset+16:self.offset+18])[0]
        minor_version = struct.unpack('>H', self.fmap[self.offset+18:self.offset+20])[0]
        self.decoration = 'type:{0} version:{1}.{2}'.format(type, major_version, minor_version)


class schi_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)


class tenc_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)

    @property
    def is_encrypted(self):
        return struct.unpack('>i', '\x00'+self.fmap[self.offset+12:self.offset+15])[0]

    @property
    def iv_size(self):
        return struct.unpack('>b', self.fmap[self.offset+15:self.offset+16])[0]

    @property
    def key_id(self):
        return self.fmap[self.offset+16:self.offset+32]

    @property
    def decoration(self):
        if self.is_encrypted != 0:
            kid = ''.join(["%02X"%ord(x) for x in self.key_id])
            ret = 'enc:{0} iv size:{1}, kid:0x{2}'.format(self.is_encrypted, self.iv_size, kid)
        else:
            ret = 'enc:{0}'.format(self.is_encrypted)
        return ret


class tkhd_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.creation_time = i.send(self.version and '>Q' or '>I')[0]
        self.modification_time = i.send(self.version and '>Q' or '>I')[0]
        self._track_id = i.send('>I')[0]
        i.send('>I') # reserved
        self.duration = i.send(self.version and '>Q' or '>I')[0]

        for j in range(0, 13):
            # reserved, matrix etc
            i.send('>I')

        self.width = i.send('>I')[0] >> 16
        self.height = i.send('>I')[0] >> 16

        self.decoration = 'track_id:%d creation=%s modification=%s duration=%d width=%d height=%d' % \
            (self._track_id, self.creation_time, self.modification_time, self.duration, self.width, self.height)

    @property
    def track_id(self):
        return self._track_id


class mdhd_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.creation_time = i.send(self.version and '>Q' or '>I')[0]
        self.modification_time = i.send(self.version and '>Q' or '>I')[0]
        self.timescale = i.send('>I')[0]
        self.duration = i.send(self.version and '>Q' or '>I')[0]
        lang = i.send('>H')[0]
        lang_1 = ((lang >> 10) & 0x1f) + 0x60
        lang_2 = ((lang >> 5) & 0x1f) + 0x60
        lang_3 = (lang & 0x1f) + 0x60
        language = chr(lang_1) + chr(lang_2) + chr(lang_3)
        self.decoration = 'tscale:%d dur:%d (=%.3f sec) language=%s' % \
            (self.timescale,
             self.duration,
             self.duration / float(self.timescale),
             language)


class hdlr_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        i.send('>I')[0] # pre_defined
        handler_type = ''
        for k in range(4):
            handler_type += chr(i.send('>B')[0]) # handler_type
        i.send('>I')[0] # reserved
        i.send('>I')[0] # reserved
        i.send('>I')[0] # reserved

        rest = self.size - 12 - 5 * 4
        encoding_name = ''
        for k in range(rest-1):
            encoding_name += chr(i.send('>B')[0])

        self.decoration = 'type={0} name={1}'.format(handler_type, encoding_name)

        self.handler_type = handler_type
        self.encoding_name = encoding_name


class moof_box(box):
    def __init__(self, fmap, box_type, size, offset, parent=None):
        box.__init__(self, fmap, box_type, size, offset, parent)

    def get_mdat(self):
        box_list = self.parent.children
        pindex = self.parent.children.index(self)
        # print('my index of parent: %d' % (pindex))
        while pindex < len(box_list):
            box = box_list[pindex]
            if box.type == 'mdat':
                return box
            pindex += 1

        return None
        # mdat = [obj for obj in self.parent.children[pindex:] if obj.type == 'mdat']
        # return len(mdat) and mdat[0] or None


class trex_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size], '>I')
        self.track_id = i.next()[0]
        self.default_sample_description_index = i.next()[0]
        self.default_sample_duration = i.next()[0]
        self.default_sample_size = i.next()[0]
        self.default_sample_flags = i.next()[0]

        self.decoration = 'track_id:%d dur:%d' % (self.track_id, self.default_sample_duration)


class mfhd_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)
        self.seqno = struct.unpack('>i', self.fmap[self.offset+12:self.offset+16])[0]

    def get_track_duration(self, track_id, timescale):
        truns = self.find('.traf.tfhd[track_id=%d]..trun' % track_id, return_first=False)
        dur = sum([trun.total_duration for trun in truns])
        return dur / float(timescale)

    @property
    def video_duration(self):
        video_track, video_timescale = self.root.get_video_info()
        return self.get_track_duration(video_track, video_timescale)

    @property
    def audio_duration(self):
        audio_track, audio_timescale = self.root.get_audio_info()
        return self.get_track_duration(audio_track, audio_timescale)

    def get_track_sample_count(self, track_id):
        truns = self.find('.traf.tfhd[track_id=%d]..trun' % track_id, return_first=False)
        return sum([trun.sample_count for trun in truns])

    @property
    def video_sample_count(self):
        track, timescale = self.root.get_video_info()
        return self.get_track_sample_count(track)

    @property
    def audio_sample_count(self):
        track, timescale = self.root.get_audio_info()
        return self.get_track_sample_count(track)

    def description(self):
        self.decoration = 'seqno:%d' % (self.seqno)
        return box.description(self)


class tfhd_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)

        self.has_base_data_offset = self.flags & 0x0001
        self.has_sample_description_index = self.flags & 0x0002
        self.has_default_sample_duration = self.flags & 0x0008
        self.has_default_sample_size = self.flags & 0x0010
        self.has_default_sample_flags = self.flags & 0x0020

        self.base_data_offset = 0
        self.sample_description_index = 0
        self.default_sample_duration = 0
        self.default_sample_size = 0
        self.default_sample_flags = 0

        msg = 'track_id:%d' % self.track_id

        offset = 16

        if self.has_base_data_offset:
            self.base_data_offset = struct.unpack('>Q', self.fmap[self.offset + offset : self.offset + offset + 8])[0]
            msg = msg + ' base_data_offset:%d' % self.base_data_offset
            offset = offset + 8

        if self.has_sample_description_index:
            self.sample_description_index = \
                struct.unpack('>I', self.fmap[self.offset + offset : self.offset + offset + 4])[0]
            msg = msg + ' sample_description_index:%d' % self.sample_description_index
            offset = offset + 4

        if self.has_default_sample_duration:
            self.default_sample_duration = struct.unpack('>I', self.fmap[self.offset+offset:self.offset+offset+4])[0]
            msg = msg + ' default_sample_duration:%d' % self.default_sample_duration
            offset = offset + 4

        if self.has_default_sample_size:
            self.default_sample_size = struct.unpack('>I', self.fmap[self.offset+offset:self.offset+offset+4])[0]
            msg = msg + ' default_sample_size:%d' % self.default_sample_size
            offset = offset + 4

        if self.has_default_sample_flags:
            self.default_sample_flags = struct.unpack('>I', self.fmap[self.offset+offset:self.offset+offset+4])[0]
            msg = msg + ' default_sample_flags:%d' % self.default_sample_flags
            offset = offset + 4

        self.msg = msg

    @property
    def track_id(self):
        return struct.unpack('>I', self.fmap[self.offset+12:self.offset+16])[0]

    @property
    def decoration(self):
        return self.msg


class trun_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)

        self.has_data_offset = self.flags & 0x0001
        self.has_first_sample_flags = self.flags & 0x0004
        self.has_sample_duration = self.flags & 0x0100
        self.has_sample_size = self.flags & 0x0200
        self.has_sample_flags = self.flags & 0x0400
        self.has_sample_composition_time_offset = self.flags & 0x0800

        # self.sample_count = struct.unpack('>I', self.fmap[self.offset+12:self.offset+16])[0]
        self.data_offset = 0
        self.first_sample_flags = 0
        self.decoration = 'size:%d' % self.sample_count
        # self.decorators = {'size':self.sample_count}

        self.sample_array_offset = 16
        if self.has_data_offset:
            self.data_offset = struct.unpack('>i', \
                self.fmap[self.offset+self.sample_array_offset:self.offset + self.sample_array_offset + 4])[0]
            self.sample_array_offset += 4
            self.decoration += ' offset:%d' % self.data_offset

        if self.has_first_sample_flags:
            self.first_sample_flags = struct.unpack('>I', \
                self.fmap[self.offset+self.sample_array_offset:self.offset+self.sample_array_offset+4])[0]
            self.sample_array_offset += 4
            self.decoration += ' fs_flags:%d' % self.first_sample_flags

        self.sample_row_size = (self.has_sample_duration and 4) + \
            (self.has_sample_size and 4) + (self.has_sample_flags and 4) + \
            (self.has_sample_composition_time_offset and 4)
        if self.has_sample_duration:
            self.total_duration = sum([struct.unpack_from('>I', self.fmap, self.offset + self.sample_array_offset + i * self.sample_row_size)[0] for i in range(self.sample_count)])
        else:
            self.total_duration = self.parent.find('tfhd').default_sample_duration * self.sample_count

        self.decoration += ' tdur:%d' % self.total_duration

    #@property
    #def has_data_offset(self):
    #    return self.flags & 0x0001

    #@property
    #def data_offset(self):
    #    return struct.unpack('>i', \
    #        self.fmap[self.offset+self.sample_array_offset:self.offset+self.sample_array_offset+4])[0]

    @property
    def sample_count(self):
        return struct.unpack('>I', self.fmap[self.offset+12:self.offset+16])[0]

    def sample_entry(self, i):
        row = {}
        offset = self.offset + self.sample_array_offset + i * self.sample_row_size
        if self.has_sample_duration:
            row['duration'] = struct.unpack('>I', self.fmap[offset:offset+4])[0]
            offset += 4
        if self.has_sample_size:
            row['size'] = struct.unpack('>I', self.fmap[offset:offset+4])[0]
            offset += 4
        if self.has_sample_flags:
            row['flags'] = '0x%x' % struct.unpack('>I', self.fmap[offset:offset+4])[0]
            offset += 4
        if self.has_sample_composition_time_offset:
            row['time_offset'] = struct.unpack('>I', self.fmap[offset:offset+4])[0]
            offset += 4

        return row

    def description(self):
        root = self
        while root.parent:
            root = root.parent

        current_track_id = self.parent.find('tfhd').track_id

        # track_id, timescale = root.get_video_info()
        # if track_id != current_track_id:
        #     track_id, timescale = root.get_audio_info()
        #
        # self.decoration += ' tdur:%f' % (self.total_duration / float(timescale))

        ret = full_box.description(self)

        if VERBOSE > 1:
            for i in range(self.sample_count):
                row = {}
                offset = self.offset + self.sample_array_offset + i * self.sample_row_size
                if self.has_sample_duration:
                    row['duration'] = struct.unpack('>I', self.fmap[offset:offset+4])[0]
                    offset += 4
                if self.has_sample_size:
                    row['size'] = struct.unpack('>I', self.fmap[offset:offset+4])[0]
                    offset += 4
                if self.has_sample_flags:
                    row['flags'] = '0x%x' % struct.unpack('>I', self.fmap[offset:offset+4])[0]
                    offset += 4
                if self.has_sample_composition_time_offset:
                    row['time_offset'] = struct.unpack('>I', self.fmap[offset:offset+4])[0]
                    offset += 4

                ret += ' - ' + ' '.join(['%s:%s' % (k, v) for k, v in row.iteritems()]) + '\n'

        return ret


class tfra_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        self.random_access_time = []
        self.random_access_moof_offset = []

    @property
    def track_id(self):
        return struct.unpack('>I', self.fmap[self.offset+12:self.offset+16])[0]

    @property
    def length_size_of_traf_num(self):
        return (struct.unpack('>B', self.fmap[self.offset+19])[0] & 0x30) >> 4

    @property
    def length_size_of_trun_num(self):
        return (struct.unpack('>B', self.fmap[self.offset+19])[0] & 0x0C) >> 2

    @property
    def length_size_of_sample_num(self):
        return struct.unpack('>B', self.fmap[self.offset+19])[0] & 0x03

    @property
    def number_of_entry(self):
        return struct.unpack('>I', self.fmap[self.offset+20:self.offset+24])[0]

    @property
    def end_time(self):
        if self.number_of_entry == 0:
            return 0

        # This is an approx. Assumes a full GOP.
        last_keyframe_time = self.entry(self.number_of_entry - 1)[0]
        prev_keyframe_time = self.entry(self.number_of_entry - 2)[0]
        return last_keyframe_time + (last_keyframe_time - prev_keyframe_time)

    def entry(self, index):
        intro_format, intro_length = self.version and ('>Q', 16) or ('>I', 8)
        row_length = (intro_length +
                      1 + self.length_size_of_traf_num +
                      1 + self.length_size_of_trun_num +
                      1 + self.length_size_of_sample_num)
        row_start = self.offset + 24 + (row_length * index)

        # sys.stderr.write(str(locals())+'\n')
        # sys.stderr.write('start:{row_start} len:{row_length}\n'.format(**locals()))

        p = parse_generator(self.fmap[row_start:row_start+row_length], intro_format)
        time = p.next()[0]
        moof_offset = p.next()[0]
        traf = p.send(['>B', '>H', '>BH', '>I'][self.length_size_of_traf_num])[-1]
        trun = p.send(['>B', '>H', '>BH', '>I'][self.length_size_of_trun_num])[-1]
        sample = p.send(['>B', '>H', '>BH', '>I'][self.length_size_of_sample_num])[-1]

        return time, moof_offset, traf, trun, sample

    def parse_random_access_table(self):
        intro_format, intro_length = self.version and ('>QQ', 16) or ('>II', 8)
        row_length = (intro_length +
                      1 + self.length_size_of_traf_num +
                      1 + self.length_size_of_trun_num +
                      1 + self.length_size_of_sample_num)

        self.random_access_time = []
        self.random_access_moof_offset = []
        for i in range(self.number_of_entry):
            row_start = self.offset + 24 + (row_length * i)
            time, moof_offset = struct.unpack(intro_format, self.fmap[row_start:row_start+intro_length])

            if not self.random_access_moof_offset or self.random_access_moof_offset[-1] != moof_offset:
                self.random_access_time.append(time)
                self.random_access_moof_offset.append(moof_offset)

    def time_for_fragment(self, fragment):
        if not self.random_access_time:
            self.parse_random_access_table()

        if len(self.random_access_time) < fragment:
            return None

        return self.random_access_time[fragment - 1]

    def moof_offset_for_fragment(self, fragment):
        if not self.random_access_moof_offset:
            self.parse_random_access_table()

        if len(self.random_access_moof_offset) < fragment:
            return None, None

        offset = self.random_access_moof_offset[fragment - 1]
        size = 0

        if len(self.random_access_moof_offset) > fragment:
            size = self.random_access_moof_offset[fragment] - offset

        return offset, size

    def moof_offset_for_time(self, seek_time):
        if not self.random_access_moof_offset:
            self.parse_random_access_table()

        # float_time = seek_time/90000.0
        # print('Searching for {float_time:.2f} ({seek_time})'.format(**locals()))
        index = bisect.bisect_left(self.random_access_time, seek_time)
        # print(' - got index:{0} index_time:{1} ({2})'\
        #    .format(index, self.random_access_time[index]/90000.0, self.random_access_time[index]))
        index = max(index-1, 0)
        # print(' - adjusted index:{0} index_time:{1} ({2})'\
        #    .format(index, self.random_access_time[index]/90000.0, self.random_access_time[index]))
        # print(' - obj: {0!s}'.format(self.parent.parent.find('moof[offset={0}]'\
        #   .format(self.random_access_moof_offset[index]))))
        return self.random_access_moof_offset[index]

    def time_for_moof_offset(self, offset):
        if not self.random_access_moof_offset:
            self.parse_random_access_table()

        index = self.random_access_moof_offset.index(offset)
        return self.random_access_time[index]

    @property
    def fragment_count(self):
        if not self.random_access_moof_offset:
            self.parse_random_access_table()

        return len(self.random_access_moof_offset)

    @property
    def decoration(self):
        extras = 'track_id:%d #traf:%d #trun:%d #sample:%d #entries:%d end_time:%d' % (self.track_id,
                                                                                       self.length_size_of_traf_num,
                                                                                       self.length_size_of_trun_num,
                                                                                       self.length_size_of_sample_num,
                                                                                       self.number_of_entry,
                                                                                       self.end_time)
        entries = ['\n']

        if VERBOSE > 1:
            timescale = 0
            format_time = lambda x: '{0}'.format(x)
            moov = self.root.find('moov')
            if moov:
                track_id, track_timescale = self.root.get_video_info()
                if track_id == self.track_id:
                    timescale = float(track_timescale)
                else:
                    timescale = float(self.root.get_audio_info()[1])
                format_time = lambda x: '{0:.3f}'.format(x/timescale)

            for i in range(self.number_of_entry):
                data = self.entry(i)
                entry_time = format_time(data[0])
                entries.append(' - #{index:03d} time:{time} moof:{1} traf:{2} trun:{3} sample:{4}\n'\
                    .format(*data, index=i, time=entry_time))

        return extras + ''.join(entries)[:-1]


class mfro_box(full_box):
    @property
    def decoration(self):
        return 'size:%d' % struct.unpack('>I', self.fmap[self.offset+12:self.offset+16])[0]


class stbl_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)


class stts_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.entry_count = i.send('>I')[0]
        self._entries = []
        for j in range(self.entry_count):
            self._entries.append({'sample_count' : i.send('>I')[0], 'sample_delta' : i.send('>I')[0]})

        self.array = []
        self.unroll()

    def entry(self, index):
        return self._entries[index]

    def unroll(self):
        time = 0
        self.array.append({'time' : 0, 'delta' : 0})
        for entry in self._entries:
            delta = entry['sample_delta']
            for i in range(entry['sample_count']):
                self.array.append({'time' : time, 'delta' : delta})
                time = time + delta


class ctts_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.entry_count = i.send('>I')[0]
        self._entries = []
        for j in range(self.entry_count):
            self._entries.append({'sample_count' : i.send('>I')[0], 'sample_offset' : i.send('>I')[0]})

        self.array = []
        self.unroll()

    def entry(self, index):
        return self._entries[index]

    def unroll(self):
        self.array.append(0)
        for entry in self._entries:
            offset = entry['sample_offset']
            for i in range(entry['sample_count']):
                self.array.append(offset)


class stss_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.entry_count = i.send('>I')[0]
        self._entries = []
        for j in range(self.entry_count):
            self._entries.append({'sample_number' : i.send('>I')[0]})

    def entry(self, index):
        return self._entries[index]
    def has_index(self, index):
        for i in self._entries:
            if i['sample_number'] == index:
                return True
        return False


class stsz_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.sample_size = i.send('>I')[0]
        self.sample_count = i.send('>I')[0]
        self.decoration = 'sample_size=' + str(self.sample_size) + ' sample_count=' + str(self.sample_count)
        self._entries = []
        if self.sample_size == 0:
            for j in range(self.sample_count):
                self._entries.append({'entry_size' : i.send('>I')[0]})

    def entry(self, index):
        return self._entries[index]


class stsc_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.entry_count = i.send('>I')[0]
        self.decoration = 'entry_count=' + str(self.entry_count)
        self._entries = []
        for j in range(self.entry_count):
            self._entries.append({'first_chunk' : i.send('>I')[0], \
                                  'samples_per_chunk' : i.send('>I')[0], \
                                  'sample_description_index' : i.send('>I')[0]})

        self.array = []
        self.unroll()

    def entry(self, index):
        return self._entries[index]

    def unroll(self):
        self.array.append([0, 0, 0])
        last_chunk = 0
        last_num_samples = 0
        for entry in self._entries:
            first_chunk = entry['first_chunk']
            samples_per_chunk = entry['samples_per_chunk']
            sample_description_index = entry['sample_description_index']

            for i in range(last_chunk + 1, first_chunk):
                for j in range(last_num_samples):
                    self.array.append([i, j, last_num_samples])

            for i in range(samples_per_chunk):
                self.array.append([first_chunk, i, samples_per_chunk])

            last_chunk = first_chunk
            last_num_samples = samples_per_chunk

        #print self.array

    def get_unrolled(self, idx):
        if idx < len(self.array):
            return self.array[idx][0], self.array[idx][1]
        else:
            while True:
                #print 'add chunk'
                self.add_chunk()
                #print self.array
                if idx < len(self.array):
                    return self.array[idx][0], self.array[idx][1]

    def add_chunk(self):
        last_chunk = self.array[-1][0]
        num_samples = self.array[-1][2]
        for i in range(num_samples):
            self.array.append([last_chunk + 1, i, num_samples])


class stco_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime
        self.entry_count = i.send('>I')[0]
        self.decoration = 'entry_count=' + str(self.entry_count)
        self._entries = []
        for j in range(self.entry_count):
            val = i.send('>I')
            self._entries.append({'chunk_offset' : val[0]})

    def entry(self, index):
        return self._entries[index]


class ftyp_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)

        i = parse_generator(self.fmap[self.offset+8:self.offset+self.size])
        i.next() # prime

        self.major_brand = i.send('>c')[0] + i.send('>c')[0] + i.send('>c')[0] + i.send('>c')[0]
        self.minor_version = i.send('>I')[0]
        self.brands = []

        num_brands = (self.size - 16) / 4
        for j in range(num_brands):
            self.brands.append(i.send('>c')[0] + i.send('>c')[0] + i.send('>c')[0] + i.send('>c')[0])

    @property
    def decoration(self):
        ret = self.major_brand + ' ' + ','.join(brand for brand in self.brands)
        return ret


class styp_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)

        i = parse_generator(self.fmap[self.offset+8:self.offset+self.size])
        i.next() # prime

        self.major_brand = i.send('>c')[0] + i.send('>c')[0] + i.send('>c')[0] + i.send('>c')[0]
        self.minor_version = i.send('>I')[0]
        self.brands = []

        num_brands = (self.size - 16) / 4
        for j in range(num_brands):
            self.brands.append(i.send('>c')[0] + i.send('>c')[0] + i.send('>c')[0] + i.send('>c')[0])

    @property
    def decoration(self):
        ret = self.major_brand + ' ' + ','.join(brand for brand in self.brands)
        return ret


class tfma_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime

        self.entry_count = i.send('>I')[0]

        self._entries = []
        for j in range(self.entry_count):
            segment_duration = i.send(self.version and '>Q' or '>I')[0]
            media_time = i.send(self.version and '>q' or '>i')[0]
            media_rate_integer = i.send('>H')[0]
            media_rate_fraction = i.send('>H')[0]
            self._entries.append({'segment-duration' : segment_duration,
                                  'media-time' : media_time,
                                  'media-rate-integer' : media_rate_integer,
                                  'media-rate-fraction' : media_rate_fraction})

    def entry(self, index):
        return self._entries[index]

    @property
    def decoration(self):
        ret = ''
        for entry in self._entries:
            ret += ', dur={0} time={1} rate={2}'\
                .format(entry['segment-duration'], entry['media-time'], entry['media-rate-integer'])
        return ret


class tfad_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)


class sidx_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime

        self.reference_track_id = i.send('>I')[0]
        self.timescale = i.send('>I')[0]
        self.first_pres_time = i.send(self.version and '>Q' or '>I')[0]
        self.first_offset = i.send(self.version and '>Q' or '>I')[0]
        self.reserved = i.send('>H')[0]
        self.reference_count = i.send('>H')[0]
        #print 'count=', self.reference_count

        self._references = []
        for j in range(self.reference_count):
            byte_1 = i.send('>I')[0]
            referenced_type = (int(byte_1) >> 31) & 0x01
            referenced_size = int(byte_1) & 0x7fffffff
            subsegment_duration = i.send('>I')[0]
            byte_3 = i.send('>I')[0]
            starts_with_sap = (int(byte_3) >> 31) & 0x01
            sap_type = (int(byte_3) >> 28) & 0x07
            sap_delta_time = int(byte_3) & 0x0fffffff

            ref_type = 'moof'
            if int(referenced_type) == 0: # moof reference
                ref_type = 'moof'
            else:
                ref_type = 'sidx'

            self._references.append({'referenced-type' : ref_type,
                                     'referenced-size' : referenced_size,
                                     'subsegment-duration' : subsegment_duration,
                                     'starts-with-sap' : starts_with_sap,
                                     'sap-type' : sap_type,
                                     'sap-delta-time' : sap_delta_time})

    def track_entry(self, index):
        return self._tracks[index]

    def reference_entry(self, index):
        return self._references[index]

    @property
    def decoration(self):
        msg = 'ref_track={0} timescale={1} first_pres_time={2} first_offset={3} reference_count={4}'\
            .format(self.reference_track_id,
                    self.timescale,
                    self.first_pres_time,
                    self.first_offset,
                    self.reference_count)
        for ref in self._references:
            msg = msg + '\n - ' + str(ref)
        return msg


class udta_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)


class meta_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)


class tfdt_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime

        self.decode_time = i.send(self.version and '>Q' or '>I')[0]

    @property
    def decoration(self):
        return 'decode_time={0}'.format(self.decode_time)


class afra_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime

        byte1 = i.send('>B')[0]
        self.long_ids = (byte1 >> 7) & 0x01
        self.long_offsets = (byte1 >> 6) & 0x01
        self.global_entries = (byte1 >> 5) & 0x01
        self.reserved = (byte1 & 0x1f)
        self.time_scale = i.send('>I')[0]
        self.entry_count = i.send('>I')[0]
        self.entries = []
        for j in range(0, self.entry_count):
            time = i.send('>Q')[0]
            offset = i.send(self.long_offsets and '>Q' or '>I')[0]
            self.entries.append({'time' : time, 'offset' : offset})

        self.global_entry_count = 0
        self.global_entries_list = []
        if self.global_entries:
            self.global_entry_count = i.send('>I')[0]
        for j in range(0, self.global_entry_count):
            time = i.send('>Q')[0]
            segment = i.send(self.long_ids and '>I' or '>H')[0]
            fragment = i.send(self.long_ids and '>I' or '>H')[0]
            afra_offset = i.send(self.long_ids and '>Q' or '>I')[0]
            offset_from_afra = i.send(self.long_ids and '>Q' or '>I')[0]
            self.global_entries_list.append({
                'time' : time,
                'segment' : segment,
                'fragment' : fragment,
                'afra_offset' : afra_offset,
                'offset_from_afra' : offset_from_afra})

    @property
    def decoration(self):
        first_line = 'long ids:{0} long offsets:{1} global entries:{2} timescale:{3} num_entries:{4} num_global_entries:{5}'\
            .format(self.long_ids,
                    self.long_offsets,
                    self.global_entries,
                    self.time_scale,
                    self.entry_count,
                    self.global_entry_count)
        ent = ''
        glob_ent = ''

        if VERBOSE > 1:
            index = 0
            for entry in self.entries:
                ent += '\n - E[{0}]: time={1} offset={2}'.format(index, entry['time'], entry['offset'])
                index = index + 1

            index = 0
            for entry in self.global_entries_list:
                glob_ent += '\n - GE[{0}]: time={1} segment={2} fragment={3}, afra_offset={4} offset_from_afra={5}'\
                    .format(entry['time'],
                            entry['segment'],
                            entry['fragment'],
                            entry['afra_offset'],
                            entry['offset_from_afra'])

        return first_line + ent + glob_ent


class asrt_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime

        self.quality_entry_count = i.send('>B')[0]
        self.qualities = []
        for j in range(0, self.quality_entry_count):
            self.qualities.append(read_string(i))

        self.segment_run_entry_count = i.send('>I')[0]
        self.segments = []
        for j in range(0, self.segment_run_entry_count):
            f_seg = i.send('>I')[0]
            frag_per_seg = i.send('>I')[0]
            segment_run_entry = 'first_segment: {0} fragments_per_segment: {1}'.format(f_seg, frag_per_seg)
            self.segments.append(segment_run_entry)

    def description(self):
        ret = '\'%s\' [%d:%d] %s' % (self.type,
                                     self.offset,
                                     self.size,
                                     hasattr(self, 'decoration') and self.decoration or '')
        return ret

    @property
    def decoration(self):
        msg = ' quality_entry_count={0} segment_run_entry_count={1}'\
            .format(self.quality_entry_count, self.segment_run_entry_count)
        index = 0
        for quality in self.qualities:
            msg = msg + '\n - Q[{0}]: {1}'.format(index, quality)
            index = index + 1

        index = 0
        for segment in self.segments:
            msg = msg + '\n - S[{0}]: {1}'.format(index, segment)
            index = index + 1

        return msg


class afrt_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime

        self.time_scale = i.send('>I')[0]

        self.quality_entry_count = i.send('>B')[0]
        self.qualities = []
        for j in range(0, self.quality_entry_count):
            self.qualities.append(read_string(i))

        self.fragment_run_entry_count = i.send('>I')[0]
        self.fragments = []
        for j in range(0, self.fragment_run_entry_count):
            first_fragment = i.send('>I')[0]
            first_fragment_timestamp = i.send('>Q')[0]
            fragment_duration = i.send('>I')[0]
            discontinuity_value = ''
            if fragment_duration == 0:
                discontinuity_indicator = i.send('>B')[0]
                if discontinuity_indicator == 0:
                    discontinuity_value = 'discontinuity_indicator: end of pres'
                elif discontinuity_indicator == 1:
                    discontinuity_value = 'discontinuity_indicator: frag numbering'
                elif discontinuity_indicator == 2:
                    discontinuity_value = 'discontinuity_indicator: timestamps'
                elif discontinuity_indicator == 3:
                    discontinuity_value = 'discontinuity_indicator: timestamps + frag numbering'
                else:
                    discontinuity_value = 'unknown ({0})'.format(discontinuity_indicator)
            self.fragments.append('first_fragment: {0} first_fragment_timestamp: {1} fragment_duration: {2} {3}'\
                .format(first_fragment, first_fragment_timestamp, fragment_duration, discontinuity_value))

    def description(self):
        ret = '\'%s\' [%d:%d] %s' % (self.type,
                                     self.offset,
                                     self.size,
                                     hasattr(self, 'decoration') and self.decoration or '')
        return ret

    @property
    def decoration(self):
        msg = 'time_scale={0} quality_entry_count={1} fragment_run_entry_count={2}'\
            .format(self.time_scale, self.quality_entry_count, self.fragment_run_entry_count)
        index = 0
        for quality in self.qualities:
            msg = msg + '\n - Q[{0}]: {1}'.format(index, quality)
            index = index + 1

        index = 0
        for fragment in self.fragments:
            msg = msg + '\n - F[{0}]: {1}'.format(index, str(fragment))
            index = index + 1

        return msg


def read_string(parser):
    msg = ''
    byte = parser.send('>B')[0]
    while byte != 0:
        msg = msg + chr(byte)
        byte = parser.send('>B')[0]
    return msg


class abst_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime

        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

        self.bootstrap_info_version = i.send('>I')[0]
        byte2 = i.send('>B')[0]
        self.profile = (byte2 >> 6) & 0x03
        self.live = (byte2 >> 5) & 0x01
        self.update = (byte2 >> 4) & 0x01
        self.time_scale = i.send('>I')[0]
        self.current_media_time = i.send('>Q')[0]
        self.smtp_time_code_offset = i.send('>Q')[0]
        self.movie_identifier = read_string(i)

        o = 38 + len(self.movie_identifier)

        self.server_entry_count = i.send('>B')[0]
        o = o + 1
        self.servers = []
        for j in range(0, self.server_entry_count):
            server = read_string(i)
            self.servers.append(server)
            o = o + 1 + len(server)

        self.quality_entry_count = i.send('>B')[0]
        o = o + 1
        self.qualities = []
        for j in range(0, self.server_entry_count):
            quality = read_string(i)
            self.qualities.append(quality)
            o = o + 1 + len(quality)

        self.drm_data = read_string(i)
        self.meta_data = read_string(i)
        o = o + 2 + len(self.drm_data) + len(self.meta_data)

        # Segment run
        self.segment_run_table_count = i.send('>B')[0]
        o = o + 1
        self.segment_boxes = []
        for j in range(0, self.segment_run_table_count):
            box_size = i.send('>I')[0]
            box_type = i.send('>4s')[0]
            olas_box = asrt_box(self.fmap, box_type, box_size, self.offset + o, self)
            self.segment_boxes.append(olas_box)
            o = o + box_size

            for k in range(0, box_size - 8):
                i.send('>B')[0]

        # Fragment run
        self.fragment_run_table_count = i.send('>B')[0]
        o = o + 1
        self.fragment_boxes = []
        for j in range(0, self.fragment_run_table_count):
            box_size = i.send('>I')[0]
            box_type = i.send('>4s')[0]
            olas_box = afrt_box(self.fmap, box_type, box_size, self.offset + o, self)
            self.fragment_boxes.append(olas_box)
            o = o + box_size

            for k in range(0, box_size - 8):
                i.send('>B')[0]

    @property
    def decoration(self):
        msg = 'bi_ver:{0} prof:{1} live={2} update={3} t_scale:{4} cur_mtime:{5} smtp_toff:{6} movie_id:{7}, #server_entries:{8} #qualities:{9}, #seg_runs:{10}, #frag_runs:{11}'\
        .format(self.bootstrap_info_version,
                self.profile,
                self.live,
                self.update,
                self.time_scale,
                self.current_media_time,
                self.smtp_time_code_offset,
                self.movie_identifier,
                self.server_entry_count,
                self.quality_entry_count,
                self.segment_run_table_count,
                self.fragment_run_table_count)

        if VERBOSE > 0:
            sub_boxes = ''
            for segment_box in self.segment_boxes:
                sub_boxes = sub_boxes + '\n - ' + segment_box.description().replace('\n', '\n - ')

            msg += sub_boxes

            sub_boxes = ''
            for fragment_box in self.fragment_boxes:
                sub_boxes = sub_boxes + '\n - ' + fragment_box.description().replace('\n', '\n - ')

            msg += sub_boxes

        return msg

class mdat_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)
        #print dump_hex(self.fmap[self.offset:self.offset + 200])

    def print_base_data_offset(self):
        trafs = self.find_all('.moof.traf')
        for b in trafs:
            tfhd = b.find('tfhd')
            base_data_offset = tfhd.base_data_offset
            truns = b.find_all('trun')
            for sb in truns:
                trun_offset = sb.data_offset
                for i in range(sb.sample_count):
                    row = sb.sample_entry(i)
                    print 'trackid: {0} base_offset: {1} trun_offset: {2} row: {3}'\
                        .format(tfhd.track_id, base_data_offset, trun_offset, str(row))


class payl_box(box):
    def __init__(self, *args):
        box.__init__(self, *args)
        self.cue_text = self.fmap[self.offset + 8:self.offset + self.size]

    @property
    def decoration(self):
        return 'tfxd: time={0} dur={1}'.format(self.time, self.duration)


class tfxd_box(object):
    def __init__(self, data, version, flags):
        self.data = data
        self.version = version
        self.flags = flags

        i = parse_generator(data)
        i.next() # prime

        self.time = i.send(self.version and '>Q' or '>I')[0]
        self.duration = i.send(self.version and '>Q' or '>I')[0]

    @property
    def decoration(self):
        return 'tfxd: time={0} dur={1}'.format(self.time, self.duration)


class tfrf_box(object):
    def __init__(self, data, version, flags):
        self.data = data
        self.version = version
        self.flags = flags
        self.times = []
        self.durations = []

        i = parse_generator(data)
        i.next() # prime

        self.num_entries = i.send('>B')[0]
        print 3, self.num_entries
        for k in range(self.num_entries):
            self.times.append(i.send(self.version and '>Q' or '>I')[0])
            self.durations.append(i.send(self.version and '>Q' or '>I')[0])

    @property
    def decoration(self):
        msg = 'tfrf: num entries = {0}'.format(self.num_entries)
        for i in range(self.num_entries):
            msg = msg + ' time={0} dur={1}'.format(self.times[i], self.durations[i])
        return msg


class sampleEncryption_box(object):
    def __init__(self, data, version, flags, iv_size=8):
        self.data = data
        self.version = version
        self.flags = flags
        self.iv_size = iv_size

        self.ivs = []
        self.sub_sample_vec = []

    @property
    def decoration(self):
        msg = 'PIFF Sample Encryption'
        base_offset = 0
        if self.flags & 0x01:
            alg = struct.unpack('>i', '\x00'+self.data[base_offset:base_offset + 3])[0]
            base_offset += 3
            self.iv_size = struct.unpack('>B', self.data[base_offset:base_offset + 1])[0]
            base_offset += 1
            key_id = ''.join(["%02X" % ord(x) for x in self.data[base_offset:base_offset + 16]])
            msg += '\n Algorithm: {0} IV_size: {1} Key ID: 0x{2}'.format(alg, self.iv_size, key_id)
            base_offset += 16

        sample_count = struct.unpack('>L', self.data[base_offset:base_offset + 4])[0]
        base_offset += 4
        msg += '\n - Sample Count: {0}'.format(sample_count)

        for sample in range(sample_count):
            iv = ''.join(["%02X" % ord(x) for x in self.data[base_offset:base_offset + self.iv_size]])
            self.ivs.append(iv) # NOTE: this should be done in the constructor
            msg += '\n - - #{0} iv=0x{1}'.format(sample, iv)
            base_offset += self.iv_size
            if self.flags & 0x02:
                sub_samples = []
                entries = struct.unpack('>H', self.data[base_offset:base_offset + 2])[0]
                base_offset += 2
                for e in range(entries):
                    clear_data = struct.unpack('>H', self.data[base_offset:base_offset + 2])[0]
                    base_offset += 2
                    enc_data = struct.unpack('>L', self.data[base_offset:base_offset + 4])[0]
                    base_offset += 4
                    msg += '\n - - - #{0} clear={1} encrypted={2}'.format(e, clear_data, enc_data)

                    sub_samples.append([clear_data, enc_data])
                self.sub_sample_vec.append(sub_samples)

        return msg


class trackEncryption_box(object):
    def __init__(self, data, version, flags):
        self.data = data
        self.version = version
        self.flags = flags

    @property
    def decoration(self):
        msg = 'PIFF Track Encryption'
        base_offset = 0

        alg = struct.unpack('>i', '\x00'+self.data[base_offset:base_offset + 3])[0]
        base_offset += 3
        self.iv_size = struct.unpack('>B', self.data[base_offset:base_offset + 1])[0]
        base_offset += 1
        key_id = ''.join(["%02X" % ord(x) for x in self.data[base_offset:base_offset + 16]])
        msg += '\n Algorithm: {0} IV_size: {1} Default Key ID: 0x{2}'.format(alg, self.iv_size, key_id)
        base_offset += 16

        return msg


class pssh_uuid_box(object):
    def __init__(self, data, version, flags):
        self.data = data
        self.version = version
        self.flags = flags

    @property
    def decoration(self):
        msg = 'PIFF PSSH'
        base_offset = 0

        system_id = ''.join(["%02X" % ord(x) for x in self.data[base_offset:base_offset + 16]])
        base_offset += 16

        data_size = struct.unpack('>I', self.data[base_offset:base_offset + 4])[0]
        base_offset += 4

        data = ''.join(["%02X" % ord(x) for x in self.data[base_offset:base_offset + data_size]])

        msg += '\n system_id: {0} data_size: {1} data {2}'.format(system_id, data_size, data)
        base_offset += 16

        return msg

tfxdGuid = '6D1D9B0542D544E680E2141DAFF757B2'
tfrfGuid = 'D4807EF2CA3946958E5426CB9E46A79F'
sampleEncryptionGuid = 'A2394F525A9B4F14A2446C427C648DF4'
trackEncryptionGuid = "8974DBCE7BE74C5184F97148F9882554"
psshGuid = "D08A4F1810F34A82B6C832D8ABA183D3"


class uuid_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

    @property
    def decoration(self):
        typeStr = ''.join(["%02X"%ord(x) for x in self.extended_type])
        msg = 'ext_type:0x{0} '.format(typeStr)
        data = self.fmap[self.offset+28:self.offset+self.size]

        #print dump_hex(data)

        if typeStr == tfxdGuid:
            tfxd = tfxd_box(data, self.version, self.flags)
            return msg + tfxd.decoration
        elif typeStr == tfrfGuid:
            tfrf = tfrf_box(data, self.version, self.flags)
            return msg + tfrf.decoration
        elif typeStr == sampleEncryptionGuid:
            sampleEncryption = sampleEncryption_box(data, self.version, self.flags, iv_size=8)
            return msg + sampleEncryption.decoration
        elif typeStr == trackEncryptionGuid:
            trackEncryption = trackEncryption_box(data, self.version, self.flags)
            return msg + trackEncryption.decoration
        elif typeStr == psshGuid:
            pssh_uuid = pssh_uuid_box(data, self.version, self.flags)
            return msg + pssh_uuid.decoration
        else:
            print 'unknown uuid tag', msg
        return


class sdtp_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

    def lead(self, il):
        if il == 0:
            return 'unknown'
        elif il == 1:
            return 'yes, not decodable'
        elif il == 2:
            return 'no'
        elif il == 3:
            return 'yes, decodable'

    def depends(self, v):
        if v == 0:
            return 'unknown'
        elif v == 1:
            return 'yes'
        elif v == 2:
            return 'no'
        elif v == 3:
            return 'reserved'

    def dependend(self, v):
        if 0 == v == 0:
            return 'unknown'
        elif 1 == v == 1:
            return 'yes'
        elif 2 == v == 2:
            return 'no'
        elif 3 == v == 3:
            return 'reserved'

    def redundancy(self, v):
        if v == 0:
            return 'unknown'
        elif v == 1:
            return 'yes'
        elif v == 2:
            return 'no'
        elif v == 3:
            return 'reserved'

    @property
    def decoration(self):
        samples = self.size - 12
        msg = 'samples:{0}'.format(samples)
        base_offset = self.offset + 12
        for i in range(samples):
            v = struct.unpack('>B', self.fmap[base_offset+i:base_offset + 1 + i])[0]
            is_lead = (v & 0xc0) >> 6
            depends_on = (v & 0x30) >> 4
            dependend_on = (v & 0x0c) >> 2
            has_redundancy = (v & 0x03)
            msg += '\n- index:{0} lead: {1} depends:{2} dependend:{3} redundancy:{4}'\
                .format(i,
                        self.lead(is_lead),
                        self.depends(depends_on),
                        self.dependend(dependend_on),
                        self.redundancy(has_redundancy))

        return msg


class emsg_box(full_box):
    def __init__(self, *args):
        full_box.__init__(self, *args)
        #print dump_hex(self.fmap[self.offset:self.offset+self.size])

        i = parse_generator(self.fmap[self.offset+12:self.offset+self.size])
        i.next() # prime

        self.scheme_id_uri = read_string(i)
        self.value = read_string(i)
        self.timescale = i.send('>I')[0]
        self.presentation_time_delta = i.send('>I')[0]
        self.event_duration = i.send('>I')[0]
        self.id = i.send('>I')[0]

        self.message_data = []
        x = False
        try:
            while not x:
                self.message_data.append(i.send('>B')[0])
        except BaseException as e:
            pass

        self.message_data_str = ''.join(['%02x' % c for c in self.message_data])

    @property
    def decoration(self):
        return 'scheme_id_uri={0}, value={1}, data_len={2}'\
            .format(self.scheme_id_uri, self.value, len(self.message_data_str))

keys = globals().keys()
for key in keys:
    if key.endswith('_box'):
        #print 'adding: ', k
        REGISTERED_BOXES[key] = globals()[key]


if __name__ == '__main__':
    pass
