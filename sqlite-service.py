import os
import sys
import logging
from time import sleep
import logging.handlers
from threading import Timer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import sqlalchemy as sqlite
import pytz
from db import Db

def start():
    SQLALCHEMY_DATABASE_URL = f"sqlite:///./data.sqlite3"
    engine = sqlite.create_engine(
        SQLALCHEMY_DATABASE_URL,
    ) 
    logging.info(f"Connected: { SQLALCHEMY_DATABASE_URL }, { __name__ }")
    _db: Db = Db()
    
    max: int = 0
    try:
        f = open('sqlite-conf.txt', 'r')
        max = int(f.read())
    except:
        pass
        
    while True:
        try:
            connection = engine.connect()
            metadata = sqlite.MetaData()
            posData = sqlite.Table('pos_data', metadata, autoload=True, autoload_with=engine)
            query = sqlite.select([posData]) 
            ResultSet = connection.execute(query).fetchall()
            
            for record in ResultSet[max:]:
                created_at = record[1]
                source = record[2]
                content = record[3]
                local_tz = pytz.timezone("America/Sao_Paulo")
                created_at = created_at.replace(tzinfo=pytz.utc).astimezone(local_tz).isoformat()
                _db.save_pos(created_at, source, content)   

            f = open('sqlite-conf.txt', 'w')
            max = len(ResultSet)
            f.write(str(max))
            print('Done')
            sleep(5)
        except:
            f.close()
            logging.debug('The service has been terminated.')
            sys.exit(0)
    
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
