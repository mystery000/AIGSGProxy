from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timezone

from . import models

def save_pos(db: Session, source: str, content: str) -> None:
    row = models.PosData(
        created_at=datetime.now().isoformat() + "Z",
        source=source,
        content=content)

    db.add(row)
    db.commit()
    
def get_pos(db: Session, source: str, created_at: str) -> None:
    return db.query(models.PosData.created_at.label('TimeStamp'), models.PosData.content.label('Message')).filter(models.PosData.source == source).filter(models.PosData.created_at >= created_at).all()
