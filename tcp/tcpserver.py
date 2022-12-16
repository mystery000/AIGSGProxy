import asyncio
import logging
from typing import Set

from .tcpprotocol import TCPProtocol
from .tcpconnectionhandler import TCPConnectionHandler


class TCPServer(TCPConnectionHandler):
    _name: str
    _host: str
    _port: int
    _additional_handler: TCPConnectionHandler

    # Internal
    _protos: Set[TCPProtocol]
    _accept_task: asyncio.Task

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        additional_handler: TCPConnectionHandler = None
    ) -> None:
        self._name = name
        self._host = host
        self._port = port
        self._additional_handler = additional_handler

        # Internal
        self._protos = set()
        self._accept_task = None

    def _protocol_factory(self):
        proto = TCPProtocol(self)
        self._protos.add(proto)

        return proto

    async def start(self) -> bool:
        loop = asyncio.get_running_loop()

        try:
            server = await loop.create_server(
                self._protocol_factory,
                self._host,
                self._port
            )
        except BaseException as e:
            logging.exception(f"Creating server error { self.name() }")
            return False

        self._accept_task = asyncio.create_task(server.serve_forever())

        return True

    async def stop(self):
        # Stop the server
        if self._accept_task is None:
            return

        if not self._accept_task.done():
            self._accept_task.cancel()

            try:
                await self._accept_task
            except asyncio.CancelledError:
                pass

        # Close remaing connections
        for proto in self._protos:
            proto.close()

        self._accept_task = None
        self._protos.clear()

    async def send(self, data: bytes):
        for proto in self._protos:
            proto.send(data)

    def name(self) -> str:
        return self._name

    # Handler
    def on_new_connection(
        self,
        id: str,
        remote_host: str,
        remote_port: int
    ):
        if self._additional_handler is None:
            return

        # logging.info(f"New connection to Proxy Server { self._name } (id: '{ id }', remote_host: '{ remote_host }', remote_port: '{ remote_port }')")
        self._additional_handler.on_new_connection(id, remote_host, remote_port)

    def on_data_received(
        self,
        id: str,
        data: bytes
    ):
        if self._additional_handler is None:
            return

        # logging.info(f"Proxy Server { self._name } received data (id: '{ id }', data: '{ data }')")
        self._additional_handler.on_data_received(id, data)

    def on_closed(self, id: str):
        if self._additional_handler is None:
            return

        # logging.info(f"Proxy Server  { self._name } closed connection (id: '{ id }')")
        self._additional_handler.on_closed(id)

    def on_sent(self, id: str, num_bytes: int):
        if self._additional_handler is None:
            return

        # logging.info(f"on_sent(id: '{ id }', num_bytes: '{ num_bytes }')")
        self._additional_handler.on_sent(id, num_bytes)