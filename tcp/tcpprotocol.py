import asyncio
import logging
import uuid
from typing import Tuple
from .tcpconnectionhandler import TCPConnectionHandler


class TCPProtocol(asyncio.Protocol):
    _remote_host: str
    _remote_port: int
    _transport: asyncio.Transport
    _is_closed: bool
    _handler: TCPConnectionHandler
    _id: str

    def __init__(self, handler: TCPConnectionHandler) -> None:
        self._is_closed = True
        self._handler = handler
        self._id = str(uuid.uuid4())

    def _close(self):
        self._transport.close()
        self._is_closed = True

    def connection_made(self, transport: asyncio.Transport):
        # Tuple: (host, port) of remote
        peername: Tuple[str, int] = transport.get_extra_info("peername")
        host = peername[0]
        port = peername[1]

        # logging.info(f"Got connection from { host }:{ port }")
        self._remote_host = host
        self._remote_port = port
        self._transport = transport
        self._is_closed = False

        self._handler.on_new_connection(self._id, host, port)

    def data_received(self, data: bytes):
        # logging.info(f"data_received: { data }")

        self._handler.on_data_received(self._id, data)

    def connection_lost(self, exc):
        # logging.info(f"Connection from { self.remote_info() } lost, err: { exc }")
        self._close()
        self._handler.on_closed(self._id)

    def remote_info(self) -> str:
        return f"{ self._remote_host }:{ self._remote_port }"

    def send(self, data: bytes):
        if self._is_closed:
            return

        self._transport.write(data)
        self._handler.on_sent(self._id, len(data))

    def close(self):
        if not self._is_closed:
            # logging.info(f"Closing connection from { self.remote_info() }")
            self._close()
