from wenshu_task.redis_ip_pool import RedisPara

r = RedisPara()
while True:
    r.monitor_redis_pool()