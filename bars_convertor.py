# -*- coding: utf-8 -*-
#!/usr/bin/python3

"""bars_extractor.py: Extracts BFWAV files from Wii U (and possible 3DS, but this is untested) BARS files"""

__author__ = "Nitr4m12(forked from Peter Wunder (@SamusAranX))"
__license__ = "WTFPL"
__version__ = "1.2.4"

import os
import struct
import bcfconverter as sound

# Magic numbers, commonly known as "headers"
BARS_HEADER = b"BARS"
AMTA_HEADER = b"AMTA"
DATA_HEADER = b"DATA"
MARK_HEADER = b"MARK"
EXT_HEADER  = b"EXT_"
STRG_HEADER = b"STRG"
FWAV_HEADERS = [b"FWAV", b"FSTP"]

 #if args.big_endian else '<'

def plural_s(n):
	return "s" if n != 1 else ""

def extract_from_bars(fname, bom):
	# The Python structs to go with the above headers
	bars_header_struct = struct.Struct(bom + "4sIH2xI")
	amta_header_struct = struct.Struct(">4sH2x5I")
	data_header_struct = struct.Struct(">4sI")
	mark_header_struct = struct.Struct(">4sI")
	ext_header_struct  = struct.Struct(">4sI")
	strg_header_struct = struct.Struct(">4sI")
	fwav_header_struct = struct.Struct(">4s8xI8x2I32x")
	with open(fname, "rb+") as f:
		output_dir = os.path.splitext(f.name)[0] + "_extracted" + os.sep
		if not os.path.isdir(output_dir):
			os.mkdir(output_dir)

		bars_header, bars_file_length, bars_endianness, bars_count = bars_header_struct.unpack(f.read(bars_header_struct.size))
		bars_track_struct = struct.Struct(f"{bom}{bars_count*4}x{bars_count*2}I")
		bars_track_offsets = bars_track_struct.unpack(f.read(bars_track_struct.size))

		if bars_header != BARS_HEADER:
			raise RuntimeError(f"{f.name}: Not a valid BARS file.")

		file_size = os.fstat(f.fileno()).st_size
		# if bars_file_length != file_size:
			# raise RuntimeError(f"{f.name}: File size mismatch (expected {bars_file_length} bytes, got {file_size} bytes)")

		track_names = []
		
		for t in range(bars_count):
			bars_amta_offset = bars_track_offsets[t * 2] # Get AMTA offset from list
			f.seek(bars_amta_offset)

			amta_bytes = f.read(amta_header_struct.size)
			amta_header, amta_endianness, amta_length, data_offset, mark_offset, ext_offset, strg_offset = amta_header_struct.unpack(amta_bytes)
			if amta_endianness == 65534:
				amta_header_struct = struct.Struct("<4sH2x5I")
				data_header_struct = struct.Struct("<4sI")
				mark_header_struct = struct.Struct("<4sI")  
				ext_header_struct = struct.Struct("<4sI") 
				strg_header_struct = struct.Struct("<4sI")
				fwav_header_struct = struct.Struct("<4s8xI8x2I32x")
				amta_header, amta_endianness, amta_length, data_offset, mark_offset, ext_offset, strg_offset = amta_header_struct.unpack(amta_bytes)
			if amta_header != AMTA_HEADER:
				raise RuntimeError(f"{f.name}: Track {t+1} has an invalid AMTA header")

			data_bytes = f.read(data_header_struct.size)
			data_header, data_length = data_header_struct.unpack(data_bytes)
			if data_header != DATA_HEADER:
				raise RuntimeError(f"{f.name}: Track {t+1} has an invalid DATA header")

			data = f.read(data_length)

			mark_bytes = f.read(mark_header_struct.size)
			mark_header, mark_length = mark_header_struct.unpack(mark_bytes)
			if mark_header != MARK_HEADER:
				raise RuntimeError(f"{f.name}: Track {t+1} has an invalid MARK header")

			mark = f.read(mark_length)

			ext_bytes = f.read(ext_header_struct.size)
			ext_header, ext_length = ext_header_struct.unpack(ext_bytes)
			if ext_header != EXT_HEADER:
				raise RuntimeError(f"{f.name}: Track {t+1} has an invalid EXT_ header")

			ext = f.read(ext_length)
			strg_bytes = f.read(strg_header_struct.size)
			strg_header, strg_length = strg_header_struct.unpack(strg_bytes)
			if strg_header != STRG_HEADER:
				raise RuntimeError(f"{f.name}: Track {t+1} has an invalid STRG header")

			# Seek until the end of the STRG
			strg = f.read(strg_length).decode("utf8").split('\0')[0]
			track_names.append(strg)

		print(f"{f.name}: {bars_count} track{plural_s(bars_count)} found!")

		if f.tell() == bars_file_length: # We have now reached the end of the file despite the file telling us that there would be stuff here
			raise RuntimeError(f"{f.name}: Reached EOF, this file probably doesn't actually contain any FWAVs despite containing the offsets for them")

		for t in range(bars_count):
			bars_track_offset = bars_track_offsets[t * 2 + 1] # Get track offset from list
			if bars_track_offset >= bars_file_length: # The offset the file is telling us to jump to can't exist because the file's too small
				print(f"{f.name}: Track {t+1} probably doesn't exist, skipping it")
				continue

			f.seek(bars_track_offset) # seek to the next FWAV header

			fwav_header_bytes = f.read(fwav_header_struct.size)
			fwav_header, fwav_length, fwav_info_offset, fwav_data_offset = fwav_header_struct.unpack(fwav_header_bytes)
			if fwav_header not in FWAV_HEADERS:
				print(f"{f.name}: Track {t+1} has an invalid FWAV header")
				continue

			f.seek(-fwav_header_struct.size, os.SEEK_CUR) # seek back to the start of the FWAV data...
			fwav_data = f.read(fwav_length) # ...so that we can read it out in one big chunk
			track_ext = [".bfwav", ".bfstp"][FWAV_HEADERS.index(fwav_header)] # Give the output file a different extension depending on content
			track_name = track_names[t] # Remove null bytes and trim potentially LONG file names
			bfwav_name = output_dir + track_name + track_ext # Construct output file name

			with open(bfwav_name, "wb") as wf:
				wf.write(fwav_data) # write the data to a BFWAV file
				print(f"{f.name}: Saved track {t+1} to {bfwav_name}")