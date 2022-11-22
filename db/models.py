from sqlalchemy import Boolean, Column, Integer, String, DateTime

from .database import Base


class PosData(Base):
    __tablename__ = "pos_data"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(String, index=True)
    source = Column(String, index=True)
    content = Column(String)