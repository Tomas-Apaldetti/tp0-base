package common

import (
	"bufio"
	"context"
	"fmt"
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
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
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

func readResponse(ctx context.Context, reader *bufio.Reader) (string, error) {
	responseChan := make(chan string)
	errorChan := make(chan error)

	// Start a goroutine to handle the blocking read operation
	go func() {
		line, err := reader.ReadString('\n')
		if err != nil {
			errorChan <- err
			return
		}
		responseChan <- line
	}()
	// Use select to wait for either the response or the context cancellation
	select {
	case res := <-responseChan:
		return res, nil
	case err := <-errorChan:
		return "", err
	case <-ctx.Done():
		// Context was canceled
		return "", ctx.Err()
	}
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(ctx context.Context) {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		// Create the connection the server in every loop iteration. Send an
		c.createClientSocket()

		// TODO: Modify the send to avoid short-write
		fmt.Fprintf(
			c.conn,
			"[CLIENT %v] Message N°%v\n",
			c.config.ID,
			msgID,
		)

		msg, err := readResponse(ctx, bufio.NewReader(c.conn))
		c.conn.Close()
		if err != nil && err == context.Canceled {
			log.Infof("action: shutdown_client | result: in_progress")
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
			// There is no connection created here, nor anything open.
			log.Infof("action: shutdown_client | result: in_progress")
			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
