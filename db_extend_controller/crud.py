import pytz
from . import models
from datetime import timedelta
from sqlalchemy.sql import func
from operator import attrgetter
from sqlalchemy.orm import Session
from datetime import datetime, timezone

def save_pos(db: Session, source: str, content: str) -> None:
    row = models.PosData(
        created_at=datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat(),
        source=source,
        content=content)

    db.add(row)
    db.commit()

def save_pos(db: Session, created_at: str, source: str, content: str) -> None:
    row = models.PosData(
        created_at=created_at,
        source=source,
        content=content)

    db.add(row)
    db.commit()


def get_pos(db: Session, source: str, created_at: str) -> None:
    records = db.query(models.PosData.created_at.label('TimeStamp'), models.PosData.content.label('Message')).filter(models.PosData.source == source).filter(models.PosData.created_at >= created_at).order_by(models.PosData.id.desc()).limit(100).all()
    posData = []
    
    for record in records:
        posData.append(record._mapping)
    posData.sort(key = attrgetter('TimeStamp'), reverse = False)

    return posData

def get_samba(db: Session, source: str, created_at: str) -> None:
    records = db.query(models.PosData.created_at.label('TimeStamp'), models.PosData.content.label('Content')).filter(models.PosData.source == source).filter(models.PosData.created_at >= created_at).order_by(models.PosData.id.desc()).limit(100).all()
    posData = []
    
    for record in records:
        posData.append(record._mapping)
    posData.sort(key = attrgetter('TimeStamp'), reverse = False)

    return posData