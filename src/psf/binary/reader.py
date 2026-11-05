import io
import struct

from psf.errors import PsfParseError


class BinaryReader:
    """Reads the primitives psfbin is built from."""

    def __init__(self, file: io.BufferedReader):
        self.fp = file

    def tell(self) -> int:
        return self.fp.tell()

    def seek(self, offset: int, whence: int = 0) -> None:
        self.fp.seek(offset, whence)

    # === Core Read ===
    def read_bytes(self, n: int) -> bytes:
        data = self.fp.read(n)
        if len(data) != n:
            raise PsfParseError(f"expected {n} bytes, got {len(data)}")
        return data

    def _read_struct(self, fmt: str) -> tuple:
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.read_bytes(size))

    def read_uint8(self) -> int:
        return self._read_struct("!B")[0]

    def read_int8(self) -> int:
        return self._read_struct("!b")[0]

    def read_uint16(self) -> int:
        return self._read_struct("!H")[0]

    def read_uint32(self) -> int:
        return self._read_struct("!I")[0]

    def read_float64(self) -> float:
        return self._read_struct("!d")[0]

    def read_string(self, encoding="utf-8") -> str:
        length = self.read_uint32()
        data = self.read_bytes(length)
        padding = (4 - (length % 4)) % 4
        if padding:
            self.read_bytes(padding)
        return data.decode(encoding)

    # === Peek Support ===
    def peek_bytes(self, n: int) -> bytes:
        data = self.fp.peek(n)[:n]
        if len(data) < n:
            raise PsfParseError(f"could only peek {len(data)} bytes, expected {n}")
        return data

    def peek_uint32(self) -> int:
        data = self.peek_bytes(4)
        return struct.unpack("!I", data)[0]

    def skip(self, n: int) -> None:
        self.seek(n, 1)

    def close(self) -> None:
        self.fp.close()
