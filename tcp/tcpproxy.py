import asyncio
import logging
from typing import Any, Coroutine, Set

from db import Db
from .tcpclient import TCPClient
from .tcpserver import TCPServer
from .tcpconnectionhandler import TCPConnectionHandler


class TCPProxy(TCPConnectionHandler):
    _db: Db
    _name: str
    _listen_host: str
    _listen_port: int
    _origin_host: str
    _origin_port: int

    _is_auto_connect: bool
    _reconnect_interval: float

    _origin: TCPClient
    _server: TCPServer
    _reconnect_task: asyncio.Task
    _additional_tasks: Set[asyncio.Task]
    _pending_close: bool

    _is_connected: bool
    _watchdog_task: asyncio.Task

    def __init__(
        self,
        db: Db,
        name: str,
        listen_host: str,
        listen_port: int,
        origin_host: str,
        origin_port: str,
        auto_connect: bool,
        reconnect_interval: float
    ) -> None:
        self._db = db
        self._name = name

        self._listen_host = listen_host
        self._listen_port = listen_port
        self._origin_host = origin_host
        self._origin_port = origin_port
        self._is_auto_connect = auto_connect
        self._reconnect_interval = reconnect_interval

        self._origin = None
        self._server = None
        self._reconnect_task = None

        self._additional_tasks = set()
        self._pending_close = False
        self._is_connected = False

    async def connect_origin(self) -> bool:
        self._origin = TCPClient(
            f"{ self._name } origin",
            self._origin_host,
            self._origin_port,
            self
        )

        logging.info(f"Connecting to '{ self._origin.name() }' ({ self._origin.location() })")
        ret = await self._origin.connect()
        self._is_connected = ret

        if not ret:
            await self._schedule_reconnect_origin()

        return ret

    async def _keep_alive(self):
        while True:
            await asyncio.sleep(60)

            logging.info(f"Sending keep-alive messages...")
            if self._is_connected:
                await self._origin.send(b"\0")

            await self._server.send(b"\0")

    async def _schedule_reconnect_origin(self):
        # If already have reconnect pending ...
        if self._reconnect_task is not None:
            if not self._reconnect_task.done():
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass

        self._reconnect_task = None
        self._reconnect_task = asyncio.create_task(self._reconnect_origin())
        self._reconnect_task.add_done_callback(self._async_callback_result)

    async def _reconnect_origin(self):
        logging.info(f"Scheduled to reconnect in { self._reconnect_interval } seconds ...")
        await asyncio.sleep(self._reconnect_interval)
        await self.connect_origin()

    async def reset_origin(self, is_force: bool = False) -> None:
        self._origin = None

        if not is_force:
            await self._schedule_reconnect_origin()

    async def _start_server(self) -> bool:
        self._server = TCPServer(
            f"{ self._name } server",
            self._listen_host,
            self._listen_port
        )

        if not await self._server.start():
            self._server = None
            return False

        logging.info(f"Started server '{ self._server.name() }'")
        return True

    async def _reset_server(self) -> None:
        if self._server is None:
            return

        await self._server.stop()
        self._server = None

    def _async_callback_result(self, t: asyncio.Task):
        try:
            t.result()
        except asyncio.CancelledError:
            pass

    async def start(self) -> bool:
        if not await self._start_server():
            return False

        if self._is_auto_connect:
            await self.connect_origin()

        task = asyncio.create_task(self._keep_alive())
        task.add_done_callback(self._remove_task_from_set)
        self._additional_tasks.add(task)

    async def stop(self) -> None:
        logging.info(f"Stopping proxy '{ self._name }'")
        self._pending_close = True

        await self._reset_server()

        if self._reconnect_task is not None:
            if not self._reconnect_task.done():
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass

            self._reconnect_task = None

        if self._origin is not None:
            await self._origin.close()

        tasks = [ t for t in self._additional_tasks ]
        for task in tasks:
            if task.done():
                continue

            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

        logging.info(f"'{ self._name }' stopped")

    def is_connected(self) -> bool:
        return self._is_connected

    def is_auto_reconnect(self) -> bool:
        return self._is_auto_connect

    def invoke_async_func(self, func: Coroutine):
        task = asyncio.create_task(func)
        self._additional_tasks.add(task)

        task.add_done_callback(self._remove_task_from_set)

    # Handler
    def _remove_task_from_set(self, task: asyncio.Task):
        try:
            task.result()
        except asyncio.CancelledError:
            pass

        self._additional_tasks.remove(task)

    def on_new_connection(
        self,
        id: str,
        remote_host: str,
        remote_port: int
    ):
        logging.debug(f"New connection { id } from { remote_host }:{ remote_port }")

        if self._server is None:
            return

        self.invoke_async_func(self._server.send(f"'{ self._name }' origin connected\r\n".encode()))

    def on_closed(self, id: str):
        logging.debug(f"Connection closed: { id }")
        if self._pending_close:
            return

        self.invoke_async_func(self.reset_origin())

        if self._server is None:
            return

        self.invoke_async_func(self._server.send(f"'{ self._name }' origin disconnected\r\n".encode()))

    def on_data_received(
        self,
        id: str,
        data: bytes
    ):
        try:
            self._db.save_pos(self._name, data.decode())
        except:
            logging.exception(f"Failed to save data received '{ self._name }'")

        try:
            self.invoke_async_func(self._server.send(data))
        except:
            logging.exception(f"Failed to forward data received '{ self._name }'")

