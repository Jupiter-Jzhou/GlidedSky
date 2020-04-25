#
# 未完成
#


import re, time, random
from lxml import etree
import requests
import dbRedis

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0',
           "Accept-Encoding": "gzip, deflate",
           }


def gen_page_mip():
    url_home = "https://proxy.mimvp.com"
    url_sole = "https://proxy.mimvp.com/freesole"
    url_secret= "https://proxy.mimvp.com/freesecret"
    url_open = "https://proxy.mimvp.com/freeopen"
    return [(url_sole, url_home), (url_secret, url_sole), (url_open, url_secret)]


def crawler(sess, url, referer):

    headers.update(referer=referer)
    while True:
        try:
            r = sess.get(url, headers=headers)
            if r.status_code == 200:
                time.sleep(random.randint(1, 2))
                return r.text
            else:
                time.sleep(random.randint(1, 2))
                continue
        except Exception as e:
            print(type(e), e)
            time.sleep(random.randint(1, 2))
            continue


def parser(html):
    zdb = dbRedis.RedisZSet("http")
    tree = etree.HTML(html)
   ### port 是图片！！！


def run():
    page_list = gen_page_mip()
    with requests.Session() as sess:
        for url, referer in page_list:
            html = crawler(sess, url, referer)
            parser(html)


if __name__ == '__main__':
    run()