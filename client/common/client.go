package common

import (
	"context"
	"encoding/binary"
	"net"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	action Action
	conn   net.Conn
}

type Message struct {
	length   uint32
	clientId string
	payload  []byte
}

func (h *Message) Serialize() []byte {
	s := NewSerializer()
	s.WriteUint32(h.length)
	s.WriteString(h.clientId)
	s.WriteBytes(h.payload)
	return s.ToBytes()
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig, action Action) *Client {
	client := &Client{
		config: config,
		action: action,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(ctx context.Context) {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		// Create the connection the server in every loop iteration. Send an
		c.createClientSocket()

		c.safeWrite(ctx, c.WrapPayload(c.action.Do()))

		_, msg, err := c.readResponse(ctx)
		c.conn.Close()
		if err != nil && err == context.Canceled {
			return
		} else if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
			c.config.ID,
			msg,
		)

		// Wait a time between sending one message and the next one
		select {
		case <-ctx.Done():
			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) safeWrite(ctx context.Context, data []byte) error {
	to_write := len(data)
	for to_write > 0 {
		written, err := c.conn.Write(data[len(data)-to_write:])
		if err != nil {
			return err
		}
		to_write -= written
	}

	return nil
}

func (c *Client) safeRead(ctx context.Context, n int) ([]byte, error) {
	responseChan := make(chan []byte, 1)
	errorChan := make(chan error, 1)

	go func() {
		read := 0
		buf := make([]byte, n)
		for read < n {
			a, err := c.conn.Read(buf[read:])
			if err != nil {
				errorChan <- err
				return
			}
			read += a
		}
		responseChan <- buf
	}()
	select {
	case res := <-responseChan:
		return res, nil
	case err := <-errorChan:
		return nil, err
	case <-ctx.Done():
		// Context was canceled
		return nil, ctx.Err()
	}
}

func (c *Client) readResponse(ctx context.Context) (int, []byte, error) {
	length, err := c.safeRead(ctx, 4)

	if err != nil {
		return 0, nil, err
	}

	code, err := c.safeRead(ctx, 4)

	if err != nil {
		return 0, nil, err
	}

	m, err := c.safeRead(ctx, int(int32(binary.LittleEndian.Uint32(length))))

	if err != nil {
		return 0, nil, err
	}

	return int(int32(binary.LittleEndian.Uint32(code))), m, nil
}

func (c *Client) WrapPayload(payload []byte) []byte {
	l := len(payload)
	m := &(Message{
		payload:  payload,
		clientId: c.config.ID,
		length:   uint32(l),
	})
	return m.Serialize()
}

type Action interface {
	Do() []byte
}
