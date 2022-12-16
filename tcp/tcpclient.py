import asyncio
import logging

from .tcpprotocol import TCPProtocol, TCPConnectionHandler


class TCPClient(TCPConnectionHandler):
    _name: str
    _host: str
    _port: int

    _transport: asyncio.Transport
    _proto: TCPProtocol
    _additional_handler: TCPConnectionHandler

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

        self._transport = None
        self._proto = None

    async def connect(self) -> bool:
        if self._transport is not None:
            return

        loop = asyncio.get_running_loop()

        try:
            (self._transport, self._proto) = await loop.create_connection(
                lambda: TCPProtocol(self),
                self._host,
                self._port
            )
        except BaseException as e:
            return False

        return True

    async def send(self, buf: bytes):
        if self._transport is None:
            return

        self._proto.send(buf)

    async def close(self):
        if self._transport is None:
            return

        self._transport.close()
        self._transport = None
        self._proto = None

    def name(self) -> str:
        return f"{ self._name }"

    def location(self) -> str:
        return f"{ self._host }:{ self._port }"

    # Handler
    def on_new_connection(
        self,
        id: str,
        remote_host: str,
        remote_port: int
    ):
        if self._additional_handler is None:
            return

        self._additional_handler.on_new_connection(
            id,
            remote_host,
            remote_port
        )

    def on_data_received(
        self,
        id: str,
        data: bytes
    ):
        if self._additional_handler is None:
            return

        self._additional_handler.on_data_received(id, data)

    def on_closed(self, id: str):
        if self._additional_handler is None:
            return

        self._additional_handler.on_closed(id)

    def on_sent(self, id: str, num_bytes: int):
        if self._additional_handler is None:
            return

        self._additional_handler.on_sent(id, num_bytes)
