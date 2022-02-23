# -*- coding: utf-8 -*-
#!/usr/bin/python3

"""bars.py: a python module to work with the BARS format"""

__author__ = "Nitr4m12(based on bars_convertor.py from Peter Wunder (@SamusAranX))"
__license__ = "GPL-3.0"

try:
	from .utils import *
except ModuleNotFoundError:
	from bars_py.utils import *

from typing import List, Dict, Tuple, Any

def plural_s(n):
	return "s" if n != 1 else ""

def get_bars_tracks(bars):

	"""
	Gets the embedded tracks of a bars file, alongside their respective
	offsets, and return two dictionaries: one containing the tracks and 
	another one containing each track's offset, each using the respective
	track's name as keys.
	"""

	if bars[0x8:0xA] == b"\xFF\xFE":
		bom = '<'
	else:
		bom = '>'

	# Set our position to the start of the file
	file_size: int = len(bars)
	pos: int = 0

	# Create a structure for the header
	header: Header = Header(bom)
	header.data(bars, pos)

	# Check for an invalid file
	if header.magic != b"BARS":
		print('Invalid BARS file!')
		return False

	# Offset an amount of header.size
	pos += header.size + header.count * 4

	# Create a structure for the track structure
	track_struct: TRKStruct = TRKStruct(bom, header.count)
	track_struct.data(bars, pos)

	tracks_data = []
	track_names = []
	track_offsets = []

	# Look for the track name
	for i in range(header.count):
		# Get AMTA offset
		pos = track_struct.offsets[i * 2] 

		# Create a structure for the AMTA header
		amta: AMTAHeader = AMTAHeader(bom)
		amta.data(bars, pos)

		if amta.magic != AMTA_HEADER:
			print('Invalid AMTA Header!')
			return False

		# Offset an amount of amta.size
		pos += amta.size

		for j in MAGICS:
			data: AMTASubHeader = AMTASubHeader(bom)
			data.data(bars, pos)
			pos += data.size
			if j != b'STRG':
				pos += data.length
			else:	
				data.data_ = bars[pos:pos + data.length]
				track_names.append((data.data_).decode('utf-8').split('\0')[0])

	for i in range(header.count):
		# Get the offset of our track
		pos = track_struct.offsets[i * 2 + 1] 

		if pos >= header.size_: 
			# The offset the file is telling us to jump to can't exist because the file's too small
			continue

		fwav: FWAVHeader = FWAVHeader(bom)
		fwav.data(bars, pos)

		fwav.data_ = bars[pos:pos + fwav.size_]

		tracks_data.append(fwav.data_)
		track_offsets.append(pos)

	tracks = dict(zip(track_names, tracks_data))
	offsets = dict(zip(track_names, track_offsets))

	return tracks, offsets

def convert_bars(bars, dest_bom):

	"""
	Convert a bars file between endians, and return the converted
	file
	"""

	if bars[0x8:0xA] == b"\xFF\xFE":
		bom = '<'
	else:
		bom = '>'

	# Create an output buffer the length of our file
	output_buffer = bytearray(len(bars))
	pos = 0

	# Create a structure for the header
	header = Header(bom)
	header.data(bars, pos)

	# Check for an invalid file
	if header.magic != BARS_HEADER:
		raise RuntimeError(f"Not a valid BARS file.")

	file_size = len(bars)

	# Write the header data to the output buffer
	output_buffer[pos:pos + header.size] = bytes(
		Header(dest_bom).pack("BARS".encode("utf-8").ljust(4, b'\0'), header.size_, header.endian, header.reserved, header.count)
	)

	# Offset an amount of header.size
	pos += header.size

	# Copy the unknown data portion to the output_buffer
	unknown = Unknown(bom, header.count)
	unknown.data(bars, pos)
	output_buffer[pos:pos + unknown.size] = Unknown(dest_bom, header.count).pack(*unknown.unknown)
	pos += unknown.size

	# Create a structure for the track structure
	track_struct = TRKStruct(bom, header.count)
	track_struct.data(bars, pos)

	# Write the track structure data to the output buffer
	output_buffer[pos:pos + track_struct.size] = TRKStruct(dest_bom, header.count).pack(*track_struct.offsets)

	track_names = []
	
	for i in range(header.count):
		# Get AMTA offset from list and position ourselves at that point
		pos = track_struct.offsets[i * 2] 

		# Create a structure for the AMTA header
		amta = AMTAHeader(bom)
		amta.data(bars, pos)

		if amta.magic != AMTA_HEADER:
			raise RuntimeError(f"Track {t+1} has an invalid AMTA header")

		# Write the AMTA data to the output buffer
		output_buffer[pos:pos + amta.size] = bytes(
			AMTAHeader(dest_bom).pack(amta.magic, amta.endian, amta.reserved, amta.length, amta.data_offset, amta.mark_offset, amta.ext_offset, amta.strg_offset)
		)

		# Offset an amount of amta.size
		pos += amta.size

		for j in MAGICS:

			data = AMTASubHeader(bom)
			data.data(bars, pos)
				
			output_buffer[pos:pos + data.size] = bytes(AMTASubHeader(dest_bom).pack(data.magic, data.length))
			pos += data.size

			data.data_ = bars[pos:pos + data.length]
			start = 0
			if j == b'DATA':
				output_buffer[pos:pos + 12] = bars[pos:pos + 12]
				start = 12
			
			if bom != dest_bom and j != b'STRG':
				for k in range(start, len(data.data_), 4):
					output_buffer[pos + k:pos + k + 4] = bytes([
						data.data_[k+3], data.data_[k+2], data.data_[k+1], data.data_[k] # Do an endian swap
					])
			elif bom != dest_bom:
				output_buffer[pos:pos + data.length] = data.data_

			pos += data.length
		
			if data.magic != j:
				raise RuntimeError(f"Track {i+1} has an invalid {data.magic} header")
	# Print out the number of tracks found
	print(f"{header.count} track{plural_s(header.count)} found!")

	if pos == header.size_: # We have now reached the end of the file despite the file telling us that there would be stuff here
		raise RuntimeError(f"Reached EOF, this file probably doesn't actually contain any FWAVs despite containing the offsets for them")

	for i in range(header.count):
		pos = track_struct.offsets[i * 2 + 1] # Get track offset from list
		if pos >= header.size_:
			# The offset the file is telling us to jump to can't exist because the file's too small
			continue

		fwav = FWAVHeader(bom)
		fwav.data(bars, pos)

		output_buffer[pos:pos + fwav.size_] = bars[pos:pos + fwav.size_]

	output_buffer[0x4:0x8] = struct.pack(dest_bom + "I", len(output_buffer))

	return output_buffer
