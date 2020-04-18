import requests
import time
import random
from multiprocessing import Process, Queue
from lxml import etree
from tools import dbRedis

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0',
           "Accept-Encoding": "gzip, deflate, br"}

url_kdl = "https://www.kuaidaili.com"


def crawler(sess, url_page, referer, queue1):
    """专注于网络请求，返回网页文本，并记录失败的页码，用于再次请求"""

    headers.update(referer=referer)
    page_failed = []
    try:
        r = sess.get(url_page, headers=headers)
        if r.status_code == 200:
            queue1.put(r.text)
        else:
            print(r.status_code)
            page_failed.append((url_page, referer))
    except Exception as e:
        print(type(e), e)
        page_failed.append((url_page, referer))

    return page_failed


def parser(q1):
    """解析网页，获得代理，并写入数据库"""
    # ldb = dbRedis.RedisList(list_name="kdl_page")
    zdb2 = dbRedis.RedisZSet()  # 公用的存储代理池
    while 1:
        text = q1.get()
        if text is False:
            print("获取代理任务已完成: 快代理")
            break
        tree = etree.HTML(text)
        trs = tree.xpath('//tbody/tr')
        for tr in trs:
            ip = tr.xpath('./td[@data-title="IP"]/text()')[0]
            port = tr.xpath('./td[@data-title="PORT"]/text()')[0]
            proxy = ":".join([ip, port])
            zdb2.add(proxy)            # 相同的会覆盖


def make_url(page):
    """制作每页的url 和 referer"""
    if page == 1:
        url_page = url_kdl + "/free/"
        referer = url_kdl
    elif page == 2:
        url_page = url_kdl + f"/free/inha/{page}/"
        referer = url_kdl + "/free/"
    else:
        url_page = url_kdl + f"/free/inha/{page}/"
        referer = url_kdl + f"/free/inha/{page - 1}/"

    return url_page, referer


def run(queue1):
    PAGE_START = 201
    PAGE_END = 600
    with requests.Session() as sess:  # 这样才能共享每次请求的cookie
        for page in range(PAGE_START, PAGE_END + 1):
            url_page, referer = make_url(page)
            while 1:
                time.sleep(random.randint(1, 3))
                page_failed = crawler(sess, url_page, referer, queue1)
                if not page_failed:
                    print("正常结束: ", page)
                    break
                url_page, referer = page_failed[0]
    queue1.put(False)  # 结束标志


def main():
    queue1 = Queue()
    proc1 = Process(target=parser, args=(queue1,))
    zdb = dbRedis.RedisZSet()

    start = zdb.count(_min=10, _max=10)
    t11 = time.perf_counter()

    proc1.start()
    run(queue1)
    proc1.join()

    t12 = time.perf_counter()
    end = zdb.count(_min=10, _max=10)

    print("新增代理:", end - start)
    print("爬取代理任务运行时长:", t12 - t11)


if __name__ == '__main__':
    main()
