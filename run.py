import multiprocessing as mp

from samba_svc import run_app
from web import run_web
# from proxy_svc import run_proxy


def main():
    queue = mp.Queue(maxsize=100)

    app = mp.Process(target=run_app, args=(queue, True))
    app.start()

    web = mp.Process(target=run_web, args=(queue, True))
    web.start()

    # proxy = mp.Process(target=run_proxy, args=(queue, True))
    # proxy.start()

    app.join()
    web.join()
    # proxy.join()


if __name__ == "__main__":
    mp.set_start_method("spawn")
    main()