#!/usr/bin/python
#-*- coding=utf-8 -*-

import sys
import getopt 
import webbrowser
import MySQLdb
import time
import weibo
import urllib2


# Database config
db_host     = "localhost"
db_username = "root"
db_password = "RooT"
db_port     = 3306
db_database = "spider"


APP_KEY                    = 3983759328
APP_SECRET                 = """36d1bd885bb6553c201b50fc9912b756"""
CALLBACK_URL               = "http://www.uhquan.com:8888/callback"


#status                     = " 1）有没有兴趣来看下 2）推荐您来看看哦  3）现在购票有优惠，详情咨询@盟邦戏剧  4）抢票进行中 5）转发送票喽"

g_statuses = []
g_statuses.append("有没有兴趣来看下")
g_statuses.append("推荐您来看看哦")
g_statuses.append("现在购票有优惠，详情咨询@盟邦戏剧")
g_statuses.append("抢票进行中")
g_statuses.append("转发送票喽")
g_mid      = "3477166051980538"
g_sent_out = 0
g_group_number = 3

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



def get_code(conn):
    cursor = conn.cursor()
    sql = "select verifier, is_valid from code where id = 1"
    while (1):
        n = cursor.execute(sql)
        res = cursor.fetchall()
        print (res)
        if (1 == int(res[0][1])):
            sql = "update code set is_valid = 0 where id = 1"
            n = cursor.execute(sql)
            cursor.close()
            print("The code is: %s" % str(res[0][0]))
            return res[0][0]
        time.sleep(5)


def do_auth(conn):
    logging = Logging.get_logger('do_auth')
    logging.info(" IN DO_AUTH()")
    client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    url = client.get_authorize_url()   
    #urllib2.Request(url)
    webbrowser.open(url)
    # verifier = input("Verifier: ").strip()
    verifier = get_code(conn)
    #client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    ret = client.request_access_token(verifier)
    access_token = ret.access_token 
    expires_in = ret.expires_in 
    print("access_token = %s    expires_in = %s " %( access_token, expires_in))

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




def get_users(conn):
    logging = Logging.get_logger('get_users')
    cursor = conn.cursor()
    sql = "select nick_name from spider.users where province='北京' and description like '%时尚%' or description like '%戏剧%' or career like '时尚' or career like '戏剧' order by id desc limit 1000;"
    n = cursor.execute(sql)
    logging.info("Find %s users in total..." % n)
    nick_names = cursor.fetchall()
    #logging.info("All Nick Names are: ")
    #print(nick_names)
    cursor.close()
    return nick_names


def repost(api, nick_names):
    global g_sent_out, g_statuses, g_mid
    logging = Logging.get_logger('repost')
    try:
        counter = 0
        status = ""
        logging.info("Len of nick_names = " + str(len(nick_names)))
        while (counter < len(nick_names)):
            g_sent_out += 1
            diff = len(nick_names) - counter
            logging.info("diff = " + str(diff))
            if (diff >= g_group_number):
                logging.info("counter = " + str(counter))
                status = g_statuses[g_sent_out%g_group_number]
                for i in range (0, g_group_number):
                    status += " @" + nick_names[counter+i][0]
                logging.info(str(g_sent_out) + " ==> " + status)
                if not api.is_expires():
                    try:
                        api.post.statuses__repost(id=g_mid, status=status)
                    except weibo.APIError as apierr:
                        logging.error(str(apierr))
                        logging.info("Repost " + str(g_sent_out-1) + " Statuses In Total!")
                        sys.exit(1)
                counter += g_group_number
                logging.info("I am waiting for the next call...")
                time.sleep(10*60)
            else:
                logging.info("I am waiting for the next call...")
                time.sleep(10*60)
                break
        status = g_statuses[g_sent_out%g_group_number]
        for i in range (counter, len(nick_names)):
            status += " @" + nick_names[i][0]
        if not api.is_expires():
            try:
                api.post.statuses__repost(id=g_mid, status=status)
            except weibo.APIError as apierr:
                logging.error(str(apierr))
                logging.info("Repost " + str(g_sent_out) + " Statuses In Total!")
                sys.exit(1)
        g_sent_out += 1
        logging.info(str(g_sent_out) + " ==> " + status)
        logging.info(status)
    except weibo.APIError as apierr:
        print "??????????????????????"
        pass

        #ret = api.post.statuses__repost(id=mid, status=status)
        #print ret
    # except weibo.APIError as apierr:
    #     logging.error(str(apierr))
    #     logging.info("Repost " + str(g_sent_out) + " Statuses In Total!")
    #     sys.exit(1)


def main():
    logging = Logging.get_logger('main')
    logging.info("START --> ")
    conn = MySQLdb.connect(host=db_host, user=db_username, passwd=db_password, db=db_database, charset="utf8")
    api = do_auth(conn)
    nick_names = get_users(conn)
    conn.close()
    logging.info("Start to repost statuses as bubargain@gmail.com")
    repost(api, nick_names)
    logging.info("Repost " + str(g_sent_out) + " Statuses In Total!")
    logging.info(" ---> END")



    # try:
    #     while (1):
    #         for s in g_statuses:
    #             ret = api.post.statuses__update(status=s)
    #             g_sent_out += 1
    #             logging.info("Just sent a status, mid = %s" % ret.mid)
    #             logging.info("--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=------>>>>>>===----- >>>>> ALREADY Have sent number: %s" % g_sent_out)
    #             logging.info("===-=-=-=-=-=-=-=----->>>>>  start to SLEEP for 120 seconds...")
    #             time.sleep(120)
    #             logging.info("===-=-=-=-=-=-=-=----->>>>>  Start to SEND the next status...")
    # except weibo.APIError as apierr:
    #         logging.error(str(apierr))
    #         sys.exit(1)




if __name__ == "__main__":
    main()


