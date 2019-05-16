import requests

# 程序捕获以下指定异常
ExceptionCollections = (requests.exceptions.ConnectionError,requests.exceptions.ReadTimeout,requests.exceptions.ProxyError)

# 设置爬虫线程数量
ThreadNum = 3

# Mongo 数据库信息
MongoSetting = ''

# Redis 数据库信息
host = '',
port = 6379,
password = '',
decode_responses = True,
db = 0