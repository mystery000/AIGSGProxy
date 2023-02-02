from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

time = datetime.now().strftime("%d-%b-%Y-%H-%M")

SQLALCHEMY_DATABASE_URL = f"sqlite:///./data_{time}.sqlite3"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()