import asyncio
import aiohttp.client_exceptions as ex
import time
import concurrent.futures as exc
from lxml import etree
import aiohttp
from tools import mycookie, dbRedis

headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"}

url = "http://www.glidedsky.com/level/web/crawler-ip-block-1"
url_base2 = "http://www.glidedsky.com/level/web/crawler-basic-2"


def generator():
    """一页url配一个proxy"""

    # 获取代理
    db = dbRedis.RedisZSet()
    proxy_list = db.get(mode="score", _min=0, _max=199)
    # 获取页码
    page_need = get_page()
    # page_need = (i for i in range(1, 1001))

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
    zdb = dbRedis.RedisZSet()
    hdb = dbRedis.RedisHash()
    conn = aiohttp.TCPConnector()
    try:
        async with aiohttp.ClientSession(cookies=cookie, connector=conn) as session:
            async with session.get(url_page, proxy=proxy, timeout=22, headers=headers) as resp:
                status = resp.status
                text = await resp.read()

    except (ex.ServerConnectionError, ex.ClientOSError, ex.ClientHttpProxyError, exc.TimeoutError) as e:
        print(type(e), e)
        zdb.minus(ip, account=201)
    except Exception as e:
        print(type(e), e)
        zdb.minus(ip, account=5)
    else:
        if status == 200:
            try:
                _sum = parser(text)
                hdb.add(key=page, value=_sum)
                zdb.add(ip, score=200)
            except Exception as e:
                print(ip, "状态200", type(e), e)
        else:
            print(f"fail {status} ")
            zdb.minus(ip, account=201)


def parser(text):
    tree = etree.HTML(text)
    numbers = tree.xpath('//div[@class="row"]/div/text()')
    numbers = [i.strip() for i in numbers]
    _sum = "+".join(numbers)
    _sum = str(eval(_sum))
    return _sum


def load_db():
    """展示统计情况，完成最后的计算"""
    db = dbRedis.RedisHash()
    length = db.get(mode='len')
    result = db.get(mode="vs")
    total = 0
    for i in result:
        total += int(i)
    print("已完成：", length, "还有：", 1000-length)
    print("当前总和：", total)


async def run():

    page_zip = generator()
    tasks =[asyncio.create_task(get_nums(p, i)) for p, i in page_zip]
    [await t for t in tasks]



if __name__ == '__main__':
    mycookie.get_cookie()
    cookie = mycookie.load_cookie()

    t11 = time.perf_counter()
    asyncio.run(run())
    load_db()
    t12 = time.perf_counter()

    print("运行时长:", t12-t11)
