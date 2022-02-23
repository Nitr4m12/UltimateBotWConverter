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

try:
    from .utils import *

except ModuleNotFoundError:
    from bars_py.utils import *

def conv_file(f, dest, dest_bom):
    # Convert embedded files, usually inside a bars file
    magic = bytes_to_string(f[:4])
    if magic in supp_STM and dest in supp_STM:
        outputBuffer = STMtoSTM(f, magic, dest, dest_bom)

    elif magic in supp_WAV and dest in supp_WAV:
        outputBuffer = WAVtoWAV(f, magic, dest, dest_bom)

    else:
        print("\nUnsupported file format!")
    
    return outputBuffer

def STMtoSTM(f, magic, dest, dest_bom):
    outputBuffer = bytearray(len(f))
    pos = 0

    if f[4:6] == b'\xFF\xFE':
        bom = '<'

    elif f[4:6] == b'\xFE\xFF':
        bom = '>'

    else:
        print("\nInvalid BOM!")
        return False

    if not dest_bom:
        if dest in ["FSTM", "FSTP"]:
            dest_bom = '>'

        else:
            dest_bom = '<'

    header = AudioHeader(bom)
    header.data(f, pos)

    curr = magic

    dest_ver = {"FSTM": 0x40000, "CSTM": 0x2020000, "FSTP": 0x20100}
    if magic == dest:
        dest_ver[dest] = header.version

    outputBuffer[pos:pos + header.size] = bytes(
        AudioHeader(dest_bom).pack(to_bytes(dest, 4), header.size_, dest_ver[dest], header.fileSize, header.numBlocks,
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
        print("\nSomething went wrong!")
        return False

    pos = sized_refs[1].offset

    info = BLKHeader(bom)
    info.data(f, pos)

    outputBuffer[pos:pos + info.size] = bytes(BLKHeader(dest_bom).pack(info.magic, info.size_))
    pos += info.size

    stmInfo_ref = Ref(bom)
    stmInfo_ref.data(f, pos)

    outputBuffer[pos:pos + stmInfo_ref.size] = bytes(Ref(dest_bom).pack(stmInfo_ref.type_, stmInfo_ref.offset))

    if stmInfo_ref.type_ != 0x4100 or stmInfo_ref.offset in [0, -1]:
        print("\nSomething went wrong!")
        return False

    stmInfo_ref.pos = pos
    pos += stmInfo_ref.size

    trkInfoTable_ref = Ref(bom)
    trkInfoTable_ref.data(f, pos)

    outputBuffer[pos:pos + trkInfoTable_ref.size] = bytes(
        Ref(dest_bom).pack(trkInfoTable_ref.type_, trkInfoTable_ref.offset))

    if trkInfoTable_ref.type_ not in [0x0101, 0]:
        print("\nSomething went wrong!")
        return False

    pos += trkInfoTable_ref.size

    channelInfoTable_ref = Ref(bom)
    channelInfoTable_ref.data(f, pos)

    outputBuffer[pos:pos + channelInfoTable_ref.size] = bytes(
        Ref(dest_bom).pack(channelInfoTable_ref.type_, channelInfoTable_ref.offset))

    if channelInfoTable_ref.type_ != 0x0101:
        print("\nSomething went wrong!")
        return False

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
                    fix_bfstp(outputBuffer, pos, dest_bom, sized_refs)

    return outputBuffer


def WAVtoWAV(f, magic, dest, dest_bom):
    outputBuffer = bytearray(len(f))
    pos = 0

    if f[4:6] == b'\xFF\xFE':
        bom = '<'

    elif f[4:6] == b'\xFE\xFF':
        bom = '>'

    else:
        print("\nInvalid BOM found!")

    if dest_bom == '':
        if dest == "FWAV":
            dest_bom = '>'

        else:
            dest_bom = '<'

    header = AudioHeader(bom)
    header.data(f, pos)

    dest_ver = {"FWAV": 0x10100, "CWAV": 0x2010000}
    if magic == dest:
        dest_ver[dest] = header.version

    outputBuffer[pos:pos + header.size] = bytes(
        AudioHeader(dest_bom).pack(to_bytes(dest, 4), header.size_, dest_ver[dest], header.fileSize, header.numBlocks,
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
        print("\nSomething went wrong")
        return False

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