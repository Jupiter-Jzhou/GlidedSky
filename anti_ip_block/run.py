#启动代理池

import proxy_pool
from multiprocessing import freeze_support, Process
import os

if __name__ == '__main__':
    freeze_support()

    proc1 = Process(target=proxy_pool.run, args=("nma", [i for i in range(1, 750)]))
    proc2 = Process(target=proxy_pool.run, args=("yun", [i for i in range(1, 8)]))
    proc1.start()
    proc2.start()

    proc1.join()
    proc2.join()

    os.system("pause")