import sqlite3
from datetime import datetime

class Watcher():
    def __init__(self):
        self._last_check = datetime.now()

    def get_scheduled_time(self) -> datetime:
        with open("watcher.txt", "rt") as fp:
            parts = fp.read().strip().split(':')

        now = datetime.now()
        return datetime(now.year, now.month, now.day, int(parts[0]), int(parts[1]), 0)

    def check_schedule(self):
        rtime = self.get_scheduled_time()

        now = datetime.now()
        if self._last_check < rtime and now > rtime:
            conn = sqlite3.connect('data.sqlite3')
            save_date = now.strftime("%d-%b-%Y-%H-%M")
            with open(f"{save_date}.sql", "w") as dump_file:
                for line in conn.iterdump():
                    dump_file.write('%s\n' % line)
            conn.execute("DELETE FROM pos_data")
            conn.commit()
            conn.execute("VACUUM")
            conn.commit()
            conn.close()
            exit()

        self._last_check = now