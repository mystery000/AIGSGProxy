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
            exit()

        self._last_check = now