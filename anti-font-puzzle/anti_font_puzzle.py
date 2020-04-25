import asyncio, base64, re, time
from multiprocessing import Process, Queue
from fontTools.ttLib import TTFont
from lxml import etree
import aiohttp
import mycookie, dbRedis

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"}

xy = [
    '@xMin="49" and @yMin="-13" and @xMax="506" and @yMax="747"',  # 0
    '@xMin="88" and @yMin="0" and @xMax="490" and @yMax="733"',  # 1
    '@xMin="40" and @yMin="0" and @xMax="505" and @yMax="747"',  # 2
    '@xMin="29" and @yMin="-13" and @xMax="499" and @yMax="747"',  # 3
    '@xMin="20" and @yMin="0" and @xMax="523" and @yMax="733"',  # 4
    '@xMin="28" and @yMin="-13" and @xMax="501" and @yMax="733"',  # 5
    '@xMin="56" and @yMin="-13" and @xMax="511" and @yMax="747"',  # 6
    '@xMin="49" and @yMin="0" and @xMax="508" and @yMax="733"',  # 7
    '@xMin="45" and @yMin="-13" and @xMax="509" and @yMax="744"',  # 8
    '@xMin="44" and @yMin="-13" and @xMax="500" and @yMax="747"'  # 9
]
num_map = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
           "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}


######################################################################################
# 主进程

def get_page():
    hdb = dbRedis.RedisHash("font")
    page_down = hdb.get(mode="ks")
    for i in range(1, 1001):
        if str(i) not in page_down:
            yield i


def gen_page(page_need):
    for page in page_need:
        if page == 1:
            url_page = "http://glidedsky.com/level/web/crawler-font-puzzle-1"
            referer = "http://glidedsky.com/level/crawler-font-puzzle-1"
        elif page == 2:
            url_page = "http://glidedsky.com/level/web/crawler-font-puzzle-1?page=2"
            referer = "http://glidedsky.com/level/web/crawler-font-puzzle-1"
        else:
            url_page = f"http://glidedsky.com/level/web/crawler-font-puzzle-1?page={page}"
            referer = f"http://glidedsky.com/level/web/crawler-font-puzzle-1?page={page - 1}"
        yield url_page, referer


async def create_task(page_gen, queue1, ):
    cookie = mycookie.load_cookie()
    conn = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(cookies=cookie, connector=conn) as session:
        tasks = [asyncio.create_task(crawler(session, url_page, referer, queue1))
                 for url_page, referer in page_gen]
        page_failed = await asyncio.gather(*tasks)
    return page_failed


async def crawler(session, url_page, referer, queue1):
    """爬取假数和字体信息"""
    if "?page=" in url_page:
        page = url_page.rsplit("=", 1)[1]
    else:
        page = "1"
    headers.update(referer=referer)
    page_failed = None
    try:
        async with session.get(url_page, headers=headers) as resp:
            if resp.status == 200:
                html = await resp.text()
                queue1.put((page, html))
            else:
                print(resp.status, url_page, referer)
                page_failed = page
    except Exception as e:
        print(url_page, referer)
        page_failed = page

    return page_failed


def crawl_console(queue1):
    page_need = get_page()  # int
    flag = 0
    while True:
        flag += 1
        print(f"第{flag}轮请求开始")
        page_gen = gen_page(page_need)
        page_failed = asyncio.run(create_task(page_gen, queue1))
        # print(page_failed)
        if not page_failed:
            queue1.put(False)
            # print(f"第{flag}轮请求结束")
            break
        time.sleep(1)
        page_need = [int(i) for i in page_failed if i is not None]
        print(len(page_need), page_need)


######################################################################################
# 子进程1: 解析网页

def parser(queue1, queue2):
    while True:
        info = queue1.get()
        if info is False:
            print("页面信息获取完成")
            queue2.put(False)
            break
        page, html = info
        tree = etree.HTML(html)
        nums = tree.xpath('//div[@class="row"]/div/text()')
        nums = [i.strip() for i in nums]
        font = re.findall("base64,(.*). format", html)[0]
        pfn = [page, font, nums]
        queue2.put(pfn)


######################################################################################
# 子进程2: 转化数字

def trans_font(page, base64_str):
    """获得该页的假数字与真数字映射 {str:str}
    """
    base64_bytes = base64.b64decode(base64_str)
    path_ttf = r"E:\CodeStore\Git\pyPractice\anti-font-puzzle\temp" + f"\\{page}.ttf"
    with open(path_ttf, "wb") as f:
        f.write(base64_bytes)
    path_xml = r"E:\CodeStore\Git\pyPractice\anti-font-puzzle\temp" + f"\\{page}.xml"
    ttf = TTFont(path_ttf)
    ttf.saveXML(path_xml)
    tree = etree.parse(path_xml)
    fake_true = {}

    for i in xy:
        num_fake = tree.xpath(f'//TTGlyph[{i}]/@name')[0]
        num_fake = num_map.get(num_fake)  # 换成相应的数字
        num_fake = str(num_fake)  # 数字转字符串
        fake_true[num_fake] = str(xy.index(i))
    return fake_true


def trans_num(fake_nums, fake_true):
    """假数换成真数
    :param fake_nums:  [网页爬下来的假数, ]
    :param fake_true:  {假数字: 真数字}
    :return:
    """
    true_nums = []
    for num in fake_nums:
        num = "_".join(num)
        num = num.split("_")
        true_num = []
        for n in num:
            true_num.append(fake_true[n])
        true_num = "".join(true_num)
        true_nums.append(true_num)
    true_nums = [str(int(i)) for i in true_nums]
    # print(true_nums)
    num_page = "+".join(true_nums)
    _sum = str(eval(num_page))
    return _sum


def trans_console(queue2, queue3):
    while True:
        pfn = queue2.get()
        if pfn is False:
            queue3.put(False)
            break
        page, font, fake_nums = pfn

        fake_true = trans_font(page, font)
        _sum = trans_num(fake_nums, fake_true)
        queue3.put((page, _sum))


######################################################################################
# 子进程3: 写入数据库


def add_to_db(queue3):
    hdb = dbRedis.RedisHash("font")
    while True:
        info = queue3.get()
        if info is False:
            print("写入数据库完成")
            break
        page, _sum = info
        hdb.add(key=page, value=_sum)
        print(page, _sum)



######################################################################################
# 主程序总控制台


def run():
    t1 = time.perf_counter()
    queue1 = Queue()
    queue2 = Queue()
    queue3 = Queue()
    proc1 = Process(target=parser, args=(queue1, queue2))
    proc2 = Process(target=trans_console, args=(queue2, queue3))
    proc3 = Process(target=add_to_db, args=(queue3,))
    proc1.start()
    proc2.start()
    proc3.start()
    crawl_console(queue1)
    proc1.join()
    proc2.join()
    proc3.join()
    hdb = dbRedis.RedisHash("font")
    num_list = hdb.get(mode="vs")
    total = hdb.get(mode="len")
    _sum = 0
    for num in num_list:
        num = int(num)
        _sum += num
    t2 = time.perf_counter()
    print("总个数：", total, "    总和：", _sum)
    print("总耗时: ", t2 - t1)


if __name__ == '__main__':
    # freeze_support()
    mycookie.get_cookie()
    run()

