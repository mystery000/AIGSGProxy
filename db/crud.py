import pytz
from . import models
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import Session

def save_pos(db: Session, source: str, content: str) -> None:
    row = models.PosData(
        created_at=datetime.now(pytz.timezone('America/Sao_Paulo')),
        source=source,
        content=content)

    db.add(row)
    db.commit()


def get_pos(db: Session, source: str, created_at: str) -> None:
    records = db.query(models.PosData.created_at.label('TimeStamp'), models.PosData.content.label('Message')).filter(models.PosData.source == source).filter(models.PosData.created_at >= created_at).order_by(models.PosData.id.desc()).limit(100).all()
    return records