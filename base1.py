import requests
from lxml import etree
from tools import mycookie

url = "http://www.glidedsky.com/level/web/crawler-basic-1"
referer = "http://www.glidedsky.com/level/crawler-basic-1"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"
}


def run_1():
    headers.update(referer=referer)
    cookie = mycookie.load_cookie()
    r = requests.get(url, headers=headers, cookies=cookie)
    tree = etree.HTML(r.text)
    nums = tree.xpath('//div[@class="row"]/div/text()')
    nums = [int(i.strip()) for i in nums]
    total = 0
    for i in nums:
        total += i
    print(total)


if __name__ == '__main__':
    run_1()
