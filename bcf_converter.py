#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BCFConverter
# Version v2.1
# This file is a modified version of BCFSTM-BCFWAV Converter
# Copyright © 2017-2018 AboodXD

# This file is part of UltimateBoTWConverter.

# BCFConverter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BCFConverter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time
import struct

supp_STM = ["FSTM", "CSTM", "FSTP"]
supp_WAV = ["FWAV", "CWAV"]

class Header(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4s2xH2I2H')

    def data(self, data, pos):
        (self.magic,
         self.size_,
         self.version,
         self.fileSize,
         self.numBlocks,
         self.reserved) = self.unpack_from(data, pos)


class BLKHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4sI')

    def data(self, data, pos):
        (self.magic,
         self.size_) = self.unpack_from(data, pos)


class STMInfo(struct.Struct):  # Stream Info
    def __init__(self, bom):
        super().__init__(bom + '4B11I')

    def data(self, data, pos):
        (self.codec,
         self.loop_flag,
         self.ch_count,
         self.reg_count,
         self.sample,
         self.loop_start,
         self.sample_count,
         self.sampleBlk_count,
         self.sampleBlk_size,
         self.sampleBlk_sampleCount,
         self.lSampleBlk_size,
         self.lSampleBlk_sampleCount,
         self.lSampleBlk_padSize,
         self.seek_size,
         self.SISC) = self.unpack_from(data, pos)

class WAVInfo(struct.Struct):  # Stream Info
    def __init__(self, bom):
        super().__init__(bom + '2B2x4I')

    def data(self, data, pos):
        (self.codec,
         self.loop_flag,
         self.sample,
         self.loop_start,
         self.loop_end,
         self.reserved) = self.unpack_from(data, pos)


class TRKInfo(struct.Struct):  # Track Info
    def __init__(self, bom):
        super().__init__(bom + '2BH')

    def data(self, data, pos):
        (self.volume,
         self.pan,
         self.unk) = self.unpack_from(data, pos)


class DSPContext(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '3H')

    def data(self, data, pos):
        (self.predictor_scale,
         self.preSample,
         self.preSample2) = self.unpack_from(data, pos)


class IMAContext(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '2H')

    def data(self, data, pos):
        (self.data_,
         self.tableIndex) = self.unpack_from(data, pos)


class Ref(struct.Struct):  # Reference
    def __init__(self, bom):
        super().__init__(bom + 'H2xi')

    def data(self, data, pos):
        (self.type_,
         self.offset) = self.unpack_from(data, pos)

class REGNInfo(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + 'H2xH2xi3I')
    
    def data(self, data, pos):
        (self.reg_size,
         self.reg_flag,
         self.reg_offset,
         self.loop_st,
         self.loop_ed,
         self.secret) = self.unpack_from(data, pos)

def convFile(f, dest, dest_bom):
    # Convert embedded files, usually inside a bars file
    magic = bytes_to_string(f[:4])
    if magic in supp_STM and dest in supp_STM:
        outputBuffer = STMtoSTM(f, magic, dest, dest_bom)

    elif magic in supp_WAV and dest in supp_WAV:
        outputBuffer = WAVtoWAV(f, magic, dest, dest_bom)

    elif magic in supp_STM and dest in supp_WAV:
        outputBuffer = STMtoWAV(f, magic, dest, dest_bom)

    elif magic in supp_WAV and dest in supp_STM:
        print("\nBFWAV/BCWAV to BFSTM/BCSTM/BFSTP is not implemented!")

    else:
        print("\nUnsupported file format!")
    
    return outputBuffer

def bytes_to_string(data):
    end = data.find(b'\0')
    if end == -1:
        return data.decode('utf-8')

    return data[:end].decode('utf-8')

def to_bytes(inp, length=1, bom='>'):
    if isinstance(inp, bytearray):
        return bytes(inp)

    elif isinstance(inp, int):
        return inp.to_bytes(length, ('big' if bom == '>' else 'little'))

    elif isinstance(inp, str):
        return inp.encode('utf-8').ljust(length, b'\0')

def align(x, y):
    return ((x - 1) | (y - 1)) + 1

def STMtoSTM(f, magic, dest, dest_bom):
    outputBuffer = bytearray(len(f))
    pos = 0

    if f[4:6] == b'\xFF\xFE':
        bom = '<'

    elif f[4:6] == b'\xFE\xFF':
        bom = '>'

    else:
        print("\nInvalid BOM!")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if not dest_bom:
        if dest in ["FSTM", "FSTP"]:
            dest_bom = '>'

        else:
            dest_bom = '<'

    header = Header(bom)
    header.data(f, pos)

    curr = magic

    dest_ver = {"FSTM": 0x40000, "CSTM": 0x2020000, "FSTP": 0x20100}
    if magic == dest:
        dest_ver[dest] = header.version

    outputBuffer[pos:pos + header.size] = bytes(
        Header(dest_bom).pack(to_bytes(dest, 4), header.size_, dest_ver[dest], header.fileSize, header.numBlocks,
                              header.reserved))

    outputBuffer[4:6] = (b'\xFE\xFF' if dest_bom == '>' else b'\xFF\xFE')

    pos += header.size

    dest_type = {"FSTM": 0x4002, "CSTM": 0x4002, "FSTP": 0x4004}
    sized_refs = {}

    for i in range(1, header.numBlocks + 1):
        sized_refs[i] = Ref(bom)
        sized_refs[i].data(f, pos + 12 * (i - 1))

        if sized_refs[i].type_ in [0x4002, 0x4004]:
            outputBuffer[pos + 12 * (i - 1):pos + 12 * (i - 1) + sized_refs[i].size] = bytes(
                Ref(dest_bom).pack(dest_type[dest], sized_refs[i].offset))

        else:
            outputBuffer[pos + 12 * (i - 1):pos + 12 * (i - 1) + sized_refs[i].size] = bytes(
                Ref(dest_bom).pack(sized_refs[i].type_, sized_refs[i].offset))

        sized_refs[i].block_size = struct.unpack(bom + "I", f[pos + 12 * (i - 1) + 8:pos + 12 * i])[0]
        outputBuffer[pos + 12 * (i - 1) + 8:pos + 12 * i] = to_bytes(sized_refs[i].block_size, 4, dest_bom)

    if sized_refs[1].type_ != 0x4000 or sized_refs[1].offset in [0, -1]:
        print("\nSomething went wrong!\nError code: 1")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = sized_refs[1].offset

    info = BLKHeader(bom)
    info.data(f, pos)

    outputBuffer[pos:pos + info.size] = bytes(BLKHeader(dest_bom).pack(info.magic, info.size_))
    pos += info.size

    stmInfo_ref = Ref(bom)
    stmInfo_ref.data(f, pos)

    outputBuffer[pos:pos + stmInfo_ref.size] = bytes(Ref(dest_bom).pack(stmInfo_ref.type_, stmInfo_ref.offset))

    if stmInfo_ref.type_ != 0x4100 or stmInfo_ref.offset in [0, -1]:
        print("\nSomething went wrong!\nError code: 2")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    stmInfo_ref.pos = pos
    pos += stmInfo_ref.size

    trkInfoTable_ref = Ref(bom)
    trkInfoTable_ref.data(f, pos)

    outputBuffer[pos:pos + trkInfoTable_ref.size] = bytes(
        Ref(dest_bom).pack(trkInfoTable_ref.type_, trkInfoTable_ref.offset))

    if trkInfoTable_ref.type_ not in [0x0101, 0]:
        print("\nSomething went wrong!\nError code: 3")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos += trkInfoTable_ref.size

    channelInfoTable_ref = Ref(bom)
    channelInfoTable_ref.data(f, pos)

    outputBuffer[pos:pos + channelInfoTable_ref.size] = bytes(
        Ref(dest_bom).pack(channelInfoTable_ref.type_, channelInfoTable_ref.offset))

    if channelInfoTable_ref.type_ != 0x0101:
        print("\nSomething went wrong!\nError code: 4")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = stmInfo_ref.offset + stmInfo_ref.pos
    stmInfo = STMInfo(bom)
    stmInfo.data(f, pos)

    outputBuffer[pos:pos + stmInfo.size] = bytes(
        STMInfo(dest_bom).pack(stmInfo.codec, stmInfo.loop_flag, stmInfo.ch_count, stmInfo.reg_count, stmInfo.sample, stmInfo.loop_start,
                            stmInfo.sample_count, stmInfo.sampleBlk_count, stmInfo.sampleBlk_size,
                            stmInfo.sampleBlk_sampleCount, stmInfo.lSampleBlk_size, stmInfo.lSampleBlk_sampleCount,
                            stmInfo.lSampleBlk_padSize, stmInfo.seek_size, stmInfo.SISC))
    pos += stmInfo.size

    sampleData_ref = Ref(bom)
    sampleData_ref.data(f, pos)

    outputBuffer[pos:pos + sampleData_ref.size] = bytes(Ref(dest_bom).pack(sampleData_ref.type_, sampleData_ref.offset))
    pos += sampleData_ref.size

    regInfo = REGNInfo(bom)
    regInfo.data(f, pos)

    outputBuffer[pos:pos + regInfo.size] = bytes(REGNInfo(dest_bom).pack(regInfo.reg_size, regInfo.reg_flag, regInfo.reg_offset, regInfo.loop_st, regInfo.loop_ed, regInfo.secret))
    pos += regInfo.size

    trkInfoTable = {}
    trkInfo = {}

    if trkInfoTable_ref.offset not in [0, -1]:
        pos = trkInfoTable_ref.offset + stmInfo_ref.pos
        count = struct.unpack(bom + "I", f[pos:pos + 4])[0]
        outputBuffer[pos:pos + 4] = to_bytes(count, 4, dest_bom)
        pos += 4

        for i in range(1, count + 1):
            pos = trkInfoTable_ref.offset + stmInfo_ref.pos + 4
            trkInfoTable[i] = Ref(bom)
            trkInfoTable[i].data(f, pos + 8 * (i - 1))

            outputBuffer[pos + 8 * (i - 1):pos + 8 * (i - 1) + trkInfoTable[i].size] = bytes(
                Ref(dest_bom).pack(trkInfoTable[i].type_, trkInfoTable[i].offset))

            if trkInfoTable[i].offset not in [0, -1]:
                pos = trkInfoTable[i].offset + pos - 4
                trkInfo[i] = TRKInfo(bom)
                trkInfo[i].data(f, pos)

                outputBuffer[pos:pos + trkInfo[i].size] = bytes(
                    TRKInfo(dest_bom).pack(trkInfo[i].volume, trkInfo[i].pan, trkInfo[i].unk))

                pos += trkInfo[i].size
                channelIndexByteTable_ref = Ref(bom)
                channelIndexByteTable_ref.data(f, pos)

                outputBuffer[pos:pos + channelIndexByteTable_ref.size] = bytes(
                    Ref(dest_bom).pack(channelIndexByteTable_ref.type_, channelIndexByteTable_ref.offset))

                if channelIndexByteTable_ref.offset not in [0, -1]:
                    pos = channelIndexByteTable_ref.offset + pos - trkInfo[i].size
                    count = struct.unpack(bom + "I", f[pos:pos + 4])[0]
                    outputBuffer[pos:pos + 4] = to_bytes(count, 4, dest_bom)
                    pos += 4
                    elem = f[pos:pos + count]
                    outputBuffer[pos:pos + count] = elem

    channelInfoTable = {}
    ADPCMInfo_ref = {}
    param = {}

    pos = channelInfoTable_ref.offset + stmInfo_ref.pos
    count = struct.unpack(bom + "I", f[pos:pos + 4])[0]
    outputBuffer[pos:pos + 4] = to_bytes(count, 4, dest_bom)
    pos += 4

    for i in range(1, count + 1):
        pos = channelInfoTable_ref.offset + stmInfo_ref.pos + 4
        channelInfoTable[i] = Ref(bom)
        channelInfoTable[i].data(f, pos + 8 * (i - 1))

        outputBuffer[pos + 8 * (i - 1):pos + 8 * (i - 1) + channelInfoTable[i].size] = bytes(
            Ref(dest_bom).pack(channelInfoTable[i].type_, channelInfoTable[i].offset))

        if channelInfoTable[i].offset not in [0, -1]:
            pos = channelInfoTable[i].offset + pos - 4
            ADPCMInfo_ref[i] = Ref(bom)
            ADPCMInfo_ref[i].data(f, pos)

            outputBuffer[pos:pos + ADPCMInfo_ref[i].size] = bytes(
                Ref(dest_bom).pack(ADPCMInfo_ref[i].type_, ADPCMInfo_ref[i].offset))

            if ADPCMInfo_ref[i].offset not in [0, -1]:
                pos = ADPCMInfo_ref[i].offset + pos
                if ADPCMInfo_ref[i].type_ == 0x0300:
                    for i in range(1, 17):
                        param[i] = struct.unpack(bom + "H", f[pos + 2 * (i - 1):pos + 2 * (i - 1) + 2])[0]
                        outputBuffer[pos + 2 * (i - 1):pos + 2 * (i - 1) + 2] = to_bytes(param[i], 2, dest_bom)

                    pos += 32
                    context = DSPContext(bom)
                    context.data(f, pos)

                    outputBuffer[pos:pos + context.size] = bytes(
                        DSPContext(dest_bom).pack(context.predictor_scale, context.preSample, context.preSample2))
                        
                    pos += context.size
                    loopContext = DSPContext(bom)
                    loopContext.data(f, pos)

                    outputBuffer[pos:pos + loopContext.size] = bytes(
                        DSPContext(dest_bom).pack(loopContext.predictor_scale, loopContext.preSample,
                                                  loopContext.preSample2))

                    pos += loopContext.size
                    pos += 2

                elif ADPCMInfo_ref[i].type_ == 0x0301:
                    context = IMAContext(bom)
                    context.data(f, pos)

                    outputBuffer[pos:pos + context.size] = bytes(
                        IMAContext(dest_bom).pack(context.data_, context.tableIndex))

                    pos += context.size
                    loopContext = IMAContext(bom)
                    loopContext.data(f, pos)

                    outputBuffer[pos:pos + loopContext.size] = bytes(
                        IMAContext(dest_bom).pack(loopContext.data_, loopContext.tableIndex))

                    pos += loopContext.size

    dest_dataHead = {"FSTM": b'DATA', "CSTM": b'DATA', "FSTP": b'PDAT'}

    for i in range(1, header.numBlocks + 1):
        if sized_refs[i].offset not in [0, -1]:
            if sized_refs[i].type_ == 0x4001:
                pos = sized_refs[i].offset
                seek = BLKHeader(bom)
                seek.data(f, pos)
                outputBuffer[pos:pos + seek.size] = bytes(BLKHeader(dest_bom).pack(seek.magic, seek.size_))
                pos += seek.size
                seek.data_ = f[pos:pos + seek.size_ - 8]

                if curr[:-1] == dest[:-1]:
                    for i in range(0, len(seek.data_), 2):
                        outputBuffer[pos + i:pos + i + 2] = bytes([
                            seek.data_[i+1], seek.data_[i],
                        ])

                else:
                    outputBuffer[pos:pos + seek.size_ - 8] = seek.data_
                        
            elif sized_refs[i].type_ == 0x4003:
                pos = sized_refs[i].offset
                regn = BLKHeader(bom)
                regn.data(f, pos)
                outputBuffer[pos:pos + regn.size] = bytes(BLKHeader(dest_bom).pack(regn.magic, regn.size_))
                pos += 32
                regn.data_ = f[pos:pos + regn.size_ - 32]

                if bom != dest_bom:
                    for i in range(0, len(regn.data_), regInfo.reg_size):
                        j = 0
                        step = 2
                        while j < regInfo.reg_size:
                            if j < 8:
                                step = 4
                                outputBuffer[pos + j:pos + j + 4] = bytes([
                                    regn.data_[i+j+3], regn.data_[i+j+2], regn.data_[i+j+1], regn.data_[i+j],
                                ])
                            else:
                                step = 2
                                outputBuffer[pos + j:pos + j + 2] = bytes([
                                    regn.data_[i+j+1], regn.data_[i+j],
                                ])
                            
                            j += step
                        pos += regInfo.reg_size

                else:
                    outputBuffer[pos:pos + regn.size_ - 8] = regn.data_

            elif sized_refs[i].type_ in [0x4002, 0x4004]:
                pos = sized_refs[i].offset
                data = BLKHeader(bom)
                data.data(f, pos)
                outputBuffer[pos:pos + data.size] = bytes(BLKHeader(dest_bom).pack(dest_dataHead[dest], data.size_))
                pos += data.size
                data.data_ = f[pos:pos + data.size_ - 8]

                if bom != dest_bom and stmInfo.codec == 1:
                    for i in range(0, len(data.data_), 2):
                        outputBuffer[pos + i:pos + i + 2] = bytes([
                            data.data_[i+1], data.data_[i],
                        ])

                else:
                    outputBuffer[pos:pos + data.size_ - 8] = data.data_
                if bom != dest_bom and dest == "FSTP":
                    # pdat header length is twice as big on switch than on WiiU
                    pdat_header_len = 32 if dest_bom == ">" else 64
                    pdat_offset = pos - 8
                    # Extract the pdat length and subtract half of the original header, since the other half is already accounted for in the data
                    pdat_len = int.from_bytes(outputBuffer[pdat_offset + 4:pdat_offset + 8], "little" if dest_bom == "<" else "big") - pdat_header_len // 2
                    outputBuffer[pdat_offset + 4:pdat_offset + 8] = struct.pack(dest_bom + "I", pdat_len + pdat_header_len)
                    outputBuffer[pdat_offset + 8:pdat_offset + 12] = b'\x00\x00\x00\x01' if dest_bom == ">" else b'\x01\x00\x00\x00'

                    # only data in PDAT length
                    outputBuffer[pdat_offset + 16:pdat_offset + 20] = struct.pack(dest_bom + "I", pdat_len) 

                    # just before the data in PDAT starts - usually stands 0x14 for WiiU (or Big Endian) and 0x54 for Switch (or Little Endian), currently assuming it's about BOM
                    outputBuffer[pdat_offset + 28:pdat_offset + 32] = struct.pack(dest_bom + "I", 20 if dest_bom == ">" else 52)

                    # since switch PDAT header is twice as big (32 vs 64), it needs to have the second half filled with zeros
                    if dest_bom == "<": 
                        for _ in range(32):
                            # inserting zeros that are not in the file, otherwise it would replace sound data
                            outputBuffer.insert(pdat_offset + 32, 0)

                    # trim all the unnecessary data
                    del outputBuffer[pdat_offset + pdat_header_len + pdat_len:]

                    # write the offset to the PDAT section and it's whole length
                    outputBuffer[36:44] = struct.pack(dest_bom + "2I", pdat_offset, pdat_len + pdat_header_len)

                    # fill the rest of the FSTP section with 0
                    outputBuffer[44:sized_refs[1].offset] = [0]*20

                    # write the whole file size here
                    outputBuffer[12:16] = struct.pack(dest_bom + "I", len(outputBuffer))                    

    return outputBuffer


def WAVtoWAV(f, magic, dest, dest_bom):
    outputBuffer = bytearray(len(f))
    pos = 0

    if f[4:6] == b'\xFF\xFE':
        bom = '<'

    elif f[4:6] == b'\xFE\xFF':
        bom = '>'

    else:
        print("\nInvalid BOM!")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if dest_bom == '':
        if dest == "FWAV":
            dest_bom = '>'

        else:
            dest_bom = '<'

    header = Header(bom)
    header.data(f, pos)

    dest_ver = {"FWAV": 0x10100, "CWAV": 0x2010000}
    if magic == dest:
        dest_ver[dest] = header.version

    outputBuffer[pos:pos + header.size] = bytes(
        Header(dest_bom).pack(to_bytes(dest, 4), header.size_, dest_ver[dest], header.fileSize, header.numBlocks,
                              header.reserved))

    outputBuffer[4:6] = (b'\xFE\xFF' if dest_bom == '>' else b'\xFF\xFE')

    pos += header.size
    sized_refs = {}

    for i in range(1, header.numBlocks + 1):
        sized_refs[i] = Ref(bom)
        sized_refs[i].data(f, pos + 12 * (i - 1))

        outputBuffer[pos + 12 * (i - 1):pos + 12 * (i - 1) + sized_refs[i].size] = bytes(
            Ref(dest_bom).pack(sized_refs[i].type_, sized_refs[i].offset))

        sized_refs[i].block_size = struct.unpack(bom + "I", f[pos + 12 * (i - 1) + 8:pos + 12 * i])[0]

        outputBuffer[pos + 12 * (i - 1) + 8:pos + 12 * i] = to_bytes(sized_refs[i].block_size, 4, dest_bom)

    if sized_refs[1].type_ != 0x7000 or sized_refs[1].offset in [0, -1]:
        print("\nSomething went wrong!\nError code: 5")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = sized_refs[1].offset

    info = BLKHeader(bom)
    info.data(f, pos)
    info.pos = pos

    outputBuffer[pos:pos + info.size] = bytes(BLKHeader(dest_bom).pack(info.magic, info.size_))

    pos += info.size

    wavInfo = WAVInfo(bom)
    wavInfo.data(f, pos)

    outputBuffer[pos:pos + wavInfo.size] = bytes(
        WAVInfo(dest_bom).pack(wavInfo.codec, wavInfo.loop_flag, wavInfo.sample,
                               wavInfo.loop_start, wavInfo.loop_end, wavInfo.reserved))

    pos += wavInfo.size

    channelInfoTable = {}
    sampleData_ref = {}
    ADPCMInfo_ref = {}
    param = {}

    count = struct.unpack(bom + "I", f[pos:pos + 4])[0]
    outputBuffer[pos:pos + 4] = to_bytes(count, 4, dest_bom)
    countPos = pos

    for i in range(1, count + 1):
        pos = countPos + 4
        channelInfoTable[i] = Ref(bom)
        channelInfoTable[i].data(f, pos + 8 * (i - 1))

        outputBuffer[pos + 8 * (i - 1):pos + 8 * (i - 1) + channelInfoTable[i].size] = bytes(
            Ref(dest_bom).pack(channelInfoTable[i].type_, channelInfoTable[i].offset))

        if channelInfoTable[i].offset not in [0, -1]:
            pos = channelInfoTable[i].offset + countPos
            sampleData_ref[i] = Ref(bom)
            sampleData_ref[i].data(f, pos)

            outputBuffer[pos:pos + sampleData_ref[i].size] = bytes(
                Ref(dest_bom).pack(sampleData_ref[i].type_, sampleData_ref[i].offset))

            pos += 8
            ADPCMInfo_ref[i] = Ref(bom)
            ADPCMInfo_ref[i].data(f, pos)

            outputBuffer[pos:pos + ADPCMInfo_ref[i].size] = bytes(
                Ref(dest_bom).pack(ADPCMInfo_ref[i].type_, ADPCMInfo_ref[i].offset))

            if ADPCMInfo_ref[i].offset not in [0, -1]:
                pos = ADPCMInfo_ref[i].offset + pos - 8
                if ADPCMInfo_ref[i].type_ == 0x0300:
                    for i in range(16):
                        i += 1
                        param[i] = struct.unpack(bom + "H", f[pos + 2 * (i - 1):pos + 2 * (i - 1) + 2])[0]
                        outputBuffer[pos + 2 * (i - 1):pos + 2 * (i - 1) + 2] = to_bytes(param[i], 2, dest_bom)

                    pos += 32
                    context = DSPContext(bom)
                    context.data(f, pos)

                    outputBuffer[pos:pos + context.size] = bytes(
                        DSPContext(dest_bom).pack(context.predictor_scale, context.preSample, context.preSample2))

                    pos += context.size
                    loopContext = DSPContext(bom)
                    loopContext.data(f, pos)

                    outputBuffer[pos:pos + loopContext.size] = bytes(
                        DSPContext(dest_bom).pack(loopContext.predictor_scale, loopContext.preSample,
                                                  loopContext.preSample2))

                    pos += loopContext.size
                    pos += 2

                elif ADPCMInfo_ref[i].type_ == 0x0301:
                    context = IMAContext(bom)
                    context.data(f, pos)

                    outputBuffer[pos:pos + context.size] = bytes(
                        IMAContext(dest_bom).pack(context.data_, context.tableIndex))

                    pos += context.size
                    loopContext = IMAContext(bom)
                    loopContext.data(f, pos)

                    outputBuffer[pos:pos + loopContext.size] = bytes(
                        IMAContext(dest_bom).pack(loopContext.data_, loopContext.tableIndex))

                    pos += loopContext.size

    for i in range(1, header.numBlocks + 1):
        if sized_refs[i].offset not in [0, -1]:
            if sized_refs[i].type_ == 0x7001:
                pos = sized_refs[i].offset
                data = BLKHeader(bom)
                data.data(f, pos)
                outputBuffer[pos:pos + data.size] = bytes(BLKHeader(dest_bom).pack(data.magic, data.size_))
                pos += data.size
                data.data_ = f[pos:pos + data.size_ - 8]

                if bom != dest_bom and wavInfo.codec == 1:
                    for i in range(0, len(data.data_), 2):
                        outputBuffer[pos + i:pos + i + 2] = bytes([
                            data.data_[i+1], data.data_[i],
                        ])

                else:
                    outputBuffer[pos:pos + data.size_ - 8] = data.data_

    return outputBuffer


def STMtoWAV(f, magic, dest, dest_bom):
    outputBuffer = bytearray(len(f))

    if f[4:6] == b'\xFF\xFE':
        bom = '<'

    elif f[4:6] == b'\xFE\xFF':
        bom = '>'

    else:
        print("\nInvalid BOM!")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if not dest_bom:
        if dest == "FWAV":
            dest_bom = '>'

        else:
            dest_bom = '<'

    header = Header(bom)
    header.data(f, 0)

    pos = header.size
    sized_refs = {}

    for i in range(1, header.numBlocks + 1):
        sized_refs[i] = Ref(bom)
        sized_refs[i].data(f, pos + 12 * (i - 1))

    if sized_refs[1].type_ != 0x4000 or sized_refs[1].offset in [0, -1]:
        print("\nSomething went wrong!\nError code: 1")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = sized_refs[1].offset

    info = BLKHeader(bom)
    info.data(f, pos)
    pos += 8

    stmInfo_ref = Ref(bom)
    stmInfo_ref.data(f, pos)

    if stmInfo_ref.type_ != 0x4100 or stmInfo_ref.offset in [0, -1]:
        print("\nSomething went wrong!\nError code: 2")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    stmInfo_ref.pos = pos
    pos += stmInfo_ref.size * 2

    channelInfoTable_ref = Ref(bom)
    channelInfoTable_ref.data(f, pos)

    if channelInfoTable_ref.type_ != 0x0101:
        print("\nSomething went wrong!\nError code: 4")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = stmInfo_ref.offset + stmInfo_ref.pos
    stmInfo = STMInfo(bom)
    stmInfo.data(f, pos)

    sampleBlk_size = (stmInfo.sampleBlk_count - 1) * stmInfo.sampleBlk_size + stmInfo.lSampleBlk_size

    wavInfo = WAVInfo(bom)
    wavInfo.codec = stmInfo.codec
    wavInfo.loop_flag = stmInfo.loop_flag
    wavInfo.sample = stmInfo.sample
    wavInfo.loop_start = stmInfo.loop_start
    wavInfo.loop_end = stmInfo.loop_end
    wavInfo.reserved = 0

    otherPos = 0x48 + wavInfo.size

    outputBuffer[0x48:otherPos] = bytes(
        WAVInfo(dest_bom).pack(wavInfo.codec, wavInfo.loop_flag, wavInfo.sample,
                               wavInfo.loop_start, wavInfo.loop_end, wavInfo.reserved))
    channelInfoTable = {}
    sampleData_ref = {}
    ADPCMInfo_ref = {}
    param = {}

    pos = channelInfoTable_ref.offset + stmInfo_ref.pos
    countPos = pos
    otherCountPos = otherPos

    count = struct.unpack(bom + "I", f[pos:pos + 4])[0]
    outputBuffer[otherPos:otherPos + 4] = to_bytes(count, 4, dest_bom)

    otherFstChInfPos = otherCountPos + 4 + count * 8
    otherADPCMInfPos = otherFstChInfPos + count * 0x14

    for i in range(1, count + 1):
        pos = countPos + 4
        otherPos = otherCountPos + 4

        channelInfoTable[i] = Ref(bom)
        channelInfoTable[i].data(f, pos + 8 * (i - 1))

        if channelInfoTable[i].offset in [0, -1]:
            outputBuffer[otherPos + 8 * (i - 1):otherPos + 8 * (i - 1) + channelInfoTable[i].size] = bytes(
                Ref(dest_bom).pack(0x7100, channelInfoTable[i].offset))

        else:
            outputBuffer[otherPos + 8 * (i - 1):otherPos + 8 * (i - 1) + channelInfoTable[i].size] = bytes(
                Ref(dest_bom).pack(0x7100, otherFstChInfPos + 0x14 * (i - 1) - otherCountPos))

            pos = channelInfoTable[i].offset + countPos
            otherPos = otherFstChInfPos + 0x14 * (i - 1)

            sampleData_ref[i] = Ref(bom)

            currsampleBlkSize = sampleBlk_size * (i - 1)
            outputBuffer[otherPos:otherPos + sampleData_ref[i].size] = bytes(
                Ref(dest_bom).pack(0x1F00, 0x18 + align(currsampleBlkSize, 0x20)))

            ADPCMInfo_ref[i] = Ref(bom)
            ADPCMInfo_ref[i].data(f, pos)

            if ADPCMInfo_ref[i].offset in [0, -1]:
                outputBuffer[otherPos + 8:otherPos + 8 + ADPCMInfo_ref[i].size] = bytes(
                    Ref(dest_bom).pack(ADPCMInfo_ref[i].type_, ADPCMInfo_ref[i].offset))

            else:
                pos = ADPCMInfo_ref[i].offset + pos
                if ADPCMInfo_ref[i].type_ == 0x0300:
                    outputBuffer[otherPos + 8:otherPos + 8 + ADPCMInfo_ref[i].size] = bytes(
                        Ref(dest_bom).pack(ADPCMInfo_ref[i].type_, otherADPCMInfPos + 0x2E * (i - 1) - otherPos))

                    otherPos = otherADPCMInfPos + 0x2E * (i - 1)

                    for i in range(16):
                        i += 1
                        param[i] = struct.unpack(bom + "H", f[pos + 2 * (i - 1):pos + 2 * (i - 1) + 2])[0]
                        outputBuffer[otherPos + 2 * (i - 1):otherPos + 2 * (i - 1) + 2] = to_bytes(param[i], 2, dest_bom)

                    pos += 32; otherPos += 32
                    context = DSPContext(bom)
                    context.data(f, pos)

                    outputBuffer[otherPos:otherPos + context.size] = bytes(
                        DSPContext(dest_bom).pack(context.predictor_scale, context.preSample, context.preSample2))

                    pos += context.size; otherPos += context.size
                    loopContext = DSPContext(bom)
                    loopContext.data(f, pos)

                    outputBuffer[otherPos:otherPos + loopContext.size] = bytes(
                        DSPContext(dest_bom).pack(loopContext.predictor_scale, loopContext.preSample,
                                                  loopContext.preSample2))

                    pos += loopContext.size; otherPos += loopContext.size
                    pos += 2; otherPos += 2

                elif ADPCMInfo_ref[i].type_ == 0x0301:
                    outputBuffer[otherPos + 8:otherPos + 8 + ADPCMInfo_ref[i].size] = bytes(
                        Ref(dest_bom).pack(ADPCMInfo_ref[i].type_, otherADPCMInfPos + 8 * (i - 1) - otherPos))

                    otherPos = otherADPCMInfPos + 8 * (i - 1)

                    context = IMAContext(bom)
                    context.data(f, pos)

                    outputBuffer[otherPos:otherPos + context.size] = bytes(
                        IMAContext(dest_bom).pack(context.data_, context.tableIndex))

                    pos += context.size; otherPos += context.size
                    loopContext = IMAContext(bom)
                    loopContext.data(f, pos)

                    outputBuffer[otherPos:otherPos + loopContext.size] = bytes(
                        IMAContext(dest_bom).pack(loopContext.data_, loopContext.tableIndex))

                    pos += loopContext.size; otherPos += loopContext.size

                else:
                    otherPos += 0x14

    dataBlkOffset = align(otherPos, 0x20)
    infoBlkSize = dataBlkOffset - 0x40

    otherDataBlkOffset = 0
    dataSize = 0

    for i in range(1, header.numBlocks + 1):
        if sized_refs[i].offset not in [0, -1]:
            if sized_refs[i].type_ in [0x4002, 0x4004]:
                otherDataBlkOffset = sized_refs[i].offset
                dataBlkHead = BLKHeader(bom)
                dataBlkHead.data(f, otherDataBlkOffset)
                dataSize = dataBlkHead.size_
    
    pos = header.size
    numBlocks = 0

    for i in sized_refs:
        if sized_refs[i].type_ not in [0x4000, 0x4002]:
            continue

        elif sized_refs[i].type_ == 0x4000:
            numBlocks += 1
            outputBuffer[pos:pos + 8] = bytes(Ref(dest_bom).pack(0x7000, 0x40))
            outputBuffer[pos + 8:pos + 12] = struct.pack(dest_bom + "I", infoBlkSize)
            outputBuffer[0x40:0x48] = bytes(BLKHeader(dest_bom).pack(b'INFO', infoBlkSize))

        else:
            if 0 not in [otherDataBlkOffset, dataSize] and otherDataBlkOffset != -1:
                data = f[otherDataBlkOffset + 0x20:otherDataBlkOffset + dataSize]; pos = 0

                blocks = []
                for i in range((stmInfo.sampleBlk_count - 1) * count):
                    blocks.append(data[pos:pos + stmInfo.sampleBlk_size])
                    pos += stmInfo.sampleBlk_size

                for i in range(count):
                    blocks.append(data[pos:pos + stmInfo.lSampleBlk_size])
                    pos += stmInfo.lSampleBlk_padSize

                sampleData = [[blocks[i * count + j] for i in range(stmInfo.sampleBlk_count)] for j in range(count)]
                samples = []

                for channel in sampleData:
                    channelSampleData = b''.join(channel)
                    padding = b'\0' * (align(len(channelSampleData), 0x20) - len(channelSampleData))
                    samples.append(b''.join([channelSampleData, padding]))

                data = b''.join(samples)

                if bom != dest_bom and stmInfo.codec == 1:
                    data_ = bytearray(data)
                    for i in range(0, len(data), 2):
                        data_[i:i + 2] = bytes([
                            data[i+1], data[i],
                        ])

                    data = bytes(data_); del data_

            pos = header.size

            numBlocks += 1
            outputBuffer[pos + 12:pos + 20] = bytes(Ref(dest_bom).pack(0x7001, dataBlkOffset))
            outputBuffer[dataBlkOffset + 0x20:] = data
            outputBuffer[dataBlkOffset:dataBlkOffset + 8] = bytes(BLKHeader(dest_bom).pack(b'DATA', len(outputBuffer) - dataBlkOffset))
            outputBuffer[pos + 20:pos + 24] = struct.pack(dest_bom + "I", len(outputBuffer) - dataBlkOffset)

    dest_ver = {"FWAV": 0x10100, "CWAV": 0x2010000}

    outputBuffer[:header.size] = bytes(
        Header(dest_bom).pack(to_bytes(dest, 4), 0x40, dest_ver[dest], len(outputBuffer), numBlocks,
                              header.reserved))

    outputBuffer[4:6] = (b'\xFE\xFF' if dest_bom == '>' else b'\xFF\xFE')

    return outputBuffer
