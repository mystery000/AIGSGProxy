import multiprocessing as mp

from web import run_web

def main():
    queue = mp.Queue(maxsize=100)

    web = mp.Process(target=run_web, args=(queue, True))
    web.start()

    web.join()


if __name__ == "__main__":
    mp.set_start_method("spawn")
    main()