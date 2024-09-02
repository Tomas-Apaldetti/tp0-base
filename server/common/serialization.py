import struct

class Deserializer:

    def __init__(self, buf: bytes):
        self.buf = buf;
        self.curr = 0;

    def get_uint32(self) -> int:
        b = self.buf[self.curr: self.curr + 4]
        self.curr = self.curr + 4
        return struct.unpack('<I',b)[0]

    def get_string(self) -> str:
        size = self.get_uint32()
        b = self.buf[self.curr: self.curr + size]
        self.curr = self.curr + size
        return b.decode('utf-8')

    def get_int32(self) -> int:
        b = self.buf[self.curr: self.curr + 4]
        self.curr = self.curr + 4
        return struct.unpack('<i',b)[0]

    def get_list(self, deserializer) -> list:
        r = self.get_uint32()
        return [deserializer(self) for _ in range(r)]

class Serializer:

    def __init__(self):
        self.b: bytes = b'';

    def push_uint32(self, v: int):
        self.b += struct.pack('<I', v)
        return self

    def push_int32(self, v: int):
        self.b += struct.pack('<i', v)
        return self

    def push_bytes(self, b: bytes):
        self.b += b
        return self

    def to_bytes(self) -> bytes:
        return self.b[:]