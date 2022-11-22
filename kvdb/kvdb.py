from typing import Dict
from datetime import datetime
from dataclasses import dataclass


@dataclass
class DBValue():
    last_processed: datetime
    last_write: datetime


class KVDB():
    _kv: Dict[str, DBValue]

    def __init__(self):
        self._kv = dict()

    def set(self, key: str, val: DBValue):
        self._kv[key] = val

    def get(self, key: str) -> DBValue | None:
        try:
            return self._kv[key]
        except:
            return None