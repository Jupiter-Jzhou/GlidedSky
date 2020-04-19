#
# 两进程，主进程异步请求，子进程解析
#

import asyncio
import time
import random
from multiprocessing import Process, Queue
import aiohttp
from lxml import etree
from tools import dbRedis

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}


url = "https://www.xicidaili.com/nn"  # 国内高匿页
referer = "https://www.xicidaili.com"
headers.update(referer=referer)


async def crawler(page):
    """
    """
    fail_page = []
    url_page = url + f"/{page}"
    print(url_page)
    conn = aiohttp.TCPConnector(limit=3)
    try:
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(url_page, timeout=22, headers=headers) as resp:
                if resp.status == 200:
                    text = await resp.read()
                    queue1.put(text)
                    await asyncio.sleep(random.randint(1, 2))
                else:
                    print(resp.status)
                    fail_page.append(page)
    except Exception as e:
        print(e)
        fail_page.append(page)

    return fail_page


def parser(q1):
    zdb2 = dbRedis.RedisZSet()
    while 1:
        text = q1.get()
        if text is False:
            print("解析任务已完成")
            break
        tree = etree.HTML(text)
        trs = tree.xpath('//table[@id="ip_list"]//tr')
        for tr in trs[1:]:
            # style = tr.xpath('./td')[5].xpath('./text()')[0]
            ip = tr.xpath('./td')[1].xpath('./text()')[0]
            port = tr.xpath('./td')[2].xpath('./text()')[0]
            # if style == 'HTTP':
            proxy = ":".join([ip, port])
            # print(proxy)
            zdb2.add(proxy)


async def run():
    PAGE_START = 1
    PAGE_END = 100
    page_need = range(PAGE_START, PAGE_END+1)
    while 1:
        tasks = [asyncio.create_task(crawler(page)) for page in page_need]
        fail_page = [await t for t in tasks]
        print(fail_page)
        if fail_page == [[]]:
            print("异步请求已完成")
            break
        page_need = [i[0] for i in fail_page if i != []]
        print(page_need)
        print("再次启动")
        time.sleep(3)


def load_db():
    zdb = dbRedis.RedisZSet()
    return zdb.count(_min=10, _max=10)


if __name__ == '__main__':
    zdb = dbRedis.RedisZSet()
    queue1 = Queue()
    proc1 = Process(target=parser, args=(queue1,))
    start = zdb.count(_min=10, _max=10)

    t11 = time.perf_counter()
    proc1.start()
    asyncio.run(run())
    queue1.put(False)
    proc1.join()
    t12 = time.perf_counter()

    end = zdb.count(_min=10, _max=10)
    print("新增代理:", end - start)
    print("运行时长:", t12 - t11)




