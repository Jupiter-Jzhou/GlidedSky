from multiprocessing import Pool, Manager


def pool_console(func, processes, iterator,
                 *, mode="mode1", special_kwargs=None):
    """ 多进程池控制台
    :param func: 目标函数（专注业务逻辑）
    :param processes: 进程数
    :param iterator: 迭代器，目标函数需要处理的任务
    :param mode: 选择进程间通信的方式
                mode1: 全选，返回 成功的计数（int)和成功的结果（generator）
                mode2: 不需要counter, queue1, queue2，lock送进目标函数, 无返回值
    :param special_kwargs: 传递给目标函数的额外参数，字典
    """

    pool = Pool(processes=processes)

    # 所需同步工具
    queue1 = queue2 = lock = counter = None
    m = Manager()
    if mode == "mode1":
        counter = m.Value('i', 0)
        lock = m.Lock()
        queue1 = m.Queue()      # 传送未处理成功的
        queue2 = m.Queue()      # 传送处理成功的
    if mode == "mode2":
        lock = m.Lock()
        if special_kwargs is None:
            special_kwargs = {}
        special_kwargs.update(lock=lock)

    task_total = 0  # 任务数总数
    for task in iterator:
        task_total += 1
        pool.apply_async(operator, (func, task, special_kwargs, counter, lock, queue1, queue2))
    if counter is not None:
        while counter.value <= task_total:
            # lock.acquire()
            # flag = get_pbar(counter.value, task_total)
            # lock.release()
            while not queue1.empty():
                lock.acquire()
                print("\r重新加入进程池", end='')
                lock.release()
                pool.apply_async(operator, (func, queue1.get(), special_kwargs, counter, lock, queue1, queue2))
        else:
            lock.acquire()
            get_pbar(counter.value, task_total)
            lock.release()
    pool.close()
    pool.join()
    if mode == "mode1":
        result = gen_result(queue2)
        return result


def gen_result(queue2):
    """结果生成器"""
    while not queue2.empty():
        yield queue2.get()


def operator(func, task, special_kwargs, counter, lock, queue1, queue2):
    """多进程的目标函数的共同部分
    :param func: 目标函数（专注业务逻辑）
    :param task: 目标函数要处理的任务，在生成器中需迭代的参数
    :param special_kwargs: 该目标函数所特有的参数，传入传出都是字典，到目标函数中解包
    :param counter: 任务完成数目计数器, 用于进度条，重新加入池也依赖counter来做判断
    :param lock: 进程锁
    :param queue1: 用于传出失败的任务，用于再次加入进程池
    :param queue2: 用于传出任务成功后要返回的内容
    :return: None,通过队列返回了
    """
    try:
        if special_kwargs is None:
            result = func(task)
        else:
            result = func(task, special_kwargs)
        if counter is not None or result is not None:
            lock.acquire()  # 必须上锁 不然 同时发生的会覆盖
            counter.value += 1
            # print("ok", end='')
            lock.release()
            if queue2 is not None:
                queue2.put(result)  # 任务成功，返回所需处理结果  result不可是生成器

    except Exception as e:
        lock.acquire()  # 必须上锁 不然 同时发生的会覆盖
        print("\nexcept", e)
        lock.release()
        if queue1 is not None:
            queue1.put(task)  # 任务失败，把该任务返回


def get_pbar(num, total):
    """进度条
    :param num: 当前数
    :param total: 总数
    :return: None
    """
    max_tep = 50  # 进度条的长度
    a = int(num / total * max_tep // 1)
    b = '[' + '>' * a + ' ' * (max_tep - a) + ']'
    c = str(int(100 / max_tep * a))
    print('\r{0}{1}%'.format(b, c), end='')
    if num == total:
        print('')
        return True
    else:
        return False

