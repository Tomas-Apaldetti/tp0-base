from common import serialization

class Response:

    def __init__(self, code: int, payload: bytes):
        self.code = code
        self.payload = payload

    def to_bytes(self) -> bytes:
        s = serialization.Serializer()
        return s.push_uint32(len(self.payload)
            ).push_int32(self.code
            ).push_bytes(self.payload
            ).to_bytes()
