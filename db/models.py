from .database import Base
from sqlalchemy import Boolean, Column, Integer, String, DateTime

class PosData(Base):
    __tablename__ = "pos_data"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), index=True)
    source = Column(String, index=True)
    content = Column(String)