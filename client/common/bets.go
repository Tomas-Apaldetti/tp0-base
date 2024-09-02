package common

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

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
	csvPath   string
	batchSize int
	file      *os.File
	scanner   bufio.Scanner
}

func NewBetAction(path string, batch int) (*BetAction, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	a := BetAction{
		csvPath:   path,
		batchSize: batch,
		file:      file,
		scanner:   *bufio.NewScanner(file),
	}
	return &a, nil
}

func (b *BetAction) Do() ([]byte, bool) {
	batch := make([]Bet, 0, b.batchSize)
	for i := 0; i < b.batchSize; i++ {
		if !b.scanner.Scan() {
			break
		}

		line := b.scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) == 5 {
			bet := Bet{
				Nombre:     fields[0],
				Apellido:   fields[1],
				Documento:  fields[2],
				Nacimiento: fields[3],
				Numero:     int32(parseInt(fields[4])),
			}

			batch = append(batch, bet)
		}
	}

	if len(batch) == 0 {
		return nil, true
	}

	serializables := make([]Serializable, len(batch))

	for i, bet := range batch {
		serializables[i] = bet
	}

	s := NewSerializer()
	return s.WriteArray(serializables).ToBytes(), false
}

func (b *BetAction) OnClose() {
	b.file.Close()
}

func (b *BetAction) CanDo() bool {
	return b.scanner.Err() == nil
}

func parseInt(s string) int {
	var i int
	fmt.Scan(s, &i)
	return i
}
