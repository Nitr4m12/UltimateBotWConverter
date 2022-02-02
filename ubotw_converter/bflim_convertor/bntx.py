#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# UltimateBoTWConverter
# Original by AboodXD, modified by Nitr4m12
# Copyright © 2018 AboodXD

# This file is part of UltimateBoTWConverter.

# UltimateBoTWConverter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# UltimateBoTWConverter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import struct

from . import dds
from . import globals

class BNTXHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '8sIH2BI2H2I')

    def data(self, data, pos):
        (self.magic,
         self.version,
         self.bom,
         self.alignmentShift,
         self.targetAddrSize,
         self.fileNameAddr,
         self.flag,
         self.firstBlkAddr,
         self.relocAddr,
         self.fileSize) = self.unpack_from(data, pos)


class TexContainer(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4sI5qI4x')

    def data(self, data, pos):
        (self.target,
         self.count,
         self.infoPtrsAddr,
         self.dataBlkAddr,
         self.dictAddr,
         self.memPoolAddr,
         self.memPoolPtr,
         self.baseMemPoolAddr) = self.unpack_from(data, pos)


class BlockHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4s2I4x')

    def data(self, data, pos):
        (self.magic,
         self.nextBlkAddr,
         self.blockSize) = self.unpack_from(data, pos)


class TextureInfo(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '2B4H2x2I3i3I20x3IB3x8q')

    def data(self, data, pos):
        (self.flags,
         self.dim,
         self.tileMode,
         self.swizzle,
         self.numMips,
         self.numSamples,
         self.format_,
         self.accessFlags,
         self.width,
         self.height,
         self.depth,
         self.arrayLength,
         self.textureLayout,
         self.textureLayout2,
         self.imageSize,
         self.alignment,
         self.compSel,
         self.type_,
         self.nameAddr,
         self.parentAddr,
         self.ptrsAddr,
         self.userDataAddr,
         self.texPtr,
         self.texViewPtr,
         self.descSlotDataAddr,
         self.userDictAddr) = self.unpack_from(data, pos)


class TexInfo:
    pass

def _swizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, data, toSwizzle):
    assert 0 <= blockHeightLog2 <= 5
    blockHeight = 1 << blockHeightLog2

    width = DIV_ROUND_UP(width, blkWidth)
    height = DIV_ROUND_UP(height, blkHeight)

    if tileMode == 1:
        pitch = width * bpp

        if roundPitch:
            pitch = round_up(pitch, 32)

        surfSize = pitch * height

    else:
        pitch = round_up(width * bpp, 64)
        surfSize = pitch * round_up(height, blockHeight * 8)

    result = bytearray(surfSize)

    for y in range(height):
        for x in range(width):
            if tileMode == 1:
                pos = y * pitch + x * bpp

            else:
                pos = getAddrBlockLinear(x, y, width, bpp, 0, blockHeight)

            pos_ = (y * width + x) * bpp

            if pos + bpp <= surfSize:
                if toSwizzle:
                    result[pos:pos + bpp] = data[pos_:pos_ + bpp]

                else:
                    result[pos_:pos_ + bpp] = data[pos:pos + bpp]

    return result

def swizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, data):
    return _swizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, bytes(data), 1)

def deswizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, data):
    return _swizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, bytes(data), 0)

def getAddrBlockLinear(x, y, image_width, bytes_per_pixel, base_address, blockHeight):
    """
    From the Tegra X1 TRM
    """
    image_width_in_gobs = DIV_ROUND_UP(image_width * bytes_per_pixel, 64)

    GOB_address = (base_address
                   + (y // (8 * blockHeight)) * 512 * blockHeight * image_width_in_gobs
                   + (x * bytes_per_pixel // 64) * 512 * blockHeight
                   + (y % (8 * blockHeight) // 8) * 512)

    x *= bytes_per_pixel

    Address = (GOB_address + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64
               + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16))

    return Address

def DIV_ROUND_UP(n, d):
    return (n + d - 1) // d

def round_up(x, y):
    return ((x - 1) | (y - 1)) + 1

def pow2_round_up(x):
    x -= 1
    x |= x >> 1
    x |= x >> 2
    x |= x >> 4
    x |= x >> 8
    x |= x >> 16

    return x + 1

def bytes_to_string(data, end=0):
    if not end:
        end = data.find(b'\0')
        if end == -1:
            return data.decode('utf-8')

    return data[:end].decode('utf-8')

def getBlockHeight(height):
    blockHeight = pow2_round_up(height // 8)
    if blockHeight > 16:
        blockHeight = 16

    return blockHeight

def read(file):
    with open(file, "rb") as inf:
        f = inf.read()

    pos = 0

    if f[0xc:0xe] == b'\xFF\xFE':
        bom = '<'

    elif f[0xc:0xe] == b'\xFE\xFF':
        bom = '>'

    else:
        print("Invalid BOM!")
        return False

    header = BNTXHeader(bom)
    header.data(f, pos)
    pos += header.size

    if header.magic != b'BNTX\0\0\0\0':
        print("Invalid file header!")
        return False

    fnameLen = struct.unpack(bom + 'H', f[header.fileNameAddr - 2:header.fileNameAddr])[0]
    fname = bytes_to_string(f[header.fileNameAddr:header.fileNameAddr + fnameLen], fnameLen)

    texContainer = TexContainer(bom)
    texContainer.data(f, pos)
    pos += texContainer.size

    if texContainer.target not in [b'NX  ', b'Gen ']:
        print("Unsupported target platform!")
        return False

    target = 0 if texContainer.target == b'Gen ' else 1

    textures = []
    texNames = []
    texSizes = []

    for i in range(texContainer.count):
        pos = struct.unpack(bom + 'q', f[texContainer.infoPtrsAddr + i * 8:texContainer.infoPtrsAddr + i * 8 + 8])[0]

        infoHeader = BlockHeader(bom)
        infoHeader.data(f, pos)
        pos += infoHeader.size

        info = TextureInfo(bom)
        info.data(f, pos)

        if infoHeader.magic != b'BRTI':
            continue

        nameLen = struct.unpack(bom + 'H', f[info.nameAddr:info.nameAddr + 2])[0]
        name = bytes_to_string(f[info.nameAddr + 2:info.nameAddr + 2 + nameLen], nameLen)

        compSel = []
        compSel2 = []
        for i in range(4):
            value = (info.compSel >> (8 * (3 - i))) & 0xff
            compSel2.append(value)
            if value == 0:
                value = 5 - len(compSel)

            compSel.append(value)

        if info.type_ not in globals.types:
            globals.types[info.type_] = "Unknown"

        dataAddr = struct.unpack(bom + 'q', f[info.ptrsAddr:info.ptrsAddr + 8])[0]
        mipOffsets = {0: 0}

        for i in range(1, info.numMips):
            mipOffset = struct.unpack(bom + 'q', f[info.ptrsAddr + (i * 8):info.ptrsAddr + (i * 8) + 8])[0]
            mipOffsets[i] = mipOffset - dataAddr

        tex = TexInfo()

        tex.infoAddr = pos
        tex.info = info
        tex.bom = bom
        tex.target = target

        tex.name = name

        tex.readTexLayout = info.flags & 1
        tex.sparseBinding = info.flags >> 1
        tex.sparseResidency = info.flags >> 2
        tex.dim = info.dim
        tex.tileMode = info.tileMode
        tex.numMips = info.numMips
        tex.width = info.width
        tex.height = info.height
        tex.format = info.format_
        tex.arrayLength = info.arrayLength
        tex.blockHeightLog2 = info.textureLayout & 7
        tex.imageSize = info.imageSize

        tex.compSel = compSel
        tex.compSel2 = compSel2

        tex.alignment = info.alignment
        tex.type = info.type_

        tex.mipOffsets = mipOffsets
        tex.dataAddr = dataAddr

        tex.data = f[dataAddr:dataAddr + info.imageSize]

        textures.append(tex)
        texNames.append(name)
        texSizes.append(info.imageSize)

    globals.fileData = bytearray(f)
    globals.texSizes = texSizes

    return fname, texContainer.target.decode('utf-8'), textures, texNames


def decode(tex):
    if (tex.format >> 8) in globals.blk_dims:
        blkWidth, blkHeight = globals.blk_dims[tex.format >> 8]

    else:
        blkWidth, blkHeight = 1, 1

    bpp = globals.bpps[tex.format >> 8]

    result_ = []

    linesPerBlockHeight = (1 << tex.blockHeightLog2) * 8
    blockHeightShift = 0

    for mipLevel in tex.mipOffsets:
        width = max(1, tex.width >> mipLevel)
        height = max(1, tex.height >> mipLevel)

        size = DIV_ROUND_UP(width, blkWidth) * DIV_ROUND_UP(height, blkHeight) * bpp

        if pow2_round_up(DIV_ROUND_UP(height, blkHeight)) < linesPerBlockHeight:
            blockHeightShift += 1

        mipOffset = tex.mipOffsets[mipLevel]

        result = swizzle.deswizzle(
            width, height, blkWidth, blkHeight, tex.target, bpp, tex.tileMode,
            max(0, tex.blockHeightLog2 - blockHeightShift), tex.data[mipOffset:],
        )

        result_.append(result[:size])

    return result_, blkWidth, blkHeight

def getCurrentMipOffset_Size(width, height, blkWidth, blkHeight, bpp, currLevel):
    offset = 0

    for mipLevel in range(currLevel):
        width_ = DIV_ROUND_UP(max(1, width >> mipLevel), blkWidth)
        height_ = DIV_ROUND_UP(max(1, height >> mipLevel), blkHeight)

        offset += width_ * height_ * bpp

    width_ = DIV_ROUND_UP(max(1, width >> currLevel), blkWidth)
    height_ = DIV_ROUND_UP(max(1, height >> currLevel), blkHeight)

    size = width_ * height_ * bpp

    return offset, size


def inject(tex, tileMode, SRGB, sparseBinding, sparseResidency, importMips, oldImageSize, f):
    width, height, format_, fourcc, dataSize, compSel, numMips, data = dds.readDDS(f, SRGB)

    if 0 in [width, dataSize] and data == []:
        print("Unsupported DDS file!")
        return False

    if format_ not in globals.formats:
        print("Unsupported DDS format!")
        return False

    if not importMips:
        numMips = 1

    else:
        if tex.numMips < numMips + 1:
            print("This DDS file has more mipmaps (%d) than the original image (%d)!\n%d mipmaps will be imported." % (numMips, tex.numMips - 1, tex.numMips - 1))

        numMips = max(1, min(tex.numMips, numMips + 1))

    if tileMode == 1:
        alignment = 1

    else:
        alignment = 512

    if (format_ >> 8) in globals.blk_dims:
        blkWidth, blkHeight = globals.blk_dims[format_ >> 8]

    else:
        blkWidth, blkHeight = 1, 1

    bpp = globals.bpps[format_ >> 8]

    if tileMode == 1:
        blockHeight = 1
        blockHeightLog2 = 0

        linesPerBlockHeight = 1

    else:
        blockHeight = getBlockHeight(DIV_ROUND_UP(height, blkHeight))
        blockHeightLog2 = len(bin(blockHeight)[2:]) - 1

        linesPerBlockHeight = blockHeight * 8

    blockHeightShift = 0
    surfSize = 0

    for mipLevel in range(numMips):
        width_ = DIV_ROUND_UP(max(1, width >> mipLevel), blkWidth)
        height_ = DIV_ROUND_UP(max(1, height >> mipLevel), blkHeight)

        dataAlignBytes = b'\0' * (round_up(surfSize, alignment) - surfSize)
        surfSize += len(dataAlignBytes)

        if tileMode == 1:
            pitch = width_ * bpp

            if tex.target == 1:
                pitch = round_up(pitch, 32)

            surfSize += pitch * height_

        else:
            if pow2_round_up(height_) < linesPerBlockHeight:
                blockHeightShift += 1

            pitch = round_up(width_ * bpp, 64)
            surfSize += pitch * round_up(height_, max(1, blockHeight >> blockHeightShift) * 8)

    if surfSize > oldImageSize:
        print('A bflim exported with a big DDS filesize!\nUsing tiling mode "Linear"...')
        return inject(tex, 1, SRGB, sparseBinding, sparseResidency, importMips, oldImageSize, f)

    result = []
    surfSize = 0
    mipOffsets = {}
    blockHeightShift = 0

    for mipLevel in range(numMips):
        offset, size = getCurrentMipOffset_Size(width, height, blkWidth, blkHeight, bpp, mipLevel)
        data_ = data[offset:offset + size]

        width_ = max(1, width >> mipLevel)
        height_ = max(1, height >> mipLevel)

        width__ = DIV_ROUND_UP(width_, blkWidth)
        height__ = DIV_ROUND_UP(height_, blkHeight)

        dataAlignBytes = b'\0' * (round_up(surfSize, alignment) - surfSize)
        surfSize += len(dataAlignBytes)
        mipOffsets[mipLevel] = surfSize

        if tileMode == 1:
            pitch = width__ * bpp

            if tex.target == 1:
                pitch = round_up(pitch, 32)

            surfSize += pitch * height__

        else:
            if pow2_round_up(height__) < linesPerBlockHeight:
                blockHeightShift += 1

            pitch = round_up(width__ * bpp, 64)
            surfSize += pitch * round_up(height__, max(1, blockHeight >> blockHeightShift) * 8)

        result.append(bytearray(dataAlignBytes) + swizzle(
            width_, height_, blkWidth, blkHeight, tex.target, bpp, tileMode,
            max(0, blockHeightLog2 - blockHeightShift), data_,
        ))

    tex.readTexLayout = 1 if tileMode == 0 else 0
    tex.sparseBinding = sparseBinding
    tex.sparseResidency = sparseResidency
    tex.dim = 2
    tex.tileMode = tileMode
    tex.numMips = numMips
    tex.mipOffsets = mipOffsets
    tex.width = width
    tex.height = height
    tex.format = format_
    tex.accessFlags = 0x20
    tex.arrayLength = 1
    tex.blockHeightLog2 = blockHeightLog2
    tex.imageSize = surfSize
    tex.compSel = compSel; tex.compSel.reverse()
    tex.compSel2 = tex.compSel.copy()
    tex.alignment = alignment
    tex.type = 1
    tex.data = b''.join(result)

    return tex


def writeTex(file, tex, oldImageSize, oldNumMips):
    compSel = tex.compSel[0] << 24 | tex.compSel[1] << 16 | tex.compSel[2] << 8 | tex.compSel[3]

    if not tex.readTexLayout:
        textureLayout = 0

    else:
        textureLayout = tex.sparseResidency << 5 | tex.sparseBinding << 4 | tex.blockHeightLog2

    infoHead = TextureInfo(tex.bom).pack(
        tex.sparseResidency << 2 | tex.sparseBinding << 1 | tex.readTexLayout,
        tex.dim,
        tex.tileMode,
        tex.info.swizzle,
        tex.numMips,
        tex.info.numSamples,
        tex.format,
        tex.info.accessFlags,
        tex.width,
        tex.height,
        tex.info.depth,
        tex.arrayLength,
        textureLayout,
        tex.info.textureLayout2,
        tex.imageSize,
        tex.alignment,
        compSel,
        tex.type,
        tex.info.nameAddr,
        tex.info.parentAddr,
        tex.info.ptrsAddr,
        tex.info.userDataAddr,
        tex.info.texPtr,
        tex.info.texViewPtr,
        tex.info.descSlotDataAddr,
        tex.info.userDictAddr,
    )

    globals.fileData[tex.infoAddr:tex.infoAddr + 144] = infoHead

    ptrs = bytearray(oldNumMips * 8)

    for mipLevel in tex.mipOffsets:
        mipOffset = tex.mipOffsets[mipLevel]
        ptrs[mipLevel * 8:mipLevel * 8 + 8] = struct.pack(tex.bom + 'q', tex.dataAddr + mipOffset)

    globals.fileData[tex.info.ptrsAddr:tex.info.ptrsAddr + oldNumMips * 8] = ptrs

    data = b''.join([tex.data, b'\0' * (oldImageSize - tex.imageSize)])
    globals.fileData[tex.dataAddr:tex.dataAddr + oldImageSize] = data

    with open(file, "wb+") as out:
        out.write(globals.fileData)
