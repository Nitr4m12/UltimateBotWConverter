# -*- coding: utf-8 -*-
#!/usr/bin/python3

import struct

class Header(struct.Struct):
	# Bars Header
	def __init__(self, bom):
		super().__init__(bom + "4sI2HI")

	def data(self, data, pos):
		(self.magic,
		 self.size_,
		 self.endian,
		 self.reserved,
		 self.count) = self.unpack_from(data, pos)

class AudioHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4s2xH2I2H')

    def data(self, data, pos):
        (self.magic,
         self.size_,
         self.version,
         self.fileSize,
         self.numBlocks,
         self.reserved) = self.unpack_from(data, pos)

class TRKStruct(struct.Struct):
	def __init__(self, bom, count):
		super().__init__(f"{bom}{count*2}I")
	
	def data(self, data, pos):
		self.offsets = self.unpack_from(data, pos)

class Unknown(struct.Struct):
	# Unknown bytes, but I'm guessing track info
	def __init__(self, bom, count):
		super().__init__(f'{bom}{count}I')

	def data(self, data, pos):
		self.unknown = self.unpack_from(data, pos)

class AMTAHeader(struct.Struct):
	# Amta Header
	def __init__(self, bom):
		super().__init__(bom + "4s2H5I")

	def data(self, data, pos):
		(self.magic,
		 self.endian,
		 self.reserved,
		 self.length,
		 self.data_offset,
		 self.mark_offset,
		 self.ext_offset,
		 self.strg_offset) = self.unpack_from(data, pos)

class BLKHeader(struct.Struct):
	def __init__(self, bom):
		super().__init__(bom + "4sI")

	def data(self, data, pos):
		(self.magic,
		 self.size_) = self.unpack_from(data, pos)

class AMTASubHeader(struct.Struct):
	# Header for DATA, MARK, EXT_ and STRG sections
	def __init__(self, bom):
		super().__init__(bom + "4sI")

	def data(self, data, pos):
		(self.magic,
		 self.length) = self.unpack_from(data, pos)

class FWAVHeader(struct.Struct):
	def __init__(self, bom):
		super().__init__(bom + "4s8xI8x2I32x")

	def data(self, data, pos):
		(self.magic,
		 self.size_,
		 self.info_offset,
		 self.data_offset) = self.unpack_from(data, pos)

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

class WAVInfo(struct.Struct):  # Wave Info
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
	# Context table for DSP formats
    def __init__(self, bom):
        super().__init__(bom + '3H')

    def data(self, data, pos):
        (self.predictor_scale,
         self.preSample,
         self.preSample2) = self.unpack_from(data, pos)


class IMAContext(struct.Struct): 
	# Context table for IMA formats
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

def fix_bfstp(outputBuffer: bytearray, pos: int, dest_bom: str, sized_refs):

	# Write the data to the PDAT header
    pdat_header_len: int = 0x20 if dest_bom == ">" else 0x40
    pdat_offset: int = pos - 0x8
    pdat_len: int = int.from_bytes(outputBuffer[pdat_offset + 4:pdat_offset + 8], "little" if dest_bom == "<" else "big") - pdat_header_len // 2
    outputBuffer[pdat_offset + 0x4:pdat_offset + 0x8] = struct.pack(dest_bom + "I", pdat_len + pdat_header_len)
    outputBuffer[pdat_offset + 0x8:pdat_offset + 0xC] = b'\x00\x00\x00\x01' if dest_bom == ">" else b'\x01\x00\x00\x00'
    outputBuffer[pdat_offset + 0x10:pdat_offset + 0x14] = struct.pack(dest_bom + "I", pdat_len) 
    # just before the data in PDAT starts - usually stands 0x14 for WiiU (or Big Endian) and 0x54 for Switch (or Little Endian)
    outputBuffer[pdat_offset + 0x1C:pdat_offset + 0x20] = struct.pack(dest_bom + "I", 0x14 if dest_bom == ">" else 0x34)
	
    # since switch PDAT header is twice as big (32 vs 64), it needs to have the second half filled with zeros
    if dest_bom == "<": 
        for _ in range(0x20):
            outputBuffer.insert(pdat_offset + 0x20, 0)

    del outputBuffer[pdat_offset + pdat_header_len + pdat_len:]

    # write the offset to the PDAT section and it's whole length, and fill the rest of the header with 0
    outputBuffer[0x24:0x2C] = struct.pack(dest_bom + "2I", pdat_offset, pdat_len + pdat_header_len)
    outputBuffer[0x2C:sized_refs[1].offset] = [0]*0x14

    # write the whole file size here
    outputBuffer[0xC:0x10] = struct.pack(dest_bom + "I", len(outputBuffer))

# Magic numbers, commonly known as "headers"
MAGICS = [b"DATA", b"MARK", b"EXT_", b"STRG"]
BARS_HEADER = b"BARS"
AMTA_HEADER = b"AMTA"
FWAV_HEADERS = [b"FWAV", b"FSTP"]


# Supported formats by the converter
supp_STM = ["FSTM", "CSTM", "FSTP"]
supp_WAV = ["FWAV", "CWAV"]