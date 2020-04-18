import requests
from lxml import etree
from tools import procPool, dbRedis

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}


url = "https://www.xicidaili.com/nn"  # 国内高匿页
referer = "https://www.xicidaili.com"
headers.update(referer=referer)


def crawler(url_page):
    """访问每一页，返回该页的proxy
    :param url_page: 每页的url
    :return: proxies: 一页的proxy列表
    """
    proxies = []
    with requests.Session() as sess:
        print(url_page)
        r = sess.get(url_page, headers=headers)
        print(r.text)
    tree = etree.HTML(r.text)
    trs = tree.xpath('//table[@id="ip_list"]//tr')
    print(etree.tostring(trs))
    for tr in trs[1:]:
        style = tr.xpath('./td')[5].xpath('./text()')[0]
        ip = tr.xpath('./td')[1].xpath('./text()')[0]
        port = tr.xpath('./td')[2].xpath('./text()')[0]
        if style == 'HTTP':
            proxy = ":".join([ip, port])
            proxies.append(proxy)
    return proxies


def generator(page_start, page_end):
    """每页url生成器
    :return: url_page: 每页的url，放在循环里就生成了所有页url的生成器
    """
    url_pat = url + "/{0}"
    for page in range(page_start, page_end + 1):
        url_page = url_pat.format(page)
        yield url_page


def run():
    PAGE_START = 100
    PAGE_END = 100
    PROCESSES = 1

    url_page_gen = generator(PAGE_START, PAGE_END)
    result = procPool.pool_console(crawler, PROCESSES, url_page_gen, mode="mode1")
    print("开始写入数据库")
    db = dbRedis.RedisZSet()
    for ii in result:
        for i in ii:
            db.add(i)                 # 写入数据库
    print("ok")


if __name__ == '__main__':

    run()

    # with open("ipo.txt", "r", encoding="utf-8") as f:
    #     ips = f.readlines()
    # # ips = (i.split("@")[0].strip() for i in ips)
    # ips = [i.split("@")[0].strip() for i in ips]
    # print(ips)
    # db = dbRedis.RedisZSet()
    # for i in ips:
    #     db.add(i)

