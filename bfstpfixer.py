# Original by NanobotZ

import os
import sys
import struct
import time

def fix(full_path): # returns true if fixer didn't have any problems
	_, file_name = os.path.split(full_path)
	
	if not os.path.exists(full_path):
		print("Couldn't find the file, wrong path: " + file_name)
		return False
	
	if file_name[-6:] != ".bfstp":
		print("Wrong file extension: " + file_name)
		return False
		
	file = open(full_path, "rb")
	data = bytearray(file.read()) # read tha bytes
	file.close()
	
	magic = data[:4]
	if magic != b"FSTP":
		print("Not a valid FSTP signature: " + file_name)
		return False
		
	bom = '>' if data[4:6] == b"\xFE\xFF" else '<' # get the file bom
	info_offset, info_size = struct.unpack(bom + "2I", data[24:32])
	data_flag = struct.unpack(bom + "H", data[32:34])[0]
	if data_flag != 16385: # the freshly converted file has a SEEK section flag (0x4001), if it's not here then it means the file is already fixed or broken 
		print("This is a fixed bfstp, fixing not needed: " + file_name)
		return False
	
	seek_offset, seek_size = struct.unpack(bom + "2I", data[36:44])
	
	num_channels = data[info_offset+34] # extract number of channels
	
	del data[seek_offset:seek_offset+seek_size] # remove the seek section
	
	pdat_offset = seek_offset #after removing the seek section, pdat section is in the same offset from beginning of the file
	pdat_len_per_channel = 24576 # the usual length of data per channel
	pdat_len = num_channels * pdat_len_per_channel # calc the usual PDAT's data length
	pdat_header_len = 32 if bom == ">" else 64 # pdat header length is twice as big on switch than on WiiU
    
	data[pdat_offset+4:pdat_offset+8] = struct.pack(bom + "I", pdat_len + pdat_header_len) # full PDAT section length
	data[pdat_offset+8] = 0 if bom == ">" else 1 # unknown flag, tested switch BFSTPs had 1, wiiu BFSTPs had 0
	data[pdat_offset+16:pdat_offset+20] = struct.pack(bom + "I", pdat_len) # only data in PDAT length
	# just before the data in PDAT starts - usually stands 0x14 for WiiU (or Big Endian) and 0x54 for Switch (or Little Endian), currently assuming it's about BOM
	data[pdat_offset+28:pdat_offset+32] = struct.pack(bom + "I", 20 if bom == ">" else 52) 
    
	if bom == "<": # since switch PDAT header is twice as big (32 vs 64), it needs to have the second half filled with zeros
		for _ in range(32):
			data.insert(pdat_offset+32, 0) # inserting zeros that are not in the file, otherwise it would replace sound data
            
	del data[pdat_offset+pdat_header_len+pdat_len:] # trim all the unnecessary data
	
	data[32:34] = struct.pack(bom + "H", 16388) # write the PDAT section flag - 0x4004
	data[36:44] = struct.pack(bom + "2I", pdat_offset, pdat_len + pdat_header_len) # write the offset to the PDAT section and it's whole length
	data[44:64] = [0]*20 # fill the rest of the FSTP section with 0
	
	data[12:16] = struct.pack(bom + "I", len(data)) # write the whole file size here
	
	file = open(full_path, "wb")
	file.write(data)
	file.close()
	return True
