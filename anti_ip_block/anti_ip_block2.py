#
# 主进程异步请求， 一子进程
#

import asyncio
import aiohttp.client_exceptions as ex
import time
import os
from multiprocessing import Process, Queue, freeze_support
import concurrent.futures as exc
from lxml import etree
import aiohttp
import dbRedis, mycookie


headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"}

url = "http://www.glidedsky.com/level/web/crawler-ip-block-2"
url_base2 = "http://www.glidedsky.com/level/web/crawler-basic-2"


def generator(*, page=None):
    """主进程：（url,proxy）的生成器"""

    # 获取代理
    zdb = dbRedis.RedisZSet("http")
    proxy_list = zdb.get(mode="score", _min=10, _max=10)
    # 获取页码
    if page is None:
        page_need = get_page()
    else:
        page_need = page

    return zip(page_need, proxy_list)


def get_page():
    """主进程：返回未完成页码 列表， 用于再次请求"""
    hdb = dbRedis.RedisHash()
    page_down = hdb.get(mode="ks")
    if page_down:
        page_down = [int(i) for i in page_down]
        page_down.sort()
        page_down_max = page_down[-1]
        page_down_min = page_down[0]
        page_con = [i for i in range(page_down_max + 1, 1001)]
        page_need = []
        for i in range(page_down_min, page_down_max + 1):
            if i not in page_down:
                page_need.append(i)
        page_need.extend(page_con)
        page_need.sort()
    else:
        page_need = (i for i in range(1, 1001))
    return page_need


async def get_nums(page, ip, queue1, queue2):
    """主进程：专注于异步请求，"""
    url_page = url + f"?page={page}"
    proxy = f"http://{ip}"
    # conn = aiohttp.TCPConnector()
    fail_page = []
    try:
        async with aiohttp.ClientSession(cookies=cookie) as session:
            async with session.get(url_page, proxy=proxy, timeout=22, headers=headers) as resp:
                if resp.status == 200:
                    text = await resp.read()
                    queue1.put((text, page, ip))
                elif resp.status == 403:
                    print("该代理已用过")
                    queue2.put((ip, 200))   # 403被封IP，表示该IP可用
                    fail_page.append(page)
                else:
                    print(resp.status)
                    queue2.put((ip, 4))     # 给三次机会

    except (ex.ServerConnectionError, ex.ClientOSError, ex.ClientHttpProxyError, exc.TimeoutError) as e:
        queue2.put((ip, 0))            # 直接移除
        fail_page.append(page)

    except Exception as e:
        print(type(e),e)
        queue2.put((ip, 5))           # 给两次机会
        fail_page.append(page)

    return fail_page


def proc1_parser(queue1):
    """子进程1：用于解析网页，操作数据库保存有用数据，置分该有用代理"""
    zdb = dbRedis.RedisZSet("http")
    hdb = dbRedis.RedisHash()
    while 1:
        text, page, ip = queue1.get()
        if (text, page, ip) == (False,) * 3:
            print("增加任务已完成")
            break
        else:
            try:
                tree = etree.HTML(text)
                numbers = tree.xpath('//div[@class="row"]/div/text()')
                numbers = [i.strip() for i in numbers]
                _sum = "+".join(numbers)
                _sum = str(eval(_sum))
                hdb.add(key=page, value=_sum)
                zdb.update(ip, 200)
            except SyntaxError:
                print("代理需登录 ", end="")
                zdb.minus(ip, account=201)
            except Exception as e:
                print(ip, "状态200", type(e), e)
                zdb.update(ip, 403)


def proc2_minus(queue2):
    """子进程2：用于操作数据库删除无用代理"""
    zdb = dbRedis.RedisZSet("http")
    while 1:
        ip, account = queue2.get()
        if (ip, account) == (False,) * 2:
            print("删除任务已完成")
            break
        elif account == 200:
            zdb.update(ip,account)
        else:
            zdb.minus(ip, account=account)


def load_db(need_total=False):
    """展示统计情况，完成最后的计算"""
    hdb = dbRedis.RedisHash()
    length = hdb.get(mode='len')
    result = hdb.get(mode="vs")
    if need_total:
        total = 0
        for i in result:
            total += int(i)
        return length, total
    else:
        return length


async def main(queue1, queue2):
    """主进程：专注异步请求"""
    flag = 0
    while 1:
        flag += 1
        page_need = None
        page_zip = generator(page=page_need)
        tasks = [asyncio.create_task(get_nums(p, i, queue1, queue2)) for p, i in page_zip]
        pages_fail = [await t for t in tasks]  # 以列表形式返回每个任务的返回值
        print(f"{'*'*55}第 {flag} 轮异步请求 结束")
        if not pages_fail:
            print(f"{'*'*55}共 {flag} 轮异步请求 全部完成")
            break
        page_need = [i[0] for i in pages_fail if i != []]
        time.sleep(3)           # 需动态变
        print(f"{'*'*55}第 {flag+1} 轮异步请求 启动")


def run():
    """进程控制器（1主2子）"""

    queue1 = Queue()
    queue2 = Queue()
    proc1 = Process(target=proc1_parser, args=(queue1,))  # 检测中解析
    proc2 = Process(target=proc2_minus, args=(queue2,))  # 检测中移除无用代理
    # proc3 = Process(target=crawl_kdl.main)               # 爬代理

    t11 = time.perf_counter()
    len_start = load_db()

    # proc3.start()
    # time.sleep(60)             # 先爬个一分钟
    proc1.start()
    proc2.start()
    asyncio.run(main(queue1, queue2))
    queue1.put((False,) * 3)
    queue2.put((False,) * 2)

    proc1.join()
    proc2.join()

    len_end, total = load_db(need_total=True)
    t12 = time.perf_counter()

    print("新增：", len_end-len_start, "已完成：", len_end, "还有：", 1000 - len_end)
    print("当前总和：", total)
    print("运行时长:", t12 - t11)


if __name__ == '__main__':
    freeze_support()
    mycookie.get_cookie()
    cookie = mycookie.load_cookie()
    run()
    os.system("pause")