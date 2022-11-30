from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timezone
from datetime import timedelta
from . import models
import pytz

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
    records = db.query(models.PosData.created_at.label('TimeStamp'), models.PosData.content.label('Message')).filter(models.PosData.source == source).filter(models.PosData.created_at >= created_at).all()
    # data = []
    # for record in records:
    #     timestamp = datetime.strptime(record[0], '%Y-%m-%dT%H:%M:%S.%f%z')
    #     print(timestamp)
    #     print(timestamp-timedelta(hours=3))
    #     data.append({
    #         "TimeStamp": timestamp-timedelta(hours=3),
    #         "Message": record[1]
    #     })
    return records