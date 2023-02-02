from dataclasses import dataclass
from typing import Any, List
from unicodedata import name
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


@dataclass
class ServerInfo():
    serial: str
    port: int
    name: str


@dataclass
class ProxyInfo():
    origin: str
    port: int
    name: str
    auto_connect: bool
    reconnect_interval_in_seconds: float


class Conf():
    _conf: Any
    _servers: List[ServerInfo]
    _server: str
    _username: str
    _password: str
    _service: str
    _root: str
    _interval_in_seconds: float
    _reconnect_inverval: float
    _smb_enabled: bool
    _agent_host: str
    _agent_port: int
    _proxies: List[ProxyInfo]


    def __init__(self, filepath: str):
        self._servers = []
        self._proxies = []
        self._smb_enabled = False

        with open(filepath, "rt") as fp:
            self._conf = load(fp, Loader=Loader)

        agent = self._conf["agent"]
        self._agent_host = agent["host"]
        self._agent_port = int(agent["port"])

        smb = self._conf["smb"]
        self._server = smb["server"]
        self._username = smb["username"]
        self._password = smb["password"]
        self._service = smb["service"]
        self._root = smb["root"]
        self._interval_in_seconds = float(smb["interval_in_seconds"])
        self._reconnect_inverval = float(smb["reconnect_inverval"])
        self._smb_enabled = smb["enabled"]

        if "servers" in self._conf:
            servers = self._conf["servers"]
            for server in servers:
                serial = server["serial"]

                self._servers.append(ServerInfo(
                    serial=serial,
                    port=int(server["port"]),
                    name=server["name"]
                ))

        if "proxies" in self._conf:
            proxies = self._conf["proxies"]
            for proxy in proxies:
                origin = proxy["origin"]
                port = int(proxy["port"])
                name = proxy["name"]
                auto_connect = proxy["auto_connect"]
                reconnect_inverval = float(proxy["reconnect_inverval"])
                self._proxies.append(ProxyInfo(
                    origin=origin,
                    port=port,
                    name=name,
                    auto_connect=auto_connect,
                    reconnect_interval_in_seconds=reconnect_inverval
                ))


    def get_servers(self) -> List[ServerInfo]:
        return self._servers


    def get_server(self, serial: str) -> ServerInfo | None:
        for server in self._servers:
            if server.serial == serial:
                return server

        return None


    def get_proxies(self) -> List[ProxyInfo]:
        return self._proxies


    def get_server(self) -> str:
        return self._server


    def get_username(self) -> str:
        return self._username


    def get_password(self) -> str:
        return self._password


    def get_service(self) -> str:
        return self._service


    def get_root(self) -> str:
        return self._root


    def get_agent_host(self) -> str:
        return self._agent_host


    def get_agent_port(self) -> int:
        return self._agent_port


    def get_interval_in_seconds(self) -> float:
        return self._interval_in_seconds


    def get_reconnect_inverval(self) -> float:
        return self._reconnect_inverval


    def get_smb_enabled(self) -> bool:
        return self._smb_enabled

    def get_conf_obj(self) -> Any:
        return self._conf
