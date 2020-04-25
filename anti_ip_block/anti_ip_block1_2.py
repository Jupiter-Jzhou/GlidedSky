import asyncio
import aiohttp.client_exceptions as ex
from multiprocessing import Process, Queue
from time import sleep
import time
import concurrent.futures as exc
from lxml import etree
import aiohttp
from tools import mycookie, dbRedis

headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"}

url = "http://glidedsky.com/level/web/crawler-ip-block-1"
url_base2 = "http://glidedsky.com/level/web/crawler-basic-2"


def generator(*, page=None):
    """一页url配一个proxy"""

    # 获取代理
    db = dbRedis.RedisZSet()
    proxy_list = db.get(mode="score", _min=0, _max=199)
    # 获取页码
    if page is None:
        page_need = get_page()
    else:
        page_need = page

    return zip(page_need, proxy_list)


def get_page():
    """返回未完成页码 列表"""
    hdb = dbRedis.RedisHash()
    page_down = hdb.get(mode="ks")
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

    return page_need


async def get_nums(page, ip):
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
                else:
                    queue2.put((ip, 201))
                    fail_page.append(page)

    except (ex.ServerConnectionError, ex.ClientOSError, ex.ClientHttpProxyError, exc.TimeoutError) as e:
        queue2.put((ip, 201))
        fail_page.append(page)

    except Exception as e:
        queue2.put((ip, 5))
        fail_page.append(page)

    return fail_page


def parser(q1):
    zdb = dbRedis.RedisZSet()
    hdb = dbRedis.RedisHash()
    while 1:
        text, page, ip = q1.get()
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
                zdb.add(ip, score=200)
            except Exception as e:
                print(ip, "状态200", type(e), e)


def minus(q2):
    zdb = dbRedis.RedisZSet()
    while 1:
        ip, account = q2.get()
        if (ip, account) == (False,) * 2:
            print("删除任务已完成")
            break
        else:
            zdb.minus(ip, account=account)


def load_db():
    """展示统计情况，完成最后的计算"""
    db = dbRedis.RedisHash()
    length = db.get(mode='len')
    result = db.get(mode="vs")
    total = 0
    for i in result:
        total += int(i)
    print("已完成：", length, "还有：", 1000 - length)
    print("当前总和：", total)


async def run():
    while 1:
        page_need = None
        page_zip = generator(page=page_need)
        tasks = [asyncio.create_task(get_nums(p, i)) for p, i in page_zip]
        pages_fail = [await t for t in tasks]  # 以列表形式返回每个任务的返回值
        print("一轮结束")
        if pages_fail == []:
            break
        sleep(3)     # 需动态变
        page_need = [i[0] for i in pages_fail if i != []]
        print(page_need)
        print("再次启动")


if __name__ == '__main__':
    mycookie.get_cookie()
    cookie = mycookie.load_cookie()
    queue1 = Queue()
    queue2 = Queue()
    proc1 = Process(target=parser, args=(queue1,))
    proc2 = Process(target=minus, args=(queue2,))
    t11 = time.perf_counter()
    proc1.start()
    proc2.start()
    asyncio.run(run())
    queue1.put((False,) * 3)
    queue2.put((False,) * 2)

    proc1.join()
    proc2.join()
    load_db()
    t12 = time.perf_counter()

    print("运行时长:", t12 - t11)
