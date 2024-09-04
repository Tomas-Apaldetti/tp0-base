package common

import (
	"bufio"
	"os"
	"strconv"
	"strings"
)

const LOAD_BETS uint8 = 1
const ASK uint8 = 2

const KEEP_ASKING uint8 = 255
const ANSWER uint8 = 254

const OK = 200
const ERROR = 500

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
		WriteInt32(c.Numero)

	return s.ToBytes()
}

type BetAction struct {
	csvPath      string
	batchSize    int
	file         *os.File
	scanner      bufio.Scanner
	endedReading bool
	winnerAns    bool
	winnerAmnt   int
}

func NewBetAction(path string, batch int) (*BetAction, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	a := BetAction{
		csvPath:      path,
		batchSize:    batch,
		file:         file,
		scanner:      *bufio.NewScanner(file),
		endedReading: false,
		winnerAns:    false,
		winnerAmnt:   0,
	}
	return &a, nil
}

func (b *BetAction) doRead() ([]byte, bool) {
	if b.endedReading {
		return nil, true
	}

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
		b.endedReading = true
		return nil, true
	}

	serializables := make([]Serializable, len(batch))

	for i, bet := range batch {
		serializables[i] = bet
	}

	s := NewSerializer()
	return s.WriteUint8(LOAD_BETS).WriteArray(serializables).ToBytes(), false
}

func (b *BetAction) doAsk() ([]byte, bool) {
	if b.winnerAns {
		return nil, true
	}

	s := NewSerializer()
	return s.WriteUint8(ASK).ToBytes(), false
}

func (b *BetAction) Do() ([]byte, bool) {
	r, next := b.doRead()
	if next {
		return b.doAsk()
	}
	return r, false
}

func (b *BetAction) readLotteryWinners(d *Deserializer) {
	n_winners, err := d.ReadUint32()
	if err != nil {
		log.Errorf("There was an error while deserializing number of winners %s", err)
		return
	}
	b.winnerAns = true
	b.winnerAmnt = int(n_winners)
	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", n_winners)
}

func (b *BetAction) Response(code int, payload []byte) {
	if code == ERROR {
		d := NewDeserializer(payload)
		err_msg, err := d.ReadString()
		if err != nil {
			log.Errorf("There was an error while deserializing %s", err)
			return
		}
		log.Debug("There was an error in the server %s", err_msg)
	}

	if code == OK {
		d := NewDeserializer(payload)
		t, err := d.ReadUint8()
		if err != nil {
			log.Errorf("There was an error while deserializing %s", err)
			return
		}
		if t == ANSWER {
			b.readLotteryWinners(&d)
			return
		}
		if t == KEEP_ASKING {
			log.Debug("I need to keep asking to the server for the winners")
			return
		}
	}
}

func (b *BetAction) OnClose() {
	b.file.Close()
}

func parseInt(s string) int {
	i, err := strconv.Atoi(s)
	if err != nil {
		return 0
	}
	return i
}
