import pytz
from . import models
from datetime import timedelta
from sqlalchemy.sql import func
from operator import attrgetter
from sqlalchemy.orm import Session
from datetime import datetime, timezone

def save_pos(db: Session, source: str, content: str, _BPSCreated: str):
    
    if _BPSCreated == None:
        row = models.PosData(
            created_at=datetime.now(pytz.timezone('America/Sao_Paulo')),
            source=source,
            content=content)

        db.add(row)
        db.commit()
    else:
        row = models.PosData(
            created_at=datetime.strptime(_BPSCreated, '%Y-%m-%d %H:%M:%S'),
            source=source,
            content=content)

        db.add(row)
        db.commit()

def get_pos(db: Session, source: str, created_at: str) -> None:
    records = db.query(models.PosData.created_at.label('TimeStamp'), models.PosData.content.label('Message')).filter(models.PosData.source == source).filter(models.PosData.created_at >= created_at).order_by(models.PosData.id.desc()).limit(100).all()
    return records

def get_samba(db: Session, source: str, created_at: str) -> None:
    records = db.query(models.PosData.created_at.label('TimeStamp'), models.PosData.content.label('Message')).filter(models.PosData.source == source).filter(models.PosData.created_at >= created_at).order_by(models.PosData.id.desc()).limit(50).all()
    posData = []
    
    for record in records:
        posData.append(record._mapping)
    posData.sort(key = attrgetter('TimeStamp'), reverse = False)

    return posData