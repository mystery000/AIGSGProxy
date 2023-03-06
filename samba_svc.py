import re
import sys
import json
import time
import logging
import asyncio
import tempfile
import requests
from db import Db #SQLITE3 CONNECTION
from conf import Conf
from samba import Samba
import logging.handlers
from server import Server
from unicodedata import name
import multiprocessing as mp
from kvdb import KVDB, DBValue
from logging import StreamHandler
from typing import List, Dict, Any
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from socket import socket, gethostbyname
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
        
        # SMB save shared files to sqlite database
        parsed_xml_data, _BPSCreated = self._parse_xml_data(xml_data)
        self._sqlite_db.save_pos(serial, parsed_xml_data, _BPSCreated)
        logging.info("SMB shared file is saved to SQLite")
        logging.info("  Done")
        return True

    def _parse_xml_data(self, xml_data: bytes):
        parsed_xml_data = None
        # Create element tree for XML
        tree = ET.ElementTree(ET.fromstring(str(xml_data, 'utf-8')))
        root = tree.getroot()

        _BPSCreated = root.attrib["Created"]
        ele = tree.find('.//Machine')
        _SerialNumber = ele.attrib["SerialNumber"]
        ele = tree.find('.//ParameterSection')
        _StartTime = ele.attrib["StartTime"]
        _EndTime = ele.attrib["EndTime"]
        ele = tree.find('.//HeadercardUnit')
        _HeaderCardID = ele.attrib["HeaderCardID"]
        _DepositID = ele.attrib["DepositID"]
        
        _counters = []
        for counter in root.iter('Counter'):
            DenomID = counter.attrib["DenomID"]
            Value = counter.attrib["Value"]
            Number = counter.attrib["Number"]
            Total = int(Value) * int(Number)
            _counters.append({"DenomID":DenomID, "Value":Value, "Number":Number, "Total":Total})

        # Create text to display xml data 
        parsed_xml_data = f'BPS Created="{_BPSCreated}"\r\nMachine SerialNumber="{_SerialNumber}"\r\nStartTime="{_StartTime}" EndTime="{_EndTime}"\r\nHeaderCardID="{_HeaderCardID}" DepositID="{_DepositID}"\r\n'

        TotalAmount: int = 0

        for counter in _counters:
            DenomID = counter["DenomID"]
            Value = counter["Value"]
            Number = counter["Number"]
            Total = counter["Total"]
            TotalAmount += Total
            parsed_xml_data += f'DenomID="{DenomID}" Value="{Value}" Number="{Number}" Total="{Total}" \r\n'

        parsed_xml_data += f'TotalAmount={TotalAmount}'
        return parsed_xml_data, _BPSCreated

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
                    "logs/samba.txt",
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
    run_app(None, True)
