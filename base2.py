import requests
from lxml import etree
from tools import mycookie
from multiprocessing import Pool, Manager
import comunits

url = "http://www.glidedsky.com/level/web/crawler-basic-2"
referer = "http://www.glidedsky.com/level/web/crawler-basic-2"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"
}


def get_nums(url_page, cookie, num, queue, queue_nums, lock):
    """多进程操作函数
    :param url_page: 网页地址
    :param cookie
    :return: num_pages: 包含所有页面的所有数字的列表
    """
    num_pages = []
    headers.update(referer=referer)
    try:
        # print("\n进程", os.getpid(), url_page)
        with requests.Session() as sess:
            r = sess.get(url_page, headers=headers, cookies=cookie, timeout=3.5)
            tree = etree.HTML(r.text)
            nums = tree.xpath('//div[@class="row"]/div/text()')
            nums = [int(i.strip()) for i in nums]
            num_pages.extend(nums)
        lock.acquire()              # 必须上锁 不然 同时发生的会覆盖
        num.value += 1
        lock.release()
        queue_nums.put(num_pages)
        # print("\n进程", os.getpid(), url_page, "结束")
    except:
        # print("\n进程", os.getpid(), url_page, "出错")
        queue.put(url_page)


def generator(page_start, page_end):
    """每页url生成器
    :return: url_page: 每页的url，放在循环里就生成了所有页url的生成器
    """
    url_pat = url + "?page={0}"
    for page in range(page_start, page_end+1):
        url_page = url_pat.format(page)
        yield url_page


def run_1():
    page_start = 1
    page_end = 10
    processes = 2
    url_page_gen = generator(page_start, page_end)
    cookie = mycookie.load_cookie()

    pool = Pool(processes=processes)
    m = Manager()
    queue = m.Queue()
    num = m.Value('i', 0)
    queue_nums = m.Queue()
    lock = m.Lock()

    try:
        for url_page in url_page_gen:
            pool.apply_async(get_nums, (url_page, cookie, num, queue, queue_nums, lock))

        while num.value < page_end-page_start+1:
            # 有一种情况，当上一句进来的时候还是满足条件的，到下一句执行的时候，num.value就变了
            comunits.show_bar(num.value, page_end-page_start+1)
            while not queue.empty():
                print("\r重新加入进程池", end='')
                pool.apply_async(get_nums, (queue.get(), cookie, num, queue, queue_nums, lock))

    finally:
        pool.close()
        pool.join()
        comunits.show_bar(num.value, page_end-page_start+1)       # 最后一个上面输出不了
        num_total = []
        total = 0
        while not queue_nums.empty():
            num_total.extend(queue_nums.get())
        print("爬取网页数", num.value)
        print("理应数字个数", num.value*12)
        print("得到数字个数", len(num_total))
        for i in num_total:
            total += i
        print("数字总和：", total)


if __name__ == '__main__':
    # mycookie.get_cookie()
    run_1()
