import re, time, random
from lxml import etree
import requests
import dbRedis

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101         Firefox/75.0',
           "Accept-Encoding": "gzip, deflate",
           }

url_home = "http://www.xsdaili.com"


def get_url(sess):
    resp = sess.get(url_home,headers=headers)
    tree = etree.HTML(resp.text)
    # print(tree)
    divs = tree.xpath('//div[@class="table table-hover panel-default panel ips "]')
    # print(divs)
    domestic = divs[0].xpath('./div/a/@href')[0]
    url_domestic = url_home + domestic
    oversea = divs[1].xpath('./div/a/@href')[0]
    url_oversea = url_home + oversea
    url_pair = [(url_domestic, url_home), (url_oversea, url_home)]
    return url_pair


def crawler(sess, url_pair):
    url_page = url_pair[0]
    referer = url_pair[1]
    headers.update(referer=referer)
    resp = sess.get(url_page, headers=headers)

    return resp.text


def parser(html):

    tree = etree.HTML(html)
    ips = tree.xpath('//div[@class="cont"]//text()')
    ips = (i.split("@")[0].strip() for i in ips[:-1])
    ips = [i.split("@")[0].strip() for i in ips]

    db = dbRedis.RedisZSet("http")
    for i in ips:
        db.add(i)


def run():
    with requests.Session() as sess:
        url_pair_list = get_url(sess)

        for url_pair in url_pair_list:
            html = crawler(sess, url_pair)
            parser(html)


if __name__ == '__main__':
    run()
