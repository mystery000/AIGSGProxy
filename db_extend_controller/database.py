import sys, os
from time import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database



SQLALCHEMY_DATABASE_URL = f"sqlite:///./collection.sqlite3"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)

if not database_exists(engine.url):
    create_database(engine.url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()