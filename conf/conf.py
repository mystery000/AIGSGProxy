from dataclasses import dataclass
from typing import Any, List
from unicodedata import name
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

class Conf():

    _agent_host: str
    _agent_port: int
    _db_username: str
    _db_password: str
    _db_hostname: str
    _db_dbname: str
    _sqlite_path: str

    def __init__(self, filepath: str):

        with open(filepath, "rt") as fp:
            self._conf = load(fp, Loader=Loader)

        sqlite = self._conf["sqlite"]
        self._sqlite_path = sqlite["path"]

        database = self._conf["database"]
        self._db_dbname = database["dbname"]
        self._db_hostname = database["hostname"]
        self._db_password = database["password"]
        self._db_username = database["username"]
        
        agent = self._conf["agent"]
        self._agent_host = agent["host"]
        self._agent_port = int(agent["port"])


    def get_sqllite_path(self)-> str:
        return self._sqlite_path

    def get_db_username(self)-> str:
        return self._db_username
    
    def get_db_password(self)-> str:
        return self._db_password
    
    def get_db_hostname(self)-> str:
        return self._db_hostname
    
    def get_db_dbname(self)-> str:
        return self._db_dbname
    
    def get_agent_host(self) -> str:
        return self._agent_host

    def get_agent_port(self) -> int:
        return self._agent_port

