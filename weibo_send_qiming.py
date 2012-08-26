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
db_database = "weibo_send"


# Using at uhquan.com
# APP_KEY                    = 3983759328
# APP_SECRET                 = """36d1bd885bb6553c201b50fc9912b756"""
# CALLBACK_URL               = "http://www.uhquan.com:8888/callback"

# Using at local
APP_KEY                    = 1145738428
APP_SECRET                 = """275b151558a7007b0c8dab0060588f42"""
CALLBACK_URL               = "http://76.116.64.145:8888/callback"

COMMENT_ORI    = 1
WAITING_PERIOD = 60*5
APP_ADDRESS    = "recoverglass.sinaapp.com"

g_create       = 0
g_send_number  = 100



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
        print(Logging.timestamp() + "  INFO   [" + self.func_name  + "]: " + content).encode('utf8')

    def warning(self, content):
        print(Logging.timestamp() + " WARNING [" + self.func_name  + "]: " + content).encode('utf8')

    def error(self, content):
        print(Logging.timestamp() + "  ERROR  [" + self.func_name  + "]: " + content).encode('utf8')


def get_codes(conn):
    logging = Logging.get_logger('get_codes')
    logging.info(" HERE ")
    cursor = conn.cursor()
    sql = "select verifier from code where is_valid=1"
    n = cursor.execute(sql)
    if (n > 0):
        logging.info("Get %s codes" % n)
        res = cursor.fetchall()
        logging.info(str(res))
        codes = []
        for code in res:
            codes.append(code[0])
        logging.info(str(codes))
        return codes
    else:
        return False

def set_invalid(conn, verifier):
    logging = Logging.get_logger('set_invalid')
    logging.info(" HERE ")
    cursor = conn.cursor()
    sql = "update code set is_valid=0 where verifier = %s"
    n = cursor.execute(sql, verifier)
    if (1 == n):
        logging.info("Set code invalid OK!")
        return True
    else:
        logging.error("Set code invalid Failed!")
        return False

def do_auth(conn):
    logging = Logging.get_logger('do_auth')
    client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    url = client.get_authorize_url()
    webbrowser.open(url)
    time.sleep(2)

    codes = False
    while (False == codes):
        time.sleep(2)
        codes = get_codes(conn)

    verified_flag = False
    for c in codes:
        try:
            logging.info("Current code is: " + str(c))
            ret = client.request_access_token(c)
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(" <<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>  Incorrect Verifier Code!  <<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>> ")
            continue
        else:
            logging.info("----------=============--  Correct Verifier Code!  --================----------------")
            verifier = c
            verified_flag = True
            break

    if (False == verified_flag):
        logging.error("There is no correct verifier code so far.")
        sys.exit(1)
    else:
        if not set_invalid(conn, verifier):
            logging.error("Error Occured when set the invalid flag for verifier code")
            sys.exit(1)
        else:
            logging.info("Set the invalid flag for verifier code successfully!")

    access_token = ret.access_token
    expires_in = ret.expires_in

    logging.info("access_token = %s    expires_in = %s " %(access_token, expires_in))

    client.set_access_token(access_token, expires_in)
    while not client.is_expires():
        try:
            uid = client.get.account__get_uid().uid
        except weibo.APIError as apierr:
            logging.error(str(apierr))
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
        else:
            break
        logging.info("uid = %s " % uid)
    while not client.is_expires():
        try:
            u = client.get.users__show(uid=uid)
        except weibo.APIError as apierr:
            logging.error(str(apierr))
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
        else:
            logging.info("We are uing API from account: [uid = %s, name = %s]" % (u.id, u.screen_name))
            break
    return client


def store_comm_res(conn, comm_res, weibo_comment_id):
    logging = Logging.get_logger('store_comm_res')
    sql = "insert into send_result (weibo_comment_id, comment_id, comment_mid, source, created_at) values(%s,%s,%s,%s,%s)"
    res = (str(weibo_comment_id), comm_res['id'], comm_res['mid'], comm_res['source'], comm_res['created_at'])
    cursor = conn.cursor()
    n = cursor.execute(sql, res)
    if (1 == n):
        logging.info("Store comment result OK!")
        cursor.close()
        return
    else:
        logging.error("Store comment result Error!")
        cursor.close()
        logging.info("So far --> Created " + str(g_create) + " Comments In Total!")
        sys.exit(0)

def set_status_done(conn, weibo_comment_id):
    logging = Logging.get_logger('set_status_done')
    sql = "update weibo_comment set status = '1' where id = %s"
    cursor = conn.cursor()
    n = cursor.execute(sql, str(weibo_comment_id))
    if (1 == n):
        logging.info("Set Status OK!")
        cursor.close()
        return
    else:
        logging.error("Set Status Error!")
        cursor.close()
        logging.info("So far --> Created " + str(g_create) + " Comments In Total!")
        sys.exit(0)



def comments_create(conn, api, send_info):
    global g_create
    logging = Logging.get_logger('comments_create')
    for si in send_info:
        if (si[1] != None and (si[2] != None and si[2] != "")):
            while not api.is_expires():
                try:
                    logging.info("Sending mid => " + str(si[1]) + "   content => " + str(si[2]))
                    mid = si[1]
                    comment = "u'" + str(si[2]) + "  " + APP_ADDRESS + "'"
                    logging.info(mid)
                    logging.info(comment)
                    logging.info(str(COMMENT_ORI))
                    comm_res = api.post.comments__create(comment=u'lalala ', id=mid, comment_ori=COMMENT_ORI)
                    store_comm_res(conn, comm_res, si[0])
                except weibo.APIError as apierr:
                    logging.error(str(apierr))
                    logging.info("Created " + str(g_create) + " Comments In Total!")
                    time.sleep(30)
                except Exception as e:
                    logging.error(str(e))
                    logging.error("Unhandled Error Occured! -------> Mark")
                    sys.exit(0)
                else:
                    g_create += 1
                    set_status_done(conn, si[0])
                    time.sleep(WAITING_PERIOD)
                    break
        else:
            logging.warning("There is no Content or mid!!!")


def get_send_info(conn):
    logging = Logging.get_logger('get_send_info')
    sql = "select id, mid, content from weibo_send.weibo_comment where status='0' limit %s"
    cursor = conn.cursor()
    n = cursor.execute(sql, g_send_number)
    if (n < 0):
        logging.error("Error Occurred when get send info")
        logging.info("So far --> Created " + str(g_create) + " Comments In Total!")
        sys.exit(0)
    elif (n < g_send_number):
        logging.info("Get Send Info OK! Get " + str(n) + " this time, less than " + str(g_send_number))
    elif (g_send_number == n):
        logging.info("Get Send Info OK!")
    send_info = cursor.fetchall()
    return send_info




def main():
    logging = Logging.get_logger('main')
    logging.info("START --> ")
    conn_code = MySQLdb.connect(host=db_host, user=db_username, passwd=db_password, db="spider", charset="utf8")
    conn_create = MySQLdb.connect(host=db_host, user=db_username, passwd=db_password, db=db_database, charset="utf8")
    api = do_auth(conn_code)
    send_info = get_send_info(conn_create)
    conn_code.close()
    logging.info("Start to create comments according to send_info")
    comments_create(conn_create, api, send_info)
    conn_create.close()
    logging.info("Created " + str(g_create) + " Comments In Total!")
    logging.info(" ---> END")


if __name__ == "__main__":
    main()


