from multiprocessing import Pool, Manager


def pool_console(func, processes, iterator,
                 *, mode="mode1", queue1=False, queue2=False, lock=False, counter=False,
                 **special_kwargs):
    """ 多进程池控制台
    :param func: 目标函数（专注业务逻辑）
    :param processes: 进程数
    :param iterator: 迭代器，目标函数需要处理的任务
    :param mode: 选择进程间通信的方式
    :param queue1: 此队列传出失败的任务，用于再次加入进程池
    :param queue2: 此队列传出任务成功后需要返回的结果
    :param lock: 进程锁
    :param counter: 任务完成数计数器
    :param special_kwargs: 目标函数的特定参数，字典
    :return: 完成任务数，成功任务结果列表
    """

    pool = Pool(processes=processes)

    # 所需同步工具
    if mode or queue1 or queue2 or lock or counter:
        m = Manager()
        if mode == "mode1":
            queue1 = queue2 = lock = counter = True
        if counter:
            counter = m.Value('i', 0)
        if lock:
            lock = m.Lock()
        if queue1:                 # 传送未处理成功的
            queue1 = m.Queue()
        if queue2:                # 传送处理成功的
            queue2 = m.Queue()

    task_total = 0        # 任务数总数
    try:
        for task in iterator:
            task_total += 1
            pool.apply_async(operator, (func, task, special_kwargs, counter, lock, queue1, queue2))
        while counter.value < task_total:
            get_pbar(counter.value, task_total)
            while not queue1.empty():
                print("\r重新加入进程池", end='')
                pool.apply_async(operator, (func, queue1.get(), special_kwargs, counter, lock, queue1, queue2))

    finally:
        pool.close()
        pool.join()
        get_pbar(counter.value, task_total)           # 最后一个上面输出不了
        # while not queue1.empty():
        #     print(queue1.get())
        result = []
        while not queue2.empty():
            result.extend(queue2.get())

        return counter.value, result


def operator(func, task, special_kwargs, counter, lock, queue1, queue2):
    """多进程的目标函数的共同部分
    :param func: 目标函数（专注业务逻辑）
    :param task: 目标函数要处理的任务，在生成器中需迭代的参数
    :param special_kwargs: 该目标函数所特有的参数，传入传出都是字典，到目标函数中解包
    :param counter: 任务完成数目计数器
    :param lock: 进程锁
    :param queue1: 用于传出失败的任务，用于再次加入进程池
    :param queue2: 用于传出任务成功后要返回的内容
    :return: None,通过队列返回了
    """
    try:
        result = func(task, special_kwargs)
        lock.acquire()  # 必须上锁 不然 同时发生的会覆盖
        counter.value += 1
        lock.release()
        queue2.put(result)     # 任务成功，返回所需处理结果
    except Exception as e:
        print("except", e)
        queue1.put(task)       # 任务失败，把该任务返回


def get_pbar(num, total):
    """进度条
    :param num: 当前数
    :param total: 总数
    :return: None
    """

    max_tep = 50        # 进度条的长度
    a = int(num / total * max_tep // 1)
    b = '[' + '>' * a + ' ' * (max_tep - a) + ']'
    c = str(int(100 / max_tep * a))
    print('\r{0}{1}%'.format(b, c), end='')
    if num == total:
        print('')


