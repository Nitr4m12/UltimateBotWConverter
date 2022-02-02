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

Version = '0.1'

formats = {
    0x0101: 'R4_G4_UNORM',
    0x0201: 'R8_UNORM',
    0x0301: 'R4_G4_B4_A4_UNORM',
    0x0401: 'A4_B4_G4_R4_UNORM',
    0x0501: 'R5_G5_B5_A1_UNORM',
    0x0601: 'A1_B5_G5_R5_UNORM',
    0x0701: 'R5_G6_B5_UNORM',
    0x0801: 'B5_G6_R5_UNORM',
    0x0901: 'R8_G8_UNORM',
    0x0b01: 'R8_G8_B8_A8_UNORM',
    0x0b06: 'R8_G8_B8_A8_SRGB',
    0x0c01: 'B8_G8_R8_A8_UNORM',
    0x0c06: 'B8_G8_R8_A8_SRGB',
    0x0e01: 'R10_G10_B10_A2_UNORM',
    0x1a01: 'BC1_UNORM',
    0x1a06: 'BC1_SRGB',
    0x1b01: 'BC2_UNORM',
    0x1b06: 'BC2_SRGB',
    0x1c01: 'BC3_UNORM',
    0x1c06: 'BC3_SRGB',
    0x1d01: 'BC4_UNORM',
    0x1d02: 'BC4_SNORM',
    0x1e01: 'BC5_UNORM',
    0x1e02: 'BC5_SNORM',
    0x1f05: 'BC6_FLOAT',
    0x1f0a: 'BC6_UFLOAT',
    0x2001: 'BC7_UNORM',
    0x2006: 'BC7_SRGB',
    0x2d01: 'ASTC_4x4_UNORM',
    0x2d06: 'ASTC_4x4_SRGB',
    0x2e01: 'ASTC_5x4_UNORM',
    0x2e06: 'ASTC_5x4_SRGB',
    0x2f01: 'ASTC_5x5_UNORM',
    0x2f06: 'ASTC_5x5_SRGB',
    0x3001: 'ASTC_6x5_UNORM',
    0x3006: 'ASTC_6x5_SRGB',
    0x3101: 'ASTC_6x6_UNORM',
    0x3106: 'ASTC_6x6_SRGB',
    0x3201: 'ASTC_8x5_UNORM',
    0x3206: 'ASTC_8x5_SRGB',
    0x3301: 'ASTC_8x6_UNORM',
    0x3306: 'ASTC_8x6_SRGB',
    0x3401: 'ASTC_8x8_UNORM',
    0x3406: 'ASTC_8x8_SRGB',
    0x3501: 'ASTC_10x5_UNORM',
    0x3506: 'ASTC_10x5_SRGB',
    0x3601: 'ASTC_10x6_UNORM',
    0x3606: 'ASTC_10x6_SRGB',
    0x3701: 'ASTC_10x8_UNORM',
    0x3706: 'ASTC_10x8_SRGB',
    0x3801: 'ASTC_10x10_UNORM',
    0x3806: 'ASTC_10x10_SRGB',
    0x3901: 'ASTC_12x10_UNORM',
    0x3906: 'ASTC_12x10_SRGB',
    0x3a01: 'ASTC_12x12_UNORM',
    0x3a06: 'ASTC_12x12_SRGB',
    0x3b01: 'B5_G5_R5_A1_UNORM',
}

accessFlags = {
    0: "Read", 1: "Write",
    4: "VertexBuffer", 8: "IndexBuffer",
    0x10: "ConstantBuffer", 0x20: "Texture",
    0x40: "UnorderedAccessBuffer", 0x80: "ColorBuffer",
    0x100: "DepthStencil", 0x200: "IndirectBuffer",
    0x400: "ScanBuffer", 0x800: "QueryBuffer",
    0x1000: "Descriptor", 0x2000: "ShaderCode",
    0x4000: "Image",
}

types = {
    0: "1D", 1: "2D", 2: "3D",
    3: "Cube", 4: "1D Array", 5: "2D Array",
    6: "2D Multisample", 7: "2D Multisample Array",
    8: "Cube Array",
}

tileModes = {
    0: "Optimal",
    1: "Linear",
}

compSels = {
    0: "Zero", 1: "One",
    2: "Red", 3: "Green",
    4: "Blue", 5: "Alpha",
}

BCn_formats = [
    0x1a, 0x1b, 0x1c, 0x1d,
    0x1e, 0x1f, 0x20,
]

ASTC_formats = [
    0x2d, 0x2e, 0x2f, 0x30,
    0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38,
    0x39, 0x3a,
]

blk_dims = {  # format -> (blkWidth, blkHeight)
    0x1a: (4, 4), 0x1b: (4, 4), 0x1c: (4, 4),
    0x1d: (4, 4), 0x1e: (4, 4), 0x1f: (4, 4),
    0x20: (4, 4), 0x2d: (4, 4), 0x2e: (5, 4),
    0x2f: (5, 5), 0x30: (6, 5),
    0x31: (6, 6), 0x32: (8, 5),
    0x33: (8, 6), 0x34: (8, 8),
    0x35: (10, 5), 0x36: (10, 6),
    0x37: (10, 8), 0x38: (10, 10),
    0x39: (12, 10), 0x3a: (12, 12),
}

bpps = {  # format -> bytes_per_pixel
    0x01: 0x01, 0x02: 0x01, 0x03: 0x02, 0x05: 0x02, 0x07: 0x02,
    0x09: 0x02, 0x0b: 0x04, 0x0e: 0x04, 0x1a: 0x08, 0x1b: 0x10,
    0x1c: 0x10, 0x1d: 0x08, 0x1e: 0x10, 0x1f: 0x10, 0x20: 0x10,
    0x2d: 0x10, 0x2e: 0x10, 0x2f: 0x10, 0x30: 0x10, 0x31: 0x10,
    0x32: 0x10, 0x33: 0x10, 0x34: 0x10, 0x35: 0x10, 0x36: 0x10,
    0x37: 0x10, 0x38: 0x10, 0x39: 0x10, 0x3a: 0x10,
}


fileData = bytearray()
texSizes = []
