#!/usr/bin/env python
import io
import struct

class InvalidEndiannessError(Exception):
    pass

class Stream:
    def __init__(self, stream: io.BytesIO, endian: str = "little"):
        """
        A stream for reading and writing data
        """
        self._stream = stream
        if endian == "little":
            self._endian = "<"
        elif endian == "big":
            self._endian = ">"
        else:
            raise InvalidEndiannessError("Not a valid endianness")
        
    def seek(self, offset: int) -> None:
        self._stream.seek(offset)

    def skip(self, n: int) -> None:
        self._stream.seek(n, 1)

    def tell(self) -> int:
        return self._stream.tell()

class TemporarySeek:
    def __init__(self, stream: Stream, offset: int):
        self._stream = stream
        self._temp_offset = offset
        self._original_offset = self._stream.tell()

    def __enter__(self):
        self._stream.seek(self._temp_offset)
        return self._temp_offset

    def __exit__(self, *args):
        self._stream.seek(self._original_offset)

class Reader(Stream):
    """
    A stream to read data from
    """

    def __init__(self, data: bytes, endian: str):
        self.stream = io.BytesIO(memoryview(data))
        super().__init__(self.stream, endian)

    # Read "n" number of bytes
    def read(self, n: int) -> bytes:
        return self._stream.read(n)

    # Read a single char
    def read_int8(self) -> int:
        return struct.unpack(self._endian + "b", self._stream.read(1))[0]

    # Read a single unsigned char
    def read_uint8(self) -> int:
        return struct.unpack(self._endian + "B", self._stream.read(1))[0]

    # Read a string of "str_len"
    def read_string(self, str_len: int) -> bytes:
        return struct.unpack(self._endian + f"{str_len}s", self._stream.read(str_len))[0]
    
    # Read a short
    def read_int16(self) -> int:
        return struct.unpack(self._endian + "h", self._stream.read(2))[0]

    # Read an unsigned short
    def read_uint16(self) -> int:
        return struct.unpack(self._endian + "H", self._stream.read(2))[0]

    # Read an integer
    def read_int32(self) -> int:
        return struct.unpack(self._endian + "i", self._stream.read(4))[0]

    # Read an unsigned integer
    def read_uint32(self) -> int:
        return struct.unpack(self._endian + "I", self._stream.read(4))[0]

    # Read a long long
    def read_int64(self) -> int:
        return struct.unpack(self._endian + "q", self._stream.read(8))[0]

    # Read an unsigned long long
    def read_uint64(self) -> int:
        return struct.unpack(self._endian + "Q", self._stream.read(8))[0]

    # Read a single-point floating value
    def read_float(self) -> float:
        return struct.unpack(self._endian + "f", self._stream.read(4))[0]

