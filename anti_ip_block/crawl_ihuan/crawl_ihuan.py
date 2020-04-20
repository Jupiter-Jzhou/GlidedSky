#
#   页面返回乱码 未解决 页面有编码处理
#

import requests
import dbRedis

url_home = "https://ip.ihuan.me"
url_ti = "https://ip.ihuan.me/ti.html"
url_js = "https://ip.ihuan.me/mouse.do"
url_tqdl = "https://ip.ihuan.me/tqdl.html"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0',
           "Accept-Encoding": "gzip, deflate, br",
           }

data = {
    "num": "3000",
    "port": "",
    "kill_port": "",
    "address": "",
    "kill_address": "",
    "anonymity": "2",  # 2 高匿
    "type": "1",  # 0 不限 1 仅HTTP
    "post": "",
    "sort": "",
    "key": ""  # 需要获取
}


def crawler():
    with requests.Session() as sess:
        sess.get(url_home, headers=headers)
        headers.update(referer=url_home)
        r = sess.get(url_ti, headers=headers)
        headers.update(referer=url_ti)

        # r = sess.get(url_js, headers=headers)

        # with open("mouse_do_ti.txt", "wb") as f:
        #     f.write(r.content.decode("utf8","ignore"))

        # headers.update(origin=url_home)
        # sess.post(url_target, headers=headers, data=data)


if __name__ == '__main__':
    # crawler()

    # with open("ihuan.txt", "r") as f:
    #     proxies = f.readlines()
    # proxies = (i.strip() for i in proxies)
    # db = dbRedis.RedisZSet()
    # for i in proxies:
    #     db.add(i)


    with open("ihuan.txt", "r", encoding="utf-8") as f:
        ips = f.readlines()
    # ips = (i.split("@")[0].strip() for i in ips)
    ips = [i.split("@")[0].strip() for i in ips]
    print(ips)
    db = dbRedis.RedisZSet()
    for i in ips:
        db.add(i)