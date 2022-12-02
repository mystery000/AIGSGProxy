import os
import sys
import pytz
import logging
from db import Db
from conf import Conf
from time import sleep
import logging.handlers
from threading import Timer
import sqlalchemy as sqlite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

from os import listdir
import json

def start():

    _db: Db = Db()
    _conf: Conf = Conf("conf.yaml")

    sqlite_path: str = _conf.get_sqllite_path()
    dir_path: str = sqlite_path[0:13]
    db_prefix: str = sqlite_path[14:]    
    
    status: dict = {}

    try:
        with open('sqlite_status.json') as file:
            status = json.load(file)
    except:
        pass    
    
    while True:
        dir = listdir(dir_path)
        sqlite_dbs = []
        for file in dir:
            if file.startswith(f'{db_prefix}_') and file.endswith('sqlite3'):
                sqlite_dbs.append(file)
        for db in sqlite_dbs:
            SQLALCHEMY_DATABASE_URL = f"sqlite:///{dir_path}/{db}"   
            engine = sqlite.create_engine(
                SQLALCHEMY_DATABASE_URL,
            )
            if status.get(db) == None:
                status[db] = 0
            try:
                connection = engine.connect()
                metadata = sqlite.MetaData()
                posData = sqlite.Table('pos_data', metadata, autoload=True, autoload_with=engine)
                query = sqlite.select([posData]) 
                ResultSet = connection.execute(query).fetchall()
                max: int = status[db]

                for record in ResultSet[max:]:
                    created_at = record[1]
                    source = record[2]
                    content = record[3]
                    local_tz = pytz.timezone("America/Sao_Paulo")
                    created_at = created_at.replace(tzinfo=pytz.utc).astimezone(local_tz).isoformat()
                    _db.save_pos(created_at, source, content)
                status[db] = len(ResultSet)    
            except:
                logging.debug('The service has been terminated.')
                sys.exit(0)

        print("Done")
        with open('sqlite_status.json', 'w') as convert_file:
            json.dump(status, convert_file)
        sleep(5)



def main():
    logging.basicConfig(
        format="[%(asctime)s] %(message)s",
        level=logging.DEBUG,
        handlers=[
            logging.handlers.RotatingFileHandler(
                f"{ os.path.dirname(os.path.abspath(__file__)) }/sqliteservice.txt",
                maxBytes=1024 * 1024,
                backupCount=10
            ),
        ]
    )
    start()

if __name__ == "__main__":
    print("Being called as SQLite Service")
    main()
