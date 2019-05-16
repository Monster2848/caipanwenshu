说明文档：

# 功能说明

## 主体功能
1. new_wenshu.py 中是爬取详情页的主体逻辑，项目启动入口也在这里
2. wenshu_keyword.py 中是爬取关键词的主要逻辑，可以独立运行

## 其他功能
1. wenshu_method.py 中主要是各种公共方法
2. random_prua.py 中是获取代理ip和UA的方法
3. redis_ip_pool.py 中放的是代理ip复用的方法
4. wenshu_setting.py 配置文件
5. my_logger.py 是日志模块
6. .*.js 文件是解密需要运行的javascript代码
7. docid.py 也是解密js用的代码


# 数据库表字段说明

## 表名：wenshu
详情数据存放的表
['content'] ：详情页内容，保留了html格式
['sid'] ：docid，每篇文章的唯一id
['src'] ：详情页地址  
['category'] ：查询关键词，eg: "一级案由:刑事案由"
['title'] ：文章标题
['court'] ：法院名称
['pdate'] ：裁判日期，法院判决的日期
['writ'] ：案号 eg: "（2013）行提字第2号"
['reason'] ：判决理由
['sync']：默认为0

## 表名：wenshu_court1
关键词存放的表
['type'] : 关键词类型，eg: 一级案由
['name'] : 关键词，eg: 刑事案由
['pname'] : 父级名称
['level'] : 层级，从1开始，下一层加1
['id'] : 从0开始，自己的id，自增
['pid'] : 父级id

## 表名：wenshu_court_id
关键词id存放的表
['id'] : 与关键词表关联，自增

## 表名：wenshu_used_keyword
使用过的关键词存放的表
['keyword'] : 关键词 eg: "一级案由:刑事案由"

## 表名：wenshu_failed_keyword
失败的关键词存放的表
['keyword'] : 关键词 eg: "一级案由:刑事案由"