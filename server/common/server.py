import socket
import logging
import select
from typing import Callable
from common import serialization
from common import business
from common import response

OK = 200
ERROR = 500

class Server:
    def __init__(self, port, expected_agencies, listen_backlog, cancel_token):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_socket.setblocking(False)
        self._cancel_token = cancel_token


        def resolver(s: socket.socket, cb: Callable[[socket.socket, Callable[[], tuple[int, bytes]]], None]):
            try:
                code, payload = cb()
                self.__safe_write(s, response.Response(code,payload).to_bytes())
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
            except ConnectionError as c:
                pass
            finally:
                s.close()
        
        self._resolve_bets = LongPolling(lambda x: len(x) >= expected_agencies, resolver)

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
                break

            self.__handle_client_connection(client_sock)
        
        self._server_socket.close()

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """            
        addr = client_sock.getpeername()
        waiting = False
        try:
            client, payload = self.__read_message(client_sock)
            a = business.handle_payload(client, payload)
            if callable(a):
                self._resolve_bets.add_to_wait(client_sock, a)
                waiting = True
            else:
                code, payload = a
                self.__safe_write(client_sock, response.Response(code, payload).to_bytes())
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        except ConnectionError as c:
            pass
        finally:
            if not waiting:
                client_sock.close()

    def __should_cancel(self, where):
        readable, _, _ = select.select(
            [where, self._cancel_token],
            [],
            [],
            100
        )
        if self._cancel_token in readable:
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
            return None
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def __safe_read(self, sock: socket.socket, amount: int) -> bytes:
        read = 0
        buf = b''
        while read < amount:
            if (self.__should_cancel(sock)):
                raise ConnectionError("Socket connection closed prematurely")
            b = sock.recv(amount - read)
            read += len(b)
            buf += b
        return buf
    
    def __safe_write(self, sock: socket.socket, payload: bytes):
        total = len(payload)
        to_write = total
        while to_write > 0:
            written = sock.send(payload[total - to_write:])
            if written <= 0:
                raise ConnectionError("Socket connection closed prematurely")
            to_write -= written
    
    def __read_message(self, client_sock: socket.socket) -> (str, bytes):
        m_len = serialization.Deserializer(
                    self.__safe_read(client_sock, 4)
                ).get_uint32()

        c = self.__safe_read(
            client_sock, 
            serialization.Deserializer(
                self.__safe_read(client_sock, 4)
            ).get_uint32()
        )
        return (c.decode('utf-8'), self.__safe_read(client_sock, m_len))


class LongPolling:

    def __init__(self, ready: Callable[[list], bool], writer: Callable[[socket.socket, Callable[[], tuple[int, bytes]]], None]):
        self.wait_list: list[tuple[socket.socket, Callable[[], tuple[int, bytes]]]] = []
        self.writer = writer
        self.ready = ready

    def add_to_wait(self, s: socket.socket, cb: Callable[[], tuple[int, bytes]]):
        self.wait_list.append((s,cb))
        if self.ready(self.wait_list):
            self.do()
        
    def do(self):
        for s, cb in self.wait_list:
            self.writer(s, cb)
        self.wait_list.clear()