import json
import re
import execjs
import requests
from wenshu_task.my_logger import logger
from wenshu_task.random_prua import get_prua
from wenshu_task.wenshu_method import MongoPara


class SaveKeyWord(object):
    # 手动录入关键字
    def __init__(self):
        self.mongo = MongoPara()
        # self.keyword_list = ["文书类型:令","文书类型:通知书","文书类型:决定书","文书类型:调解书","文书类型:裁定书","文书类型:判决书",
        #     "审判程序:一审","审判程序:二审","审判程序:再审","审判程序:再审审查与审判监督","审判程序:其他",
        #     "裁判年份:2019","裁判年份:2018","裁判年份:2017","裁判年份:2016","裁判年份:2015","裁判年份:2014","裁判年份:2013",
        #     "裁判年份:2012","裁判年份:2011","裁判年份:2010","裁判年份:2009","裁判年份:2008","裁判年份:2007","裁判年份:2006",
        #     "裁判年份:2005","裁判年份:2004","裁判年份:2003","裁判年份:2002","裁判年份:2001","裁判年份:2000","裁判年份:1999",
        #     "裁判年份:1998","裁判年份:1997","裁判年份:1996","法院层级:最高法院","法院层级:高级法院","法院层级:中级法院",
        #     "法院层级:基层法院",]
        self.keyword_list =["一级案由:刑事案由", "一级案由:民事案由", "一级案由:行政案由", "一级案由:赔偿案由", "一级案由:执行案由"]

    def set_item_format(self,type,name,pname,level):
        # 设置默认格式
        item = {}
        item['type'] = type
        item['name'] = name
        item['level'] = level
        item['id'] = self.mongo.get_id()
        item['pname'] = pname
        item['pid'] = self.mongo.get_pid(pname)
        return item

    def save_by_hand(self):
        # 遍历关键词列表，处理，保存数据
        for keyword in self.keyword_list:
            type_word_list = keyword.split(':')
            item = self.set_item_format(type_word_list[0],type_word_list[1],'',1)
            # print(item)
            self.mongo.save_data(item)

    def update_data(self):
        # 为之前已有的数据添加字段
        for i in self.mongo.collection.find({"level":3}):
            result = self.mongo.collection.update( {'_id' : i['_id']},{'$set': {'type':"基层法院"}})
            return result

    def search_data(self,search_condition):

        keyword_generator = self.mongo.get_para(search_condition)
        return keyword_generator

    def save_auto(self,item):
        self.mongo.save_data(item)


class GetAnyou(object):
    # 获取文书关键字 案由类型
    def __init__(self,get_ua, get_pr):
        self.ua = get_ua
        self.proxies = {'http': 'http://{}'.format(get_pr)}
        self.item = {}
        self.log = logger()
        self.save_keyword = SaveKeyWord()

    # 首页第一次
    def home_1(self):
        url = 'http://wenshu.court.gov.cn/'
        resp = requests.get(
            url=url,
            headers={
                "User-Agent": self.ua,
            },
            proxies=self.proxies,
            allow_redirects=False,
            timeout=20
        )

        html_js = resp.text
        try:
            dynamicurl = re.search('dynamicurl="(.*?)"', html_js).group(1)
            wzwsquestion = re.search('wzwsquestion="(.*?)"', html_js).group(1)
            wzwsfactor = re.search('wzwsfactor="(.*?)"', html_js).group(1)
            wzwsmethod = re.search('wzwsmethod="(.*?)"', html_js).group(1)
            wzwsparams = re.search('wzwsparams="(.*?)"', html_js).group(1)
        except:
            return None

        para_part = '''
        var dynamicurl="{}";var wzwsquestion="{}";var wzwsfactor="{}";var wzwsmethod="{}";var wzwsparams="{}";
        '''.format(dynamicurl,wzwsquestion,wzwsfactor,wzwsmethod,wzwsparams)

        with open('home_1.js','r',re.DOTALL) as f:
            js_code = f.read()
        js_code = para_part + js_code

        ctx = execjs.compile(js_code)
        wzwschallenge = ctx.call("wzwschallenge")

        next_url = 'http://wenshu.court.gov.cn' + dynamicurl + '?' + 'wzwschallenge=' + wzwschallenge
        wzws_cid = requests.utils.dict_from_cookiejar(resp.cookies).get("wzws_cid")
        return next_url,wzws_cid

    # 首页第二次
    def home_2(self):
        box = self.home_1()
        if not box:
            return None
        next_url, wzws_cid = box

        url = next_url
        resp = requests.get(
            url=url,
            headers={
                "User-Agent": self.ua,
            },
            proxies=self.proxies,
            allow_redirects=False,
            timeout=20,
            cookies ={
                "wzws_cid": wzws_cid
            }
        )
        next_wzws_cid = requests.utils.dict_from_cookiejar(resp.cookies).get("wzws_cid")
        return next_wzws_cid

    # 列表页第一次
    def list_1(self):
        box = self.home_2()
        if not box:
            return None
        next_wzws_cid = box

        url = "http://wenshu.court.gov.cn/List/List"
        resp = requests.get(
            url=url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "keep-alive",
                "Referer": "http://wenshu.court.gov.cn/",
                "DNT": "1",
                "Host": "wenshu.court.gov.cn",
                "Upgrade-Insecure-Requests": "1",

                "User-Agent": self.ua,
            },
            cookies={
                "wzws_cid": next_wzws_cid
            },
            proxies=self.proxies,
            allow_redirects=False,
            timeout=20
        )

        vjkl5 =  requests.utils.dict_from_cookiejar(resp.cookies).get("vjkl5")
        return vjkl5,next_wzws_cid

    # 二级案由
    def sec_anyou(self):
        vjkl5, next_wzws_cid = self.list_1()

        search_condition = {"type": "二级案由"}
        keyword_generator = self.save_keyword.search_data(search_condition)

        for i in keyword_generator:
            type = "二级案由"
            keyword = i.get("name")

            url = "http://wenshu.court.gov.cn/List/ReasonTreeContent"
            resp = requests.post(
                url=url,
                headers={
                    "Referer": "http://wenshu.court.gov.cn/",
                    "Host": "wenshu.court.gov.cn",
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": self.ua,
                },
                cookies={
                    "wzws_cid": next_wzws_cid,
                    "vjkl5": vjkl5
                },
                proxies=self.proxies,
                allow_redirects=False,
                timeout=20,
                data={
                    "Param": "{}:{}".format(type,keyword),
                    "parval": keyword
                }

            )

            raw_sec_data = resp.text
            sec_data = json.loads(raw_sec_data)
            sec_data = json.loads(sec_data)
            dic_list = sec_data[0]["Child"]

            for dic in dic_list:
                sec_name = dic['Key']

                if sec_name:
                    type = "三级案由"
                    level = 3
                    name = sec_name
                    pname = keyword

                    item = self.save_keyword.set_item_format(type=type,level=level,name=name,pname=pname)
                    # self.save_keyword.save_auto(item)

                    print(item)


# box = get_prua()
# get_ua, get_pr = box
# a = GetAnyou(get_ua, get_pr)
# print(a.list_1())

# a = SaveByMyself()
# a.save()

box = get_prua()
get_ua, get_pr = box
a = GetAnyou(get_ua, get_pr)
a.sec_anyou()
