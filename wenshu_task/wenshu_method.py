import json
import random
import js2py
import re
import pymongo
from wenshu_task.wenshu_setting import MongoSetting
from .my_logger import logger


class ParseJs(object):
    '''
    解析js获得cookie参数
    return : vl5x, guid
    '''
    def __init__(self):
        self.log = logger()
        self.context = js2py.EvalJs()
        with open('./getKey.js', 'r') as f:
            self.js_content = f.read()
        with open('./md5.js', 'r') as f:
            self.js_md5 = f.read()
        with open('./sha1.js', 'r') as f:
            self.js_sha1 = f.read()
        with open('./base64.js', 'r') as f:
            self.js_base64 = f.read()
        # with open('./createGuid.js', 'r') as f:
        #     self.js_guid = f.read()

    def createGuid(self):
        return str(hex((int(((1 + random.random()) * 0x10000)) | 0)))[3:]

    def getguid(self):
        return '{}{}-{}-{}{}-{}{}{}' \
            .format(
            self.createGuid(), self.createGuid(),
            self.createGuid(), self.createGuid(),
            self.createGuid(), self.createGuid(),
            self.createGuid(), self.createGuid()
        )

    def get_key_para(self, vjkl5):
        try:
            self.context.vjkl5 = vjkl5
            self.context.execute(self.js_md5)
            self.context.execute(self.js_sha1)
            self.context.execute(self.js_base64)
            self.context.execute(self.js_content)
            guid = self.getguid()
            # self.context.execute(self.js_guid)
            # return (self.context.result, self.context.guid)
            return (self.context.result, guid)
        except:
            # 多线程可能有问题
            self.log.error('js文件读取错误')
            return None

class ParseDetail(object):
    def __init__(self,resp_text):
        self.resp_text = resp_text
        self.context = js2py.EvalJs()
        self.log = logger()

    def parse_detail(self):
        try:
            js_code = re.search(r'(var jsonHtmlData(.*?))var jsonData', self.resp_text, re.DOTALL).group(1)
            self.context.execute(js_code)
            self.context.execute('var jsonData = eval("(" + jsonHtmlData + ")")')
            self.context.execute('var jsonHtml = jsonData.Html.replace(/01lydyh01/g, "\'")')
            html_raw = self.context.jsonHtml  # 这个是个带格式的html文本
            return html_raw
        except Exception as e:
            self.log.error('ParseDetail.parse_detail异常：{}'.format(e))

    def parse_list_data(self):
        self.context.data = self.resp_text
        self.context.execute('datalist = eval(data)')
        raw_datalist = self.context.datalist
        zero_flag = re.search('"Count":"0"',raw_datalist)
        if not zero_flag:
            # 返回的值可能出现有RunEval，但是数据为0
            try:
                datalist = json.loads(self.context.datalist)
                return datalist
            except Exception as e:
                self.log.error('异常为：{}'.format(e))
                return None
        else:
            self.log.warning('列表页数据为空')
            return None

    def parse_items(self):
        case = self.resp_text
        title= case['案件名称']
        court = case['法院名称']
        pdate = case['裁判日期']
        if case['案号'] == '无':
            writ = ''
        else:
            writ = case['案号']
        try:
            reason = case['裁判要旨段原文']
        except Exception as e:
            self.log.error('未匹配出reason')
            reason = ''
        Docid = case['文书ID']
        return (title,court,pdate,writ,reason,Docid)

class MongoPara(object):
    '''
    从mongodb中获取所有二级法院名称
    '''
    def __init__(self):
        self.client = pymongo.MongoClient(MongoSetting)
        self.db = self.client.spider
        self.collection = self.db.wenshu_court1
        self.log = logger()

    def get_name_count(self,name):
        return self.collection.find({'pname':name}).count()

    def delete_court_item(self):
        '''
        快速删除数据
        :return:
        '''
        self.collection = self.db.wenshu_court1
        # return self.collection.delete_many({ "level": 3 })

    def get_max_id(self):
        max_id_cursor = self.collection.find().sort("id", pymongo.DESCENDING).skip(0).limit(1)
        for item in max_id_cursor:
            max_id = item.get('id')
            return max_id

    def get_para(self,search_condition):
        '''
        返回一个生成器，遍历结果获得每一条字典数据
        :return:
        '''
        self.search_condition = search_condition
        result_cursor = self.collection.find(search_condition)
        self.client.close()
        for item in result_cursor:
            yield item

    def get_id(self):
        '''
        mongo自增id
        :return:
        '''
        # 查询对应的表中是否还有值，没有的话就把id清0
        fcount = self.collection.find({'id': {'$gt': -1}}).count()
        # 获取法院名称表里的id最大值，如果有删除数据，让id等于名称表里id 的最大值
        current_max_id = self.get_max_id()

        self.collection = self.db.wenshu_court_id
        id_cursor = self.collection.find({'id':{'$gt':-1}})
        count = self.collection.find({'id':{'$gt':-1}}).count()
        if count == 0:
            self.collection.insert_one({'id': 0})
            return 0
        elif count == 1:
            for id in id_cursor:
                last_id = id.get('id')
                self.collection.delete_one({ "id": last_id})
                if last_id > current_max_id:
                    last_id = current_max_id
                new_id = last_id + 1
                if fcount == 0:
                    self.collection.insert_one({"id": 0})
                    return 0
                else:
                    self.collection.insert_one({"id": new_id})
                    return new_id
        else:
            self.log.error('id数量异常')

    def get_pid(self,name):
        # 如果没有父级id会返回null
        self.collection = self.db.wenshu_court1
        parent_cursor = self.collection.find({"name": name})
        for parent_dic in parent_cursor:
            pid = parent_dic.get('id')
            return pid

    def save_data(self,item):
        self.collection = self.db.wenshu_court1
        self.collection.insert_one(item)

class Para(object):
    '''
    获取其他参数
    '''
    def __init__(self):
        self.user_agents = [
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
            "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
            "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
            "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
            "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
            "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
            "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
            "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
            "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
            "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13",
            "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+",
            "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
            "Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)",
            "UCWEB7.0.2.37/28/999",
            "NOKIA5700/ UCWEB7.0.2.37/28/999",
            "Openwave/ UCWEB7.0.2.37/28/999",
            "Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999",
        ]

    def get_user_agent(self):
        '''
        获取随机user_agent
        :return:
        '''
        ua = self.user_agents[random.randint(0, 38)]
        return ua

# a = Para()
# print(a.get_user_agent())



