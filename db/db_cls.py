from typing import Any
from .crud import save_pos, get_pos, get_samba
from .database import engine, SessionLocal, Base


class Db():
    _db: Any

    def __init__(self):
        Base.metadata.create_all(bind=engine)
        self._db = SessionLocal()

    def save_pos(self, source: str, content: str, _BPSCreated: str = None):
        save_pos(self._db, source, content, _BPSCreated)

    def get_pos(self, source: str, created_at: str):
        return get_pos(self._db, source, created_at)

    def get_samba(self, source: str, created_at: str):
        return get_samba(self._db, source, created_at)