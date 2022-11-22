import sys, os
from time import time
from conf import Conf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
sys.path.append(os.path.abspath(os.path.join('..', 'conf')))
from sqlalchemy_utils import database_exists, create_database

_conf: Conf
_username: str
_password: str
_hostname: str
_dbname: str

_conf = Conf("conf.yaml")
_username = _conf.get_db_username()
_password = _conf.get_db_password()
_hostname = _conf.get_db_hostname()
_dbname = _conf.get_db_dbname()

SQLALCHEMY_DATABASE_URL = f'postgresql+psycopg2://{_username}:{_password}@{_hostname}/{_dbname}'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
if not database_exists(engine.url):
    create_database(engine.url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()