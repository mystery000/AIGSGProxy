import logging
import socket
import select
import os

from typing import List, Dict, Any


class Server():
    _port: int
    _name: str
    _socket: socket.socket
    _started: bool
    _sock_list: List[socket.socket]
    _data_by_sock: Dict[socket.socket, bytes]
    _address_by_sock: Dict[socket.socket, Any]


    def __init__(self, port: int, name: str):
        self._port = port
        self._name = name
        self._started = False
        self._readable = []
        self._data_by_sock = dict()
        self._address_by_sock = dict()


    def start(self):
        if self._started:
            raise Exception(f"Server '{ self._name }' already started")

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._socket.bind(("0.0.0.0", self._port))
        self._socket.listen(10)
        self._started = True
        self._sock_list = [self._socket]


    def iterate(self, timeout: float | None = None):
        write_list = [ sock for sock in self._sock_list if sock is not self._socket ]

        readable, writable, errored = select.select(self._sock_list, write_list, [], timeout)
        readable: List[socket.socket]
        writable: List[socket.socket]
        errored: List[socket.socket]

        for sock in readable:
            if sock is self._socket:
                client_socket, address = self._socket.accept()
                self._sock_list.append(client_socket)
                self._data_by_sock[client_socket] = b''
                self._address_by_sock[client_socket] = address

                logging.info(f"'{ self._name }' got connection from { address }")
            else:
                data = sock.recv(1024)
                if data:
                    logging.info(f"'{ self._name }' received: { data } from [{ self._address_by_sock[sock] }]")
                else:
                    logging.info(f"'{ self._name }' lost connection from client")
                    sock.close()
                    self._sock_list.remove(sock)
                    del self._data_by_sock[sock]

        for sock in writable:
            if sock in self._data_by_sock:
                buf = self._data_by_sock[sock]
                if len(buf) == 0:
                    continue

                sent = sock.send(buf)
                if sent > 0:
                    self._data_by_sock[sock] = buf[sent:]


    def send(self, data: bytes):
        for k, v in self._data_by_sock.items():
            self._data_by_sock[k] = v + data
