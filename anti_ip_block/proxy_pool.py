#
# 两进程，主进程可同步也可异步请求(mode来选择，默认同步)，子进程解析
# 可选择多个代理网站（crawl_web来选择），
# 目前有西刺、快代理、云代理（仅同步）、尼玛代理（仅同步）、66代理（resp.encoding = "gb2312"）
#

import asyncio
import json
from multiprocessing import Process, Queue
import random
import time

import aiohttp
from lxml import etree
import requests

import dbRedis

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
           "Accept-Encoding": "gzip, deflate"}
proxy_local = "http://127.0.0.1:25379"


def gen_pages_xla(page_need):
    url_home = "http://www.xiladaili.com/"
    url_gaoni = "http://www.xiladaili.com/gaoni/"   # 含https
    for page in page_need:
        if page == 1:
            url_page = url_gaoni
            referer = url_home
        elif page == 2:
            url_page = url_gaoni + f"{page}/"
            referer = url_gaoni
        else:
            url_page = url_gaoni + f"{page}/"
            referer = url_gaoni + f"{page-1}/"

        yield url_page, referer


def gen_pages_66ip(page_need):
    url_home = "http://www.66ip.cn"
    for page in page_need:
        if page == 1:
            url_page = url_home
            referer = url_home
        elif page == 2:
            url_page = url_home + f"/{page}.html"
            referer = url_home
        else:
            url_page = url_home + f"/{page}.html"
            referer = url_home + f"/{page-1}.html"

        yield url_page, referer


def gen_pages_yun(page_need):
    url_home = "http://www.ip3366.net"
    url_free = "http://www.ip3366.net/free"

    for page in page_need:
        if page == 1:
            url_page = url_free
            referer = url_home
        elif page == 2:
            url_page = url_free + f"/?stype=1&page={page}"
            referer = url_free
        else:
            url_page = url_free + f"/?stype=1&page={page}"
            referer = url_free + f"/?stype=1&page={page-1}"

        yield url_page, referer


def gen_pages_nma(page_need):
    url_http = "http://www.nimadaili.com/http"
    url_home = "http://www.nimadaili.com"
    for page in page_need:
        if page == 1:
            url_page = url_http
            referer = url_home
        elif page == 2:
            url_page = url_http + f"/{page}/"
            referer = url_http
        else:
            url_page = url_http + f"/{page}/"
            referer = url_http + f"/{page - 1}/"

        yield url_page, referer


def gen_pages_kdl(page_need):
    """制作每页的url 和 referer"""
    url_kdl = "https://www.kuaidaili.com"
    for page in page_need:
        if page == 1:
            url_page = url_kdl + "/free/"
            referer = url_kdl
        elif page == 2:
            url_page = url_kdl + f"/free/inha/{page}/"
            referer = url_kdl + "/free/"
        else:
            url_page = url_kdl + f"/free/inha/{page}/"
            referer = url_kdl + f"/free/inha/{page - 1}/"

        yield url_page, referer


def gen_pages_xci(page_need):

    url_home = "https://www.xicidaili.com"
    url_nn = "https://www.xicidaili.com/nn"
    for page in page_need:
        if page == 1:
            url_page = url_nn
            referer = url_home
        elif page == 2:
            url_page = url_nn + f"/{page}"
            referer = url_nn
        else:
            url_page = url_nn + f"/{page}"
            referer = url_nn + f"/{page - 1}"

        yield url_page, referer


def parser_xla(queue1):
    zdb_http = dbRedis.RedisZSet("http")
    # flag = 0
    while 1:
        text = queue1.get()
        if text is False:
            print("获取代理任务已完成: 西拉代理")
            break
        tree = etree.HTML(text)
        trs = tree.xpath('//tbody/tr')
        for tr in trs:
            proxy = tr.xpath('./td')[0].xpath('./text()')[0]
            zdb_http.add(proxy)            # 仅新
            # flag += 1
            # print(flag, proxy)


def parser_66ip(queue1):
    zdb_http = dbRedis.RedisZSet("http")
    # flag = 0
    while 1:
        text = queue1.get()
        if text is False:
            print("获取代理任务已完成: 66代理")
            break
        tree = etree.HTML(text)
        trs = tree.xpath('//div[@id="main"]//table/tr')
        for tr in trs[1:]:
            ip = tr.xpath('./td')[0].xpath('./text()')[0]
            port = tr.xpath('./td')[1].xpath('./text()')[0]
            proxy = ":".join([ip, port])
            zdb_http.add(proxy)  # 只添加新的
            # flag += 1
            # print(flag, proxy)


def parser_yun(queue1):
    zdb_http = dbRedis.RedisZSet("http")
    # flag = 0
    while 1:
        text = queue1.get()
        if text is False:
            print("获取代理任务已完成: 云代理")
            break
        tree = etree.HTML(text)
        trs = tree.xpath('//tbody/tr')
        for tr in trs:
            ip = tr.xpath('./td')[0].xpath('./text()')[0]
            port = tr.xpath('./td')[1].xpath('./text()')[0]
            proxy = ":".join([ip, port])
            zdb_http.add(proxy)  # 相同的会覆盖
            # flag += 1
            # print(flag, proxy)


def parser_nma(queue1):
    zdb_http = dbRedis.RedisZSet("http")
    # flag = 0
    while 1:
        text = queue1.get()
        if text is False:
            print("获取代理任务已完成: 尼玛代理")
            break
        tree = etree.HTML(text)
        trs = tree.xpath('//tbody/tr')
        for tr in trs:
            proxy = tr.xpath('./td')[0].xpath('./text()')[0]
            zdb_http.add(proxy)            # 仅新
            # flag += 1
            # print(flag, proxy)


def parser_kdl(queue1):
    """解析网页，获得代理，并写入数据库"""

    zdb_http = dbRedis.RedisZSet("http")
    while 1:
        text = queue1.get()
        if text is False:
            print("获取代理任务已完成: 快代理")
            break
        tree = etree.HTML(text)
        trs = tree.xpath('//tbody/tr')
        for tr in trs:
            ip = tr.xpath('./td[@data-title="IP"]/text()')[0]
            port = tr.xpath('./td[@data-title="PORT"]/text()')[0]
            proxy = ":".join([ip, port])
            zdb_http.add(proxy)            # 仅新


def parser_xci(queue1):
    """子程序 解析出proxy 写入数据库"""
    zdb_http = dbRedis.RedisZSet("http")
    zdb_https = dbRedis.RedisZSet("https")

    while 1:
        text = queue1.get()             # 空则一直阻塞
        if text is False:
            print("获取代理任务已完成: 西刺代理")
            break
        tree = etree.HTML(text)
        trs = tree.xpath('//table[@id="ip_list"]//tr')
        for tr in trs[1:]:
            style = tr.xpath('./td')[5].xpath('./text()')[0]
            ip = tr.xpath('./td')[1].xpath('./text()')[0]
            port = tr.xpath('./td')[2].xpath('./text()')[0]
            proxy = ":".join([ip, port])
            if style == 'HTTPS':
                zdb_http.add(proxy)
            else:
                zdb_https.add(proxy)


def write_failed_pages(pages_failed):
    file = json.dumps(pages_failed)
    with open("proxy_failed_pages.txt", "a+") as f:
        f.write(file)
        f.write("\n")


async def async_crawler(page, queue1):
    """
    :param page: (url_page,referer)
    :param queue1: 用来传递响应体的内容的队列
    :return page_failed: (url_page,referer),异步返回的是每个任务的返回值的列表，这里即是元组的列表
    """
    page_failed = None
    url_page = page[0]
    referer = page[1]

    try:
        async with aiohttp.ClientSession() as session:    # 异步会话自动保持cookie的功能
            headers.update(referer=referer)
            # vpn网页浏览器全局下， requests会自己用代理，aiohttp需要自己加代理
            async with session.get(url_page, headers=headers, timeout=22, proxy=proxy_local) as resp:
                if resp.status == 200:
                    text = await resp.read()
                    queue1.put(text)
                else:
                    print(resp.status)
                    page_failed = page
    except Exception as e:
        print(type(e), e)
        page_failed = page

    return page_failed


async def async_main(crawl_web, page_gen, queue1):
    """"""
    flag = 0
    while 1:
        flag += 1
        tasks = [asyncio.create_task(async_crawler(page, queue1)) for page in page_gen]
        pages_failed = await asyncio.gather(*tasks)
        # pages_failed = [await t for t in tasks]   #  等效上一句

        print(f"{crawl_web} 第{flag}轮异步请求 已完成")
        if set(pages_failed) == {None}:
            break
        elif flag == 3:
            break
        else:
            page_gen = [i for i in pages_failed if i is not None]
            print(page_gen)
            print(f"{crawl_web} 第{flag+1}轮异步请求 启动")

    return pages_failed  # 异步请求等所有完成后才返回所有任务的结果列表


def crawler(sess, url_page, referer, queue1):
    """
    主进程 爬 返回成功的结果或失败的页
    """
    page_failed = None

    try:
        headers.update(referer=referer)
        with sess.get(url_page, timeout=22, headers=headers) as resp:
            if resp.status_code == 200:
                queue1.put(resp.text)
            else:
                print(resp.status_code)
                page_failed = {url_page: referer}
    except Exception as e:
        print(e)
        page_failed = {url_page: referer}

    return page_failed


def main(crawl_web, page_gen, queue1):

    with requests.Session() as sess:  # 这样才能共享每次请求的cookie
        pages_failed = []  # 用于装 失败三次后的页面
        for url_page, referer in page_gen:
            flag = 0  # 某页失败3次后，记录该页，不再重新请求
            while 1:
                flag += 1
                page_failed = crawler(sess, url_page, referer, queue1)
                if page_failed is None:
                    break
                elif flag == 3:
                    pages_failed.append(page_failed)
                    break
                else:
                    print(f"{crawl_web} 重试: ", url_page)
                    url_page, referer = page_failed
                    time.sleep(random.randint(1, 2))  # 纯请求时间 0.5s左右
            time.sleep(random.randint(1, 2))    # 纯请求时间 0.5s左右

        return pages_failed


def run(crawl_web, page_need, mode=None):
    """进程控制器：1主1子
    :param crawl_web: 不同代理网站 用于选择 动态请求参数（u:url_page r:referer p:proxy）的生成器 和 网页解析器
                        "xci": 西刺代理
                        "kdl": 快代理
    :param page_need: 需要爬取的页码的列表或生成器
    :param mode: None: 同步请求
                 async: 异步请求
    """

    queue1 = Queue()

    if crawl_web == "xci":
        page_gen = gen_pages_xci(page_need)
        proc1 = Process(target=parser_xci, args=(queue1,))
    elif crawl_web == "kdl":
        page_gen = gen_pages_kdl(page_need)
        proc1 = Process(target=parser_kdl, args=(queue1,))
    elif crawl_web == "nma":
        page_gen = gen_pages_nma(page_need)
        proc1 = Process(target=parser_nma, args=(queue1,))
    elif crawl_web == "yun":
        page_gen = gen_pages_yun(page_need)
        proc1 = Process(target=parser_yun, args=(queue1,))
    elif crawl_web == "66ip":
        page_gen = gen_pages_66ip(page_need)
        proc1 = Process(target=parser_66ip, args=(queue1,))
    elif crawl_web == "xla":
        page_gen = gen_pages_xla(page_need)
        proc1 = Process(target=parser_xla, args=(queue1,))
    else:
        page_gen = proc1 = None
        exit("请正确输入代理网站编号")

    zdb_http = dbRedis.RedisZSet("http")
    zdb_https = dbRedis.RedisZSet("https")

    start1 = zdb_http.count(_min=10, _max=10)
    start2 = zdb_https.count(_min=10, _max=10)
    t11 = time.perf_counter()

    proc1.start()

    if mode == "async":
        pages_failed = asyncio.run(async_main(crawl_web, page_gen, queue1))
    else:
        pages_failed = main(crawl_web, page_gen, queue1)

    queue1.put(False)  # 结束解析子进程的标志

    write_failed_pages(pages_failed)
    proc1.join()

    t12 = time.perf_counter()
    end1 = zdb_http.count(_min=10, _max=10)
    end2 = zdb_https.count(_min=10, _max=10)

    print("新增HTTP代理:", end1 - start1, " "*7, "新增HTTPS代理:", end2 - start2)
    print(f"{crawl_web}: 爬取时长:", t12 - t11)


if __name__ == '__main__':
    page_need = (i for i in range(1, 101))
#     # run("xci", 3, 3, mode="async")
#     # run("kdl", page_need)
#     # run("xci", page_need)
#     # run("nma", page_need)
#     # run("yun", page_need)
#     run("66ip", page_need)
    run("xla", page_need)


