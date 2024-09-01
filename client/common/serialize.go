package common

import (
	"bytes"
	"encoding/binary"
)

type Serializer struct {
	buf bytes.Buffer
}

func NewSerializer() Serializer {
	var buf bytes.Buffer
	return Serializer{
		buf,
	}
}

func (s *Serializer) WriteString(str string) *Serializer {
	s.WriteUint32((uint32(len(str))))
	s.buf.WriteString(str)
	return s
}

func (s *Serializer) WriteInt64(n int32) *Serializer {
	binary.Write(&s.buf, binary.LittleEndian, n)
	return s
}

func (s *Serializer) WriteUint32(n uint32) *Serializer {
	binary.Write(&s.buf, binary.LittleEndian, n)
	return s
}

func (s *Serializer) WriteInt8(n int8) *Serializer {
	binary.Write(&s.buf, binary.LittleEndian, n)
	return s
}

func (s *Serializer) WriteBytes(b []byte) *Serializer {
	s.buf.Write(b)
	return s
}

func (s *Serializer) ToBytes() []byte {
	return s.buf.Bytes()
}
