import requests
from lxml import etree
import mycookie
import procPool

PAGE_START = 1
PAGE_END = 100
PROCESSES = 3

url = "http://www.glidedsky.com/level/web/crawler-basic-2"
referer = "http://www.glidedsky.com/level/web/crawler-basic-2"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"
}


def get_nums(url_page, special_kwargs):
    """需要用进程池来执行的目标函数
    :param url_page: 由生成器生成的迭代参数，这里为：每页的url
    :param special_kwargs: 该目标函数的专属参数，这里为：cookie
    :return: num_pages: 结果，这里为：每页的数字列表
    """
    num_pages = []
    headers.update(referer=referer)
    cookie = special_kwargs.get("cookie")
    with requests.Session() as sess:
        r = sess.get(url_page, headers=headers, cookies=cookie)
        tree = etree.HTML(r.text)
        nums = tree.xpath('//div[@class="row"]/div/text()')
        nums = [int(i.strip()) for i in nums]
        num_pages.extend(nums)

    return num_pages


def generator(page_start, page_end):
    """每页url生成器
    :return: url_page: 每页的url，放在循环里就生成了所有页url的生成器
    """
    url_pat = url + "?page={0}"
    for page in range(page_start, page_end + 1):
        url_page = url_pat.format(page)
        yield url_page


def run():
    cookie = mycookie.load_cookie()
    special_kwargs = {"cookie": cookie}
    gen_url_page = generator(PAGE_START, PAGE_END)
    num, num_total = procPool.pool_console(get_nums, PROCESSES, gen_url_page, mode="mode1", **special_kwargs)
    print("爬取网页数", num)
    print("理应数字个数", num * 12)
    print("得到数字个数", len(num_total))
    total = 0
    for i in num_total:
        total += i
    print("数字总和：", total)


if __name__ == '__main__':
    # mycookie.get_cookie()
    run()
