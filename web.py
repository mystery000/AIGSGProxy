import os
import io
import sys
import json
import asyncio
import logging
import uvicorn
from db import Db
import logging.handlers
from yaml import load, dump
import multiprocessing as mp
from logging import StreamHandler
from typing import Dict, List, Set, Union
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, Request, Response, HTTPException

from yaml import load, dump
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from watcher import Watcher

app = FastAPI()
origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name



@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    logging.basicConfig(
            format="[%(asctime)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    "webservice.txt",
                    maxBytes=1024 * 1024,
                    backupCount=100),
            ]
        )
    clientIP = request.client.host
    logging.info(f"The incoming request from {clientIP} has an invalid URL format.")
    
    return JSONResponse(
        status_code=418,
        content={"message": "The request has an invalid URL format"},
    )


from conf import Conf
conf = Conf("conf.yaml")

app_queue: mp.Queue = None
log_queues: Set[asyncio.Queue] = set()

@app.get("/api/stationdata/{station_id}")
async def get_station_data(request: Request, station_id: str = "", From: Union[str, None] = None):
    if From == None: raise UnicornException(name="WrongURL")
    _db: Db = Db()
    result  = _db.get_pos(station_id,From)
    logging.basicConfig(
            format="[%(asctime)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    "logs/Webservice-POS.txt",
                    maxBytes=1024 * 1024,
                    backupCount=100),
            ]
        )
    clientIP = request.client.host
    serverIP = conf.get_agent_host()
    serverPort = conf.get_agent_port()

    url = serverIP + ":" + str(serverPort) + "/api/stationdata/" + station_id + "?From=" + From
    logging.info(clientIP + "---->" + url)
    return { "data": result }

@app.get("/api/samba/{samba_id}")
async def get_samba_data(request: Request, samba_id: str = "", From: Union[str, None] = None):
    if From == None: raise UnicornException(name="WrongURL")
    _db: Db = Db()
    result  = _db.get_samba(samba_id,From)

    logging.basicConfig(
            format="[%(asctime)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    "logs/Webservice-SAMBA.txt",
                    maxBytes=1024 * 1024,
                    backupCount=100),
            ]
        )

    clientIP = request.client.host
    serverIP = conf.get_agent_host()
    serverPort = conf.get_agent_port()

    url = serverIP + ":" + str(serverPort) + "/api/samba/" + samba_id + "?From=" + From
    logging.info(clientIP + "---->" + url)


    return {"data": result}

def do_push_log(obj: Dict):
    global log_queues

    for queue in log_queues:
        try:
            queue.put_nowait(obj)
        except:
            pass

#class WebsocketHandler(StreamHandler):
#    def __init__(self):
#        StreamHandler.__init__(self)

#    def emit(self, record):
#        msg = self.format(record)
#        do_push_log({
#            "type": "web",
#            "message": msg
#        })


def root_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "config"))


def get_resource(path):
    mimetypes = {
        ".css": "text/css",
        ".html": "text/html",
        ".js": "application/javascript",
        ".png": "image/png"
    }
    complete_path = os.path.join(root_dir(), path)
    ext = os.path.splitext(path)[1]
    mimetype = mimetypes.get(ext, "text/html")
    with open(complete_path, "rb") as fp:
        return Response(content=fp.read(), media_type=mimetype)


@app.get("/download-sambalog")
async def download_applog():
    return FileResponse(
        path="samba.txt",
        filename="samba.txt",
        media_type="application/octet-stream")


@app.get("/download-proxylog")
async def download_proxylog():
    return FileResponse(
        path="proxy.txt",
        filename="proxy.txt",
        media_type="application/octet-stream")


@app.get("/download-weblog")
async def download_applog():
    return FileResponse(
        path="web.txt",
        filename="web.txt",
        media_type="application/octet-stream")


@app.get("/cfg")
async def get_cfg():
    with open("conf.yaml", "rt") as fp:
        return load(fp, Loader=Loader)


@app.post("/cfg")
async def set_cfg(body: Dict):
    with open("conf.yaml", "wt") as fp:
        dump(body, fp)

    return {}


@app.post("/push_log")
async def push_log(body: Dict):
    do_push_log(body)

    return {
        "status": "ok"
    }


@app.api_route("/{path_name:path}", methods=["GET"])
def receiver(path_name: str):
    whitelist = [
        "",
        "log",
        "manifest.json"
    ]
    if path_name.endswith(".css") \
            or path_name.endswith(".js") \
            or path_name.endswith(".html") \
            or path_name.endswith(".png") \
            or path_name in whitelist:

        if path_name == "" or path_name == "log":
            path_name = "index.html"

        return get_resource(path_name)


@app.api_route("/{path_name:path}", methods=["POST"])
async def ad_message(req: Request, path_name: str, NAME: str, IP: str, PORT: str):
    name = NAME
    ip = IP
    port = PORT
    if (port is None) or (len(port) == 0):
        port = '1001'

    logging.info(f"Got request for name: '{ name }', ip: '{ ip }', port: '{ port }' (path: '{ path_name }')")

    if app_queue is not None:
        try:
            msg = {
                "IP": ip,
                "NAME": name,
                "PORT": port
            }
            app_queue.put_nowait(msg)
            logging.info(f"Queued message: { json.dumps(msg) }")
        except:
            logging.warn("Can't enqueue message")

    return "<html><body><strong>\nSuccessfully Registered!\n</strong></body></html>"


@app.websocket("/logging")
async def websocket_endpoint(websocket: WebSocket):
    global log_queues

    new_queue = asyncio.Queue()
    log_queues.add(new_queue)

    try:
        await websocket.accept()
        while True:
            obj = await new_queue.get()
            await websocket.send_json(obj)
    except:
        pass

    log_queues.remove(new_queue)


def run_web(queue: mp.Queue, log_to_file: bool, is_debug: bool = False):
    global app_queue

    app_queue = queue

    if log_to_file:
        logging.basicConfig(
            format="[%(asctime)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.handlers.RotatingFileHandler(
                    "logs/web.txt",
                    maxBytes=1024 * 1024,
                    backupCount=10),
            ]
        )
    else:
        logging.basicConfig(
            format="[%(asctime)s] %(message)s",
            level=logging.INFO,
            handlers=[
                logging.StreamHandler(sys.stdout),
            ]
        )
    logging.info("Web logging is working well")
    uvicorn.run(
        "web:app",
        host=conf.get_agent_host(),
        port=conf.get_agent_port(),
        reload=True,
        debug=True,
        workers=1,
        log_level="info")


if __name__ == "__main__":
    print("Beging called as program")
    run_web(None, False, True)