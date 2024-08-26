import socket
import logging
import select


class Server:
    def __init__(self, port, listen_backlog, cancel_token):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_socket.setblocking(False)
        self._cancel_token = cancel_token

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while True:
            client_sock = self.__accept_new_connection()
            if not client_sock:
                logging.info("action: shutdown_server | result: in_progress | info: got order to shutdown")
                break

            self.__handle_client_connection(client_sock)
        
        self._server_socket.close()
        logging.info("action: shutdown_server | result: success | info: server shutdown")


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            addr = client_sock.getpeername()
            if self.__should_cancel(client_sock):
                client_sock.close()
                logging.info(f"action: shutdown_client | result: success | ip: {addr[0]}")
                return
            # TODO: Modify the receive to avoid short-reads
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            # TODO: Modify the send to avoid short-writes
            client_sock.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __should_cancel(self, where):
        readable, _, _ = select.select(
            [where, self._cancel_token],
            [],
            [],
            100
        )
        if self._cancel_token in readable:
            logging.info("action: shutdown_server | result: in_progress | info: cancel token has information")
            return True
        
        if where in readable:
            return False
        
        return self.__should_cancel(where)

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        if self.__should_cancel(self._server_socket):
            logging.info("action: shutdown_server | result: in_progress | info: cancel token has information")
            return None
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
