import redis

class RedisList(object):
    """列表"""
    def __init__(self, list_name="fail"):
        self.db = redis.StrictRedis(decode_responses=True)
        self.list_name = list_name

    def add(self, *value):
        self.db.lpush(self.list_name, *value)
        print("列表新增:{0}".format(value))

    def get(self, mode="all"):
        """列表"""
        if mode == "all":
            return self.db.lrange(self.list_name, 0 , -1)

    # def delete(self, value):
    #     self.db.lrem(self.list_name, )


class RedisHash(object):
    """散列表"""
    def __init__(self, hash_name="nums"):
        self.db = redis.StrictRedis(decode_responses=True)
        self.hash_name = hash_name

    def add(self, mode="nx", *, key=None, value=None, dic=None):
        """:param: mode
                        nx: 无键则添加值, 添加成功返回1
        """
        if mode == "nx":
            flag = self.db.hsetnx(self.hash_name, key, value)
            if flag:
                print("新添加:{0}, 值为:{1}".format(key, value))
            else:
                old_value = self.get(mode="v", key=key)
                print("已存在:{0}, 值为:{1}, 未替换新值:{2}".format(key, old_value,value))
        elif mode == "dic":
            self.db.hmset(self.hash_name, dic)
            print("已批量添加:{0}".format(dic))
        elif mode == "force":
            self.db.hset(self.hash_name, key, value)
            print("已添加:{0}, 值为:{1}".format(key, value))
        else:
            print("so,what do you want?")

    def get(self, mode="kvs", *, key=None, keys=None):
        """从哈希表中返回内容
        :param: keys: 列表,元组都行
        :param: mode: 选择模式
                     kvs: 返回表中所有键值对   字典
                     vs: 返回表中所有键的值    列表
                     ks: 返回所有键名         列表
                     len: 返回键值对个数
                     v:  返回某个键的值
                     mv: 返回多个键的值        列表

        """
        if mode == "kvs":
            return self.db.hgetall(self.hash_name)
        elif mode == "vs":
            return self.db.hvals(self.hash_name)
        elif mode == "ks":
            return self.db.hkeys(self.hash_name)
        elif mode == "len":
            return self.db.hlen(self.hash_name)
        elif mode == "v":
            return self.db.hget(self.hash_name, key)
        elif mode == "mv":
            return self.db.hmget(self.hash_name, keys)
        else:
            print("so, what do want?")

    def delete(self, *keys, mode=None):
        """给几个键就删几个
        :param: keys: 以元组给出多个
        :param: mode: all: 全删
        """
        all_keys = self.get(mode="ks")
        if mode == "all":
            self.db.hdel(self.hash_name, *all_keys)
        else:
            self.db.hdel(self.hash_name, *keys)
            print("已删除键:{0}".format(keys))

    def exist(self, key):
        """判断某个键是否存在"""
        return self.db.hexists(self.hash_name, key)


class RedisZSet(object):
    """有序集合"""

    def __init__(self, redis_key="proxies"):
        self.db = redis.StrictRedis(decode_responses=True)
        self.redis_key = redis_key
        self.INITIAL_SCORE = 10
        self.MIN_SCORE = 0
        self.MAX_SCORE = 100

    def add(self, proxy, score=None):
        """添加元素和其分数
        """
        if score is None:
            score = self.INITIAL_SCORE

        maping = {proxy: score}
        flag = self.db.zadd(self.redis_key, maping, nx=True)
        if flag == 1:
            print("代理:", proxy, " 分数:", score, "  添加")
        elif flag == 0:
            old_score = self.db.zscore(self.redis_key, proxy)
            print("代理:", proxy, " 分数:", old_score, "  已存 ")

    def update(self, proxy, score):
        """更新元素的分数"""

        maping = {proxy: score}
        old_score = self.db.zscore(self.redis_key, proxy)
        self.db.zadd(self.redis_key, maping, xx=True)
        print("代理:", proxy, " 分数:", old_score, "=>", score, "  更新")

    def minus(self, proxy, account=1):
        """减分数"""
        score = self.db.zscore(self.redis_key, proxy)
        if int(score) - account >= self.MIN_SCORE:
            score = self.db.zincrby(self.redis_key, -account, proxy)
            print("代理:", proxy, " 分数:", score, "  减", str(account))
        else:
            self.db.zrem(self.redis_key, proxy)
            print("代理:", proxy, " 分数:", score, "  移除")

    def plus(self, proxy, account=1):
        """加分数"""
        score = self.db.zscore(self.redis_key, proxy)
        if int(score) + account <= self.MAX_SCORE:
            score = self.db.zincrby(self.redis_key, account, proxy)
            print("代理:", proxy, " 分数:", score, "  加", str(account))
        else:
            self.db.zadd(self.redis_key, self.MAX_SCORE, proxy)
            print("代理:", proxy, " 分数:", score, "  满格了")

    def exist(self, proxy):
        """判断元素是否存在"""
        return not self.db.zscore(self.redis_key, proxy) is None

    def get(self, mode="all", *, _min=None, _max=None):
        """获取全部元素"""
        if mode == "all":
            return self.db.zrevrangebyscore(self.redis_key, self.MAX_SCORE, self.MIN_SCORE) # 列表
        elif mode == "score":
            return self.db.zrangebyscore(self.redis_key, _min, _max)    # 列表
        elif mode == "gen":
            return self.db.zscan_iter(self.redis_key)  # 生成器 带分数

    def count(self, _min=None, _max=None):
        """获取元素个数，默认全部元素"""
        if _min is None:
            _min = self.MIN_SCORE
        if _max is None:
            _max = self.MAX_SCORE
        return self.db.zcount(self.redis_key, _min, _max)



# if __name__ == '__main__':
#     ldb = RedisList()
#     ldb.add("1865")
#     print(ldb.get())


# db = RedisZSet("test")
# db.add("a1")
# db.add("a2", score=20)
# db.add("a2", score=30)
# # ii = db.get()
# flag =0
# for i in ii:
#     flag += 1
#     print(i)
# print(flag)
# ip = "95.181.37.114:45517"
# db.add(ip, score=200)
# # print(db.get())