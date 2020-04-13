import requests
from lxml import etree
import json


url_login = "http://www.glidedsky.com/login"
url_home = "http://www.glidedsky.com"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"
}
path = r"E:\CodeStore\Git\pyPractice\cookie_login.json"


def load_cookie():
    with open(path, "r") as f:
        cookie = f.read()
    if cookie is '':
        cookie = {}
    else:
        cookie = json.loads(cookie)
    return cookie


def get_cookie():
    """重新模拟登录，获取cookie
    :return: None
    """
    data = {
        "email": "jzhou.xc@qq.com",
        "password": "jzhou.xc@qq.com"
    }
    with requests.Session() as s:
        login_get = s.get(url_login, headers=headers)
        tree = etree.HTML(login_get.text)
        token = tree.xpath('//input[@type="hidden"]/@value')[0]
        data.update(_token=token)
        headers.update(origin=url_home, referer=url_login)
        login_post = s.post(url_login, headers=headers, data=data)
        print(login_post.cookies)
        cookie = login_post.cookies.get_dict()
        cookie = json.dumps(cookie, indent=4)
        with open(path, "w") as f:
            f.write(cookie)