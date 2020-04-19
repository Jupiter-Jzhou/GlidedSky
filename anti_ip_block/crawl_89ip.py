import requests
import re
from lxml import etree
import dbRedis


url_ti = "http://www.89ip.cn/ti.html"
url_tqdl = "http://www.89ip.cn/tqdl.html"  # ?num=100&address=&kill_address=&port=&kill_port=&isp=

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0',
           "Accept-Encoding": "gzip, deflate",
           }

params = {
    "num": "100",
    "address": "",
    "kill_address": "",
    "port": "",
    "kill_port": "",
    "isp": "",
}


def crawler():
    with requests.Session() as sess:
        r = sess.get(url_ti, headers=headers)
        total = re.compile("代理总量：(.*)个").findall(r.text)[0]
        params.update(num=total)
        r = sess.get(url_tqdl, params=params)
        parser(r.text)


def parser(html):
    zdb = dbRedis.RedisZSet()
    tree = etree.HTML(html)
    div = tree.xpath('//div[@class="fly-panel"]/div/text()')
    for i in div:
        if "更" not in i:
            zdb.add(i.strip())
        else:
            break


if __name__ == '__main__':
    crawler()