#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt 
import webbrowser
import MySQLdb
import time
import weibo
import urllib2



APP_KEY                    = 1145738428
APP_SECRET                 = """275b151558a7007b0c8dab0060588f42"""
CALLBACK_URL               = "http://114.246.95.76/merchant/callback.php"


g_sent_out = 0
g_statuses = []


g_statuses.append("是否梦想成为万众瞩目的焦点？奥迪A1给你舞台。奥迪携手盟邦戏剧 合力打造时尚话剧之张德芬 经典著作《活出全新的自己》，即日起至7月19日，演员及模特海选火热进 行！详见：http://t.cn/zWf4BGk")

g_statuses.append("【活出全新的自己】舞台剧首次公开招募剧中所有演员和模特！张德芬同名小说改编，由华联集团，奥迪A1携手盟邦戏剧重磅推出。内部推荐您来参与，也可推荐你的朋友参 加，谢谢支持：http://t.cn/zWf4BGk")

g_statuses.append(" #戏剧微海选#2012奥迪A1携手@盟邦戏剧 BHG Mall倾情打造张德芬小说≪#活出全新的自己#≫同名舞台剧。现面向社会诚招模特、演员。您想参与其中的角色么？您想圆自己 一个舞台梦吗？您想展示自己的风采吗？您想活出全新的自己吗？参加活动，在线填写报名表即可报名参加海选！http://t.cn/zWf4BGk")

g_statuses.append("2012奥迪A1携手盟邦戏剧 BHG Mall倾情打造张德芬小说#活出全新的自己#舞台剧。您想参与其中的角色么？请来这里报名：北京奥迪经销商展厅，BHG Mall北京华联购物中 心，盟邦戏剧微博（私信索取报名表）模特、演员都有机会登上舞台和我们一起打造活出全新的自己！机不可失，机会就在你面前。  http://t.cn/zWf4BGk")

g_statuses.append("#2012奥迪A1时尚话剧#奥迪A1携手盟邦戏剧 合力打造时尚话剧，张德芬 经典著作《活出全新的自己》，演员及模特海选火热进行中！你想像明星一样闪耀光芒吗？你想拥 有属于自己的舞台吗？http://t.cn/zWf4BGk")

g_statuses.append("舞台、灯光、掌声，这些是否让你艳羡？你是否梦想成为万众瞩目的焦点？机会来了！奥迪给你舞台。奥迪A1携手@盟邦戏剧 合力打造时尚话剧之 @张德芬 经典著作《活出 全新的自己》，演员及模特海选正火热进行！即日起至7月19日，还等什么，快来报名吧，闪亮的舞台属于你！ http://t.cn/zWf4BGk")




class Logging:
    func_name = ''

    def __init__(self, func_name):
        self.func_name = func_name

    @staticmethod
    def get_logger(func_name):
        return Logging(func_name.upper())

    @staticmethod
    def timestamp():
        return time.strftime('%Y-%m-%d %X', time.localtime(time.time()))

    def info(self, content):
        print(Logging.timestamp() + "  INFO   [" + self.func_name  + "]: " + content)

    def warning(self, content):
        print(Logging.timestamp() + " WARNING [" + self.func_name  + "]: " + content)

    def error(self, content):
        print(Logging.timestamp() + "  ERROR  [" + self.func_name  + "]: " + content)




def do_auth():
    logging = Logging.get_logger('do_auth')
    client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    url = client.get_authorize_url()
    webbrowser.open(url)
    verifier = input("Verifier: ").strip()
    #client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    ret = client.request_access_token(verifier)
    access_token = ret.access_token 
    expires_in = ret.expires_in 
    client.set_access_token(access_token, expires_in)
    if not client.is_expires():
        try:
            uid = client.get.account__get_uid().uid
        except weibo.APIError as apierr:
            logging.error(str(apierr))
            sys.exit(1)
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            sys.exit(1)
        logging.info("uid = %s " % uid)
        try:
            u = client.get.users__show(uid=uid)
        except weibo.APIError as apierr:
            logging.error(str(apierr))
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            sys.exit(1)
        #logging.info(str(u))
        logging.info("We are uing API from account: [uid = %s, name = %s]" % (u.id, u.screen_name))
    return client



def get_users():
    logging = Logging.get_logger('get_users')
    conn = MySQLdb.connect(host="www.uhquan.com", user="root", passwd="RooT", db="spider", charset="utf8")
    cursor = conn.cursor()
    sql = "select nick_name from users where description like '%演员%' or description like '%模特%';"
    n = cursor.execute(sql)
    print ("Find %s records in total..." % n)
    nick_names = cursor.fetchall()
    print ("All Nick Names are: ")
    print (nick_names)
    print ("To view the structure would help you to organize the statuses...")
    cursor.close()
    conn.close()
    return nick_names

# you may use the following statements...
# for nick in nick_names:
#    g_status[1] + "  @" + nick

# ... ... You could add more like this...

def main():
    global g_sent_out, g_statuses
    logging = Logging.get_logger('main')
    api = do_auth()
    users = get_users()
    logging.info("Sending statuses as bubargain@gmail.com")
    try:
        while (1):
            for s in g_statuses:
                ret = api.post.statuses__update(status=s)
                g_sent_out += 1
                logging.info("Just sent a status, mid = %s" % ret.mid)
                logging.info("--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=------>>>>>>===----- >>>>> ALREADY Have sent number: %s" % g_sent_out)
                logging.info("===-=-=-=-=-=-=-=----->>>>>  start to SLEEP for 120 seconds...")
                time.sleep(120)
                logging.info("===-=-=-=-=-=-=-=----->>>>>  Start to SEND the next status...")
    except weibo.APIError as apierr:
            logging.error(str(apierr))
            sys.exit(1)




if __name__ == "__main__":
    main()


