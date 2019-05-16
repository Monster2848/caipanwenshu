import json
import random
import redis
import requests
from .my_logger import logger

class RedisPara(object):

    def __init__(self):
        self.log = logger()
        self.sort_key = 0
        self.conn = redis.Redis(
            host='',
            port=6379,
            password='',
            decode_responses=True,
            db=15)
        self.url = ''

    def get_proxy_list(self):
        resp = requests.get(url=self.url)
        ip_list = json.loads(resp.text).get("data")
        # ip_list = json.loads(resp.text).get("Data")
        proxy_list = []
        for data in ip_list:
            proxy = data.get("ip") + ':' + str(data.get("port"))
            # proxy = data.get("Ip") + ':' + str(data.get("Port"))
            proxy_list.append(proxy)
        return proxy_list

    def save_ip(self, ip_str):
        '''
        保存ip
        :param ip_str:
        :return:
        '''
        if self.conn.keys():
            max_key = int(max(self.conn.keys()))
            if self.sort_key <= max_key:
                temp = max_key +1
                self.sort_key = temp

        self.conn.hset(self.sort_key,key="ip",value=ip_str)
        # 设置过期时间为3分钟
        self.conn.expire(self.sort_key, 180)
        self.sort_key += 1
        return ip_str

    def lpop_ip(self):
        '''
        获取ip
        :return:
        '''

        # 取出最早放进去的ip
        all_keys = self.conn.keys()

        if all_keys:
            num = 100000000
            for my_key in all_keys:
                temp = int(my_key)
                if temp < num:
                    num = temp
            earlier_key = num
            value = self.conn.hgetall(earlier_key)
            self.conn.delete(earlier_key)
            return value
        else:
            print('没有ip了')

    def get_random_ip(self):
        '''
        随机获取redis中的ip
        :return:
        '''
        all_keys = self.conn.keys()
        if all_keys:
            list_length = len(all_keys)
            rand_index = random.randint(0,list_length - 1)
            value = self.conn.hgetall(all_keys[rand_index])
            return value.get('ip')


    def monitor_redis_pool(self):
        '''
        实时监测代理池中ip数量,如果少于20条立即补充
        :return:
        '''
        current_ip_num = len(self.conn.keys())
        if current_ip_num < 20:
            self.log.info('检测到ip少于20条，获取ip')
            proxy_list = self.get_proxy_list()
            for ip in proxy_list:
                self.save_ip(ip)

# r = RedisPara()
# while True:
#     r.monitor_redis_pool()
# aaa = r.get_random_ip()
# print(aaa)




