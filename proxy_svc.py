import re
import os
import sys
import json
import socket
import sqlite3
import asyncio
import logging
import requests
import datetime
from db import Db  # SQLITE3 Connection
from conf import Conf
import logging.handlers
from tcp import TCPProxy
import multiprocessing as mp
from logging import StreamHandler
from typing import List, Tuple, Dict, Set

from watcher import Watcher

class WebsocketHandler(StreamHandler):
    _skip: bool

    def __init__(self):
        self._skip = False
        StreamHandler.__init__(self)

    def emit(self, record):
        if self._skip:
            return

        msg = self.format(record)

        try:
            pass
            #requests.post(f"http://localhost/push_log", json={
            #    "type": "proxy",
            #    "message": msg
            #})
        except:
            self._skip = True


class App():
    _conf: Conf
    _sqlite_db: Db
    _queue: mp.Queue
    _watcher: Watcher
    _proxy_by_name: Dict[str, TCPProxy]

    def __init__(self, queue: mp.Queue):
        self._conf = Conf("conf.yaml")
        self._sqlite_db = Db()
        self._queue = queue
        self._proxy_by_name = dict()
        self._watcher = Watcher()

    async def _start_proxies(self):
        logging.info("Starting proxies ...")

        if len(self._proxy_by_name) > 0:
            logging.warning("Looks like proxies have started?")

        tasks = []
        for proxy in self._conf._proxies:
            if proxy.name in self._proxy_by_name:
                continue

            (host, port) = proxy.origin.split(":")

            inst = TCPProxy(
                db=self._sqlite_db,
                name=proxy.name,
                listen_host="0.0.0.0",
                listen_port=proxy.port,
                origin_host=host,
                origin_port=int(port),
                auto_connect=proxy.auto_connect,
                reconnect_interval=proxy.reconnect_interval_in_seconds
            )
            self._proxy_by_name[proxy.name] = inst

            tasks.append(inst.start())

        await asyncio.gather(*tasks)

    async def run(self):
        await self._start_proxies()
  
        while True:
            if self._queue is not None:
                if not self._queue.empty():
                    try:
                        msg = self._queue.get_nowait()
                        logging.info(f"Got message: { json.dumps(msg) }")

                        name = msg["NAME"]
                        ip = msg["IP"]
                        port = int(msg["PORT"])
                        logging.info(f"IP={ ip }, NAME={ name }, PORT={ port }")

                        if name not in self._proxy_by_name:
                            logging.warning(f"'{ name }' was not listed in config file, skip")
                            continue

                        proxy = self._proxy_by_name[name]
                        if proxy.is_connected():
                            logging.info(f"Proxy '{ name }' already in active session, skipping")
                        elif proxy.is_auto_reconnect():
                            logging.info(f"Proxy '{ name }' in auto_connect mode, ignored discovery message")
                        else:
                            await proxy.reset_origin()
                            await proxy.connect_origin()
                    except:
                        logging.exception("Handled exception")

            self._watcher.check_schedule()
            await asyncio.sleep(0.1)

    async def shutdown(self):
        for _, proxy in self._proxy_by_name.items():
            await proxy.stop()


def entry_point(queue: mp.Queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = App(queue)

    try:
        loop.run_until_complete(app.run())
    except KeyboardInterrupt:
        logging.info("Quitting")
    except:
        logging.exception("Exception:")
    finally:
        loop.run_until_complete(app.shutdown())

    loop.close()
    asyncio.set_event_loop(None)


def run_proxy(queue: mp.Queue, log_to_file: bool):
    logging.basicConfig(
        format="[%(asctime)s] %(message)s",
        level=logging.INFO,
        handlers=[
            logging.handlers.RotatingFileHandler(
                "proxy.txt",
                maxBytes=1024 * 1024,
                backupCount=10),
            # WebsocketHandler()
        ]
    )
    
    entry_point(queue)


def main():
    # logging.basicConfig(
    #     format="[%(asctime)s] %(message)s",
    #     level=logging.DEBUG,
    #     handlers=[
    #         logging.StreamHandler(sys.stdout)
    #     ]
    # )
    logging.basicConfig(
        format="[%(asctime)s] %(message)s",
        level=logging.INFO,
        handlers=[
            logging.handlers.RotatingFileHandler(
                "logs/proxy.txt",
                maxBytes=1024 * 1024,
                backupCount=10),
            # WebsocketHandler()
        ]
    )
    entry_point(None)

    
if __name__ == "__main__":
    main()