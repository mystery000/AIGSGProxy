import socket
import logging
from dataclasses import dataclass
from typing import List, BinaryIO, Tuple, Any

from smb.SMBConnection import SMBConnection
from smb.base import SharedFile

from .exceptions import ResolveHostAddressException


@dataclass
class FileInfo:
    file_name: str
    is_directory: bool
    last_write_time: float


class Samba():
    _conn: SMBConnection
    _server_ip: str
    _is_connected: bool


    def _sharedfile_to_fileinfo(self, inp: SharedFile) -> FileInfo:
        return FileInfo(
            file_name=inp.filename,
            is_directory=inp.isDirectory,
            last_write_time=inp.last_write_time
        )


    def __init__(self, username: str, password: str, server_name: str):
        self._conn = SMBConnection(
            username,
            password,
            "aigsg_client",
            server_name,
            is_direct_tcp=True)
        self._server_ip = None

        try:
            self._server_ip = socket.gethostbyname(server_name)
            logging.info(f"Server IP: { self._server_ip }")
        except socket.gaierror:
            # raise ResolveHostAddressException()
            pass

        self._is_connected = False


    def connect(self) -> bool:
        if self._server_ip is None:
            return False

        self._is_connected = self._conn.connect(self._server_ip, port=445)
        return self._is_connected


    def listItems(self, service_name: str, path: str) -> List[FileInfo]:
        items: List[SharedFile] = self._conn.listPath(service_name, path)
        return [ self._sharedfile_to_fileinfo(item) for item in items if (item.filename!="." and item.filename!="..") ]


    def download_file(self, service_name: str, path: str, file_obj: BinaryIO) -> Tuple[int, int]:
        logging.info(f"Downloading '{ path }' from service '{ service_name }'")
        return self._conn.retrieveFile(service_name, path, file_obj)
