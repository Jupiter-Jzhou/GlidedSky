import requests
from requests.exceptions import ProxyError, Timeout
import time
from lxml import etree
from tools import procPool, mycookie, dbRedis

url = "http://glidedsky.com/level/web/crawler-ip-block-1"
url_base2 = "http://glidedsky.com/level/web/crawler-basic-2"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111"}


def get_nums(page, special_kwargs):
    """需要用进程池来执行的目标函数
    :param page: 含url_page,proxy
    :param special_kwargs: 该目标函数的专属参数，这里为：cookie
    """
    lock = special_kwargs.get("lock")
    cookie = special_kwargs.get("cookie")
    url_page = url + f"?page={page[0]}"
    proxy = {"http": f"http://{page[1]}"}

    zdb = dbRedis.RedisZSet()
    key_proxy = proxy["http"].split("//")[1]
    hdb = dbRedis.RedisHash()
    key_success = url_page.rsplit("=", 1)[1]
    try:
        with requests.Session() as s:             # 使用会话，自动重用TCP连接
            r = s.get(url_page, headers=headers, proxies=proxy, cookies=cookie, timeout=(22, 48))
    except ProxyError:
        lock.acquire()
        print("无效代理 ", end="\n")
        zdb.minus(key_proxy, account=201)
        lock.release()
    except Timeout:                  # TimeoutError 是内建的
        lock.acquire()
        print("超时 ", end="\n")
        zdb.minus(key_proxy, account=30)
        lock.release()
    except Exception as e:
        lock.acquire()
        print(type(e), e)
        zdb.minus(key_proxy, account=20)
        lock.release()
    else:
        if r.status_code == 200:
            tree = etree.HTML(r.text)
            nums = tree.xpath('//div[@class="row"]/div/text()')
            num_pages = [i.strip() for i in nums]
            nums = "+".join(num_pages)  # 列表元素得是字符串
            total = str(eval(nums))
            lock.acquire()
            hdb.add(key=key_success, value=total)
            zdb.add(key_proxy, score=200)
            lock.release()
        elif r.status_code == 403:
            lock.acquire()
            print("ip is blocked  ", end='')
            zdb.minus(key_proxy, account=201)
            lock.release()
        # elif r.status_code == 429:
        #     lock.acquire()
        #     print("429")
        #     lock.release()
        else:
            lock.acquire()
            print(r.status_code)
            lock.release()



def generator():
    """一页url配一个proxy"""

    # 获取代理
    db = dbRedis.RedisZSet()
    proxy_list = db.get(mode="score", _min=0, _max=199)
    # 获取页码
    page_need = get_page()

    return zip(page_need, proxy_list)


def get_page():
    """返回未完成页码 列表"""
    hdb = dbRedis.RedisHash()
    page_down = hdb.get(mode="ks")
    page_down = [int(i) for i in page_down]
    page_down.sort()
    page_down_max = page_down[-1]
    page_down_min = page_down[0]
    page_con = [i for i in range(page_down_max + 1, 1001)]
    page_need = []
    for i in range(page_down_min, page_down_max + 1):
        if i not in page_down:
            page_need.append(i)
    page_need.extend(page_con)
    page_need.sort()

    return page_need


def load_db():
    """展示统计情况，完成最后的计算"""
    db = dbRedis.RedisHash()
    length = db.get(mode='len')
    result = db.get(mode="vs")
    total = 0
    for i in result:
        total += int(i)
    print("已完成：", length, "还有：", 1000-length)
    print("当前总和：", total)


def run():
    PROCESSES = 30
    cookie = mycookie.load_cookie()
    special_kwargs = {"cookie": cookie}
    page_zip = generator()
    procPool.pool_console(get_nums, PROCESSES, page_zip, mode="mode2",
                          special_kwargs=special_kwargs)
    load_db()


if __name__ == '__main__':
    mycookie.get_cookie()
    t11 = time.perf_counter()
    run()
    t12 = time.perf_counter()
    print("运行时长:", t12 - t11)




    # url_test = url + "?page=428"
    # ip = "117.196.232.131:44395"
    # proxy_test = {"http": f"http://{ip}"}
    # cookie = mycookie.load_cookie()
    # r = requests.get(url_test, headers=headers, cookies=cookie,proxies=proxy_test)
    # tree = etree.HTML(r.text)
    # nums = tree.xpath('//div[@class="row"]/div/text()')
    # num_pages = [i.strip() for i in nums]
    # nums = "+".join(num_pages)  # 列表元素得是字符串
    # total = str(eval(nums))
    # print(total)

