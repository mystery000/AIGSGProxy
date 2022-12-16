import logging
import logging.handlers
from logging import StreamHandler

import sys
import json
import asyncio
import multiprocessing as mp
import re
from socket import socket, gethostbyname
import time
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unicodedata import name
import requests

from samba import Samba
from server import Server
from kvdb import KVDB, DBValue
from conf import Conf
from db import Db

FILE_EXTENSION = 'dat'


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
            requests.post(f"http://localhost/push_log", json={
                "type": "samba",
                "message": msg
            })
        except:
            self._skip = True


class App():
    _smb: Samba
    _smb_connected: bool
    _smb_last_check: datetime
    _smb_last_disconnect: datetime
    _server_by_serial: Dict[str, Server]
    _db: KVDB
    _conf: Conf
    _sqlite_db: Db
    _queue: mp.Queue


    def __init__(self, queue: mp.Queue):
        self._sqlite_db = Db()

        conf = Conf("conf.yaml")
        self._conf = conf

        self._smb = Samba(
            conf.get_username(),
            conf.get_password(),
            conf.get_server())

        self._smb_connected = False

        self._smb_last_check = datetime.now()
        self._smb_last_disconnect = datetime.now()

        self._server_by_serial = dict()
        self._db = KVDB()
        self._queue = queue


    def search_xml_recursive(self, dir: str, indent: int) -> None:
        if not dir.endswith("/"):
            raise Exception("`dir` must ends with a splash (/)")

        logging.info(f"Listing files in '{ self._conf.get_service() }{ dir }")
        items = self._smb.listItems(self._conf.get_service(), dir)

        for item in items:
            logging.info(f"{ '-' * indent }[{ 'D' if item.is_directory else 'F' }] { item.file_name }")

            if item.is_directory:
                self.search_xml_recursive(f"{ dir }{ item.file_name }/", indent + 2)
            else:
                if item.file_name.lower().endswith(f".{ FILE_EXTENSION }"):
                    self.process_xml(f"{ dir }{ item.file_name }", item.last_write_time)


    def _get_serial_from_xml(self, xml_data: bytes) -> bytes | None:
        match = re.search(b'SerialNumber="(.+?)"', xml_data, re.MULTILINE | re.DOTALL)
        match: re.Match
        if match:
            return match.group(1)

        return None


    def process_xml(self, full_path: str, last_write_time: float) -> bool:
        logging.info(f"Processing '{ full_path }'")

        last_write: datetime = datetime.utcfromtimestamp(last_write_time)
        db = self._db.get(full_path)
        if (db is not None) and (db.last_write == last_write):
            logging.info(f"  Already processed at { db.last_processed }")
            return False

        file_obj = tempfile.NamedTemporaryFile()
        file_attributes, filesize = self._smb.download_file(self._conf.get_service(), full_path, file_obj)
        file_obj.seek(0)

        xml_data = file_obj.read()
        serial_bytes = self._get_serial_from_xml(xml_data)

        serial = None
        if serial_bytes is not None:
            serial = serial_bytes.decode("utf-8")

        if serial in self._server_by_serial:
            logging.info(f"  Broadcasting data for serial '{ serial }'")
            self._server_by_serial[serial].send(xml_data)
            self._server_by_serial[serial].send(b"\r\n\r\n")

        self._db.set(full_path, DBValue(
            last_processed=datetime.now(),
            last_write=last_write))

        logging.info("  Done")
        return True


    def _start_servers(self):
        servers = self._conf.get_servers()
        for server in servers:
            self._server_by_serial[server.serial] = Server(server.port, server.name)
            self._server_by_serial[server.serial].start()


    def _connect_smb(self) -> bool:
        self._smb_connected = self._smb.connect()
        if not self._smb_connected:
            logging.warning(f"Can't connect to SMB host, scheduled to reconnect after { self._conf.get_reconnect_inverval() } seconds")
            self._smb_last_disconnect = datetime.now()

        return self._smb_connected


    def _process_queue(self):
        if self._queue is None:
            return

        if self._queue.empty():
            return


    def start(self):
        self._start_servers()
        # self._start_proxies()

        if self._conf.get_smb_enabled():
            self._connect_smb()

        while True:
            now = datetime.now()

            if self._conf.get_smb_enabled():
                if not self._smb_connected and (now - self._smb_last_disconnect > timedelta(seconds=self._conf.get_reconnect_inverval())):
                    self._connect_smb()

                if self._smb_connected and (now - self._smb_last_check > timedelta(seconds=self._conf.get_interval_in_seconds())):
                    self._smb_last_check = now
                    self.search_xml_recursive(self._conf.get_root(), 0)

            for _, server in self._server_by_serial.items():
                server.iterate(0.001)

            self._process_queue()


def run_app(queue: mp.Queue, log_to_file: bool):
    if log_to_file:
        logging.basicConfig(
            format="[%(asctime)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    "samba.txt",
                    maxBytes=1024 * 1024,
                    backupCount=10),
                WebsocketHandler()
            ]
        )
    else:
        logging.basicConfig(
            format="[%(asctime)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.StreamHandler(sys.stdout),
                WebsocketHandler()
            ]
        )

    try:
        app = App(queue)
        app.start()
    except KeyboardInterrupt:
        logging.info("Quitting ...")
    except Exception as e:
        logging.warning("Exception")
        logging.warning(str(e))


if __name__ == "__main__":
    print("Beging called as program")
    run_app(None, False)
