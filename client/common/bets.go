package common

type Bet struct {
	Nombre     string
	Apellido   string
	Documento  string
	Nacimiento string
	Numero     int32
}

func (c Bet) Serialize() []byte {
	s := NewSerializer()
	s.WriteString(c.Nombre).
		WriteString(c.Apellido).
		WriteString(c.Documento).
		WriteString(c.Nacimiento).
		WriteInt64(c.Numero)

	return s.ToBytes()
}

type BetAction struct {
	Nombre     string
	Apellido   string
	Documento  string
	Nacimiento string
	Numero     int32
}

func (b BetAction) Do() []byte {
	return Bet{
		Nombre:     b.Nombre,
		Apellido:   b.Apellido,
		Documento:  b.Documento,
		Nacimiento: b.Nacimiento,
		Numero:     int32(b.Numero),
	}.Serialize()
}
