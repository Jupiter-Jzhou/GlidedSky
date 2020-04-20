import requests
from lxml import etree
from tools import procPool, dbRedis

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}

url = "http://www.nimadaili.com/http"  # 国内高匿页
referer = "http://www.nimadaili.com"
headers.update(referer=referer)


def crawler(url_page):
    """访问每一页，返回该页的proxy
    :param url_page: 每页的url
    :return: proxies: 一页的proxy列表
    """
    proxies = []
    with requests.Session() as sess:
        r = sess.get(url_page, headers=headers)
        print(r.text)
        tree = etree.HTML(r.text)
        trs = tree.xpath('//tbody/tr')
        for tr in trs:
            proxy = tr.xpath('./td')[0].xpath('./text()')[0]
            proxies.append(proxy)

    # sleep(random.randint(0,2))
    return proxies


def generator(page_start, page_end):
    """每页url生成器
    :return: url_page: 每页的url，放在循环里就生成了所有页url的生成器
    """
    url_pat = url + "/{0}"
    for page in range(page_start, page_end + 1):
        url_page = url_pat.format(page)
        print(url_page)
        yield url_page


def run():
    PAGE_START = 2
    PAGE_END = 3
    PROCESSES = 1

    url_page_gen = generator(PAGE_START, PAGE_END)
    result = procPool.pool_console(crawler, PROCESSES, url_page_gen, mode="mode1")
    print("开始写入数据库")
    db = dbRedis.RedisZSet()
    for ii in result:
        print(ii)
        for i in ii:
            db.add(i)  # 写入数据库
    print("ok")


if __name__ == '__main__':
    run()


