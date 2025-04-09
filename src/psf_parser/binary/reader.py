import os
import io
import struct
from typing import BinaryIO


class BinaryReader:
    '''A buffered binary file reader providing abstractions for simple read operations.'''

    def __init__(self, file: BinaryIO):
        self.file = io.BufferedReader(file)

    def read_bytes(self, n: int) -> bytes:
        '''Read n bytes from the buffer.'''
        return self.file.read(n)

    def read_int(self, n: int = 4) -> int:
        '''Read a n-byte integer.'''
        return struct.unpack('!i', self.read_bytes(n))[0]

    def read_float(self, n: int = 8) -> float:
        '''Read an n-byte float.'''
        return struct.unpack('!d', self.read_bytes(n))[0]

    def read_string(self, encoding: str = 'utf-8') -> str:
        '''Read a length-prefixed string (4-byte aligned)'''
        length = self.read_int()
        data = self.read_bytes(length)
        self.goto(offset=(-length)%4, whence=os.SEEK_CUR)  # pad align to 4
        return data.decode(encoding)

    @property
    def filesize(self) -> int:
        '''Returns the total number of bytes in the IO object.'''
        try:
            # Attempt to query file metadata
            return os.stat(self.file.name).st_size
        except (OSError, AttributeError):
            # Fallback: Use seek operations to determine total size
            current_pos = self.file.tell()
            self.file.seek(0, os.SEEK_END)
            size = self.file.tell()
            self.file.seek(current_pos, os.SEEK_SET)
            return size

    @property
    def pos(self) -> int:
        '''Return the current position in the file.'''
        return self.file.tell()

    def goto(self, offset: int, whence: int = os.SEEK_SET):
        '''Go to a specific position in the file.'''
        self.file.seek(offset, whence)

    def close(self):
        '''Close the underlying file. After this, file-operations result in errors.'''
        self.file.close()


