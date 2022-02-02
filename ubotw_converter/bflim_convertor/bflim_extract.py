#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# UltimateBoTWConverter
# Original by AboodXD, modified by Nitr4m12
# Copyright © 2016-2019 AboodXD

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

"""bflim_extract.py: Decode and encode BFLIM files."""

import os
import struct
import sys
import time

from . import addrlib
from . import dds

__author__ = "AboodXD"
__copyright__ = "Copyright 2016-2019 AboodXD"
__credits__ = ["AboodXD", "AMD", "Exzap"]

formats = {
    0x00000000: 'GX2_SURFACE_FORMAT_INVALID',
    0x0000001a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM',
    0x0000041a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB',
    0x00000019: 'GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM',
    0x00000008: 'GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM',
    0x0000000a: 'GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM',
    0x0000000b: 'GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM',
    0x00000001: 'GX2_SURFACE_FORMAT_TC_R8_UNORM',
    0x00000007: 'GX2_SURFACE_FORMAT_TC_R8_G8_UNORM',
    0x00000002: 'GX2_SURFACE_FORMAT_TC_R4_G4_UNORM',
    0x00000031: 'GX2_SURFACE_FORMAT_T_BC1_UNORM',
    0x00000431: 'GX2_SURFACE_FORMAT_T_BC1_SRGB',
    0x00000032: 'GX2_SURFACE_FORMAT_T_BC2_UNORM',
    0x00000432: 'GX2_SURFACE_FORMAT_T_BC2_SRGB',
    0x00000033: 'GX2_SURFACE_FORMAT_T_BC3_UNORM',
    0x00000433: 'GX2_SURFACE_FORMAT_T_BC3_SRGB',
    0x00000034: 'GX2_SURFACE_FORMAT_T_BC4_UNORM',
    0x00000035: 'GX2_SURFACE_FORMAT_T_BC5_UNORM',
}

BCn_formats = [0x31, 0x431, 0x32, 0x432, 0x33, 0x433, 0x34, 0x35]


class FLIMData:
    pass


class FLIMHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4s2H2IH2x')

    def data(self, data, pos):
        (self.magic,
         self.endian,
         self.size_,
         self.version,
         self.fileSize,
         self.numBlocks) = self.unpack_from(data, pos)


class imagHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4sI3H2BI')

    def data(self, data, pos):
        (self.magic,
         self.infoSize,
         self.width,
         self.height,
         self.alignment,
         self.format_,
         self.swizzle_tileMode,
         self.imageSize) = self.unpack_from(data, pos)


def computeSwizzleTileMode(tileModeAndSwizzlePattern):
    if isinstance(tileModeAndSwizzlePattern, int):
        tileMode = tileModeAndSwizzlePattern & 0x1F
        swizzlePattern = ((tileModeAndSwizzlePattern >> 5) & 7) << 8
        if tileMode not in [1, 2, 3, 16]:
            swizzlePattern |= 0xd0000

        return swizzlePattern, tileMode

    return tileModeAndSwizzlePattern[0] << 5 | tileModeAndSwizzlePattern[1]  # swizzlePattern << 5 | tileMode


def readFLIM(f):
    flim = FLIMData()

    pos = len(f) - 0x28

    if f[pos + 4:pos + 6] == b'\xFF\xFE':
        bom = '<'

    elif f[pos + 4:pos + 6] == b'\xFE\xFF':
        bom = '>'

    header = FLIMHeader(bom)
    header.data(f, pos)

    if header.magic != b'FLIM':
        raise ValueError("Invalid file header!")

    pos += header.size

    info = imagHeader(bom)
    info.data(f, pos)

    if info.magic != b'imag':
        raise ValueError("Invalid imag header!")

    flim.width = info.width
    flim.height = info.height

    if info.format_ == 0x00:
        flim.format = 0x01
        flim.compSel = [0, 0, 0, 5]

    elif info.format_ == 0x01:
        flim.format = 0x01
        flim.compSel = [5, 5, 5, 0]

    elif info.format_ == 0x02:
        flim.format = 0x02
        flim.compSel = [0, 0, 0, 1]

    elif info.format_ == 0x03:
        flim.format = 0x07
        flim.compSel = [0, 0, 0, 1]

    elif info.format_ in [0x05, 0x19]:
        flim.format = 0x08
        flim.compSel = [2, 1, 0, 5]

    elif info.format_ == 0x06:
        flim.format = 0x1a
        flim.compSel = [0, 1, 2, 5]

    elif info.format_ == 0x07:
        flim.format = 0x0a
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x08:
        flim.format = 0x0b
        flim.compSel = [2, 1, 0, 3]

    elif info.format_ == 0x09:
        flim.format = 0x1a
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x0a:
        flim.format = 0x31
        flim.format_ = "ETC1"
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x0C:
        flim.format = 0x31
        flim.format_ = "BC1"
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x0D:
        flim.format = 0x32
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x0E:
        flim.format = 0x33
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ in [0x0F, 0x10]:
        flim.format = 0x34
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x11:
        flim.format = 0x35
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x14:
        flim.format = 0x41a
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x15:
        flim.format = 0x431
        flim.format_ = "BC1"
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x16:
        flim.format = 0x432
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x17:
        flim.format = 0x433
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x18:
        flim.format = 0x19
        flim.compSel = [0, 1, 2, 3]

    else:
        print("")
        print("Unsupported texture format: " + hex(info.format_))
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    flim.imageSize = info.imageSize

    # Calculate swizzle and tileMode
    flim.swizzle, flim.tileMode = computeSwizzleTileMode(info.swizzle_tileMode)
    if not 1 <= flim.tileMode <= 16:
            print("")
            print("Invalid tileMode!")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    flim.alignment = info.alignment

    surfOut = addrlib.getSurfaceInfo(flim.format, flim.width, flim.height, 1, 1, flim.tileMode, 0, 0)

    tilingDepth = surfOut.depth
    if surfOut.tileMode == 3:
        tilingDepth //= 4

    if tilingDepth != 1:
        print("")
        print("Unsupported depth!")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    flim.pitch = surfOut.pitch

    flim.data = f[:info.imageSize]

    flim.surfOut = surfOut

    if flim.format in BCn_formats:
        flim.realSize = ((flim.width + 3) >> 2) * ((flim.height + 3) >> 2) * (
            addrlib.surfaceGetBitsPerPixel(flim.format) // 8)

    else:
        flim.realSize = flim.width * flim.height * (addrlib.surfaceGetBitsPerPixel(flim.format) // 8)

    return flim


def get_deswizzled_data(flim):
    if flim.format == 0x01:
        format_ = 61

    elif flim.format == 0x02:
        format_ = 112

    elif flim.format == 0x07:
        format_ = 49

    elif flim.format == 0x08:
        format_ = 85

    elif flim.format == 0x0a:
        format_ = 86

    elif flim.format == 0x0b:
        format_ = 115

    elif flim.format in [0x1a, 0x41a]:
        format_ = 28

    elif flim.format == 0x19:
        format_ = 24

    elif flim.format in [0x31, 0x431]:
        format_ = flim.format_

    elif flim.format in [0x32, 0x432]:
        format_ = "BC2"

    elif flim.format in [0x33, 0x433]:
        format_ = "BC3"

    elif flim.format == 0x34:
        format_ = "BC4U"

    elif flim.format == 0x35:
        format_ = "BC5U"

    result = addrlib.deswizzle(flim.width, flim.height, 1, flim.format, 0, 1, flim.surfOut.tileMode,
                               flim.swizzle, flim.pitch, flim.surfOut.bpp, 0, 0, flim.data)

    if flim.format in BCn_formats:
        size = ((flim.width + 3) >> 2) * ((flim.height + 3) >> 2) * (addrlib.surfaceGetBitsPerPixel(flim.format) >> 3)

    else:
        size = flim.width * flim.height * (addrlib.surfaceGetBitsPerPixel(flim.format) >> 3)

    result = result[:size]

    hdr = dds.generateHeader(1, flim.width, flim.height, format_, flim.compSel, size, flim.format in BCn_formats)

    return hdr, result
