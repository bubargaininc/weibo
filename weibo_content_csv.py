#!/usr/local/bin/python3

#-*- coding: utf-8 -*-

import os, sys, getopt 
from weibopy.auth import OAuthHandler
from weibopy.api import API
from weibopy.error import WeibopError
import webbrowser
import pymysql
import time
import csv
import codecs


DEFAULT_FETCH_USERS_NUMBER	= 1
DEFAULT_ONE_PAGE_COUNT		= 100
DEFAULT_CITY_CODE		= 11 # beijing
DEFAULT_CSV_PATH		= "csv/"

APP_KEY				= 1830868372
APP_SECRET			= """425d41c01a336ab667e4b92fc64812ac"""
BACK_URL			= "http://www.bubargain.com/backurl"

class Mode:
    FROM_DB     = 1
    FROM_NAME   = 2

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


# global vars:
g_city_code 		= DEFAULT_CITY_CODE
g_one_page_count	= DEFAULT_ONE_PAGE_COUNT 
g_fetch_users_number	= DEFAULT_FETCH_USERS_NUMBER
g_stored_counter	= 0
g_mode			= Mode.FROM_DB
g_name			= ""
g_person_counter	= 0


def do_auth():
    logging = Logging.get_logger('do_auth')
    auth = OAuthHandler(APP_KEY, APP_SECRET, BACK_URL)
    auth_url = auth.get_authorization_url()
    request_token_key = auth.request_token.key
    request_token_secret = auth.request_token.secret
    auth.set_request_token(request_token_key, request_token_secret)
    webbrowser.open(auth_url)
    verifier = input("Verifier: ").strip()
    access_token = auth.get_access_token(verifier)
    ATK = access_token.key
    ATS = access_token.secret
    auth.setAccessToken(ATK, ATS)
    api = API(auth)
    user = api.verify_credentials()
    logging.info("We are uing API from account: [uid = %s, name = %s]" % (user.id, user.screen_name))
    return api


def fetch_one_user_statuses(api, _uid):
    logging = Logging.get_logger('fetch_one_user_statuses')
    all_statuses = []
    page_number = 1
    logging.info("count = %s" % g_one_page_count)
    logging.info("page = %s" % page_number)
    statuses = api.user_timeline(user_id=_uid, count=g_one_page_count, page=page_number)
    statuses_number = len(statuses)
    logging.info("Get %d statuses this time." % statuses_number)
    all_statuses.extend(get_statuses_data(statuses, statuses_number, _uid)) 
    while (statuses_number > 0):
        page_number += 1
        statuses = api.user_timeline(user_id=_uid, count=g_one_page_count, page=page_number)
        statuses_number = len(statuses)
        logging.info("Get %d statuses this time." % statuses_number)
        if (0 == statuses_number):
            logging.info("Have got all statuses of the user: %s" % _uid)
            break;
        else:
            all_statuses.extend(get_statuses_data(statuses, statuses_number, _uid))   
    #logging.info("all_statuses:  %s " % all_statuses)
    return all_statuses
        

def get_statuses_data(statuses, number, uid):
    logging = Logging.get_logger('get_statuses_data')
    data = []
    for index in range(0, number):
        if ('转发微博。' != statuses[index].text):
            gender = statuses[index].user.gender
            location = statuses[index].user.location
            loc = location.split(' ')
            province = loc[0]
            if (2 == len(loc)):
                city = loc[1]
            else:
                city = ''
            weibo_id = str(statuses[index].id)
            created_at = str(statuses[index].created_at)
            source = statuses[index].source
            text = str(statuses[index].text)
            data.append((uid, gender, province, city, weibo_id, created_at, source, text))
            #logging.info(str(data))
    return data



def is_exist(conn, weibo_id):
    logging = Logging.get_logger('is_exist')
    cursor = conn.cursor()
    sql = "select id from statuses where weibo_id = %s"
    param = weibo_id
    n = cursor.execute(sql, param)
    if (0 == n):
        cursor.close()
        return False
    elif (1 == n):
        #logging.info("Exist in users, uid = %s" % uid)
        cursor.close()
        return True
    else:
        logging.error("Error Occured when check the uid = %s in users" % uid)
        cursor.close()
        conn.close()
        logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
        sys.exit(1)


def safe_path(path):
    if (not os.path.exists(path)):
        os.mkdir(path)


def store_one_user_statuses(conn, statuses, uid):
    global g_stored_counter
    logging = Logging.get_logger('store_one_user_statuses')
    file_name = DEFAULT_CSV_PATH + str(uid) + ".csv"
    logging.info("Preparing to write the statues of %s into the file: %s" % (str(uid), file_name))
    safe_path(DEFAULT_CSV_PATH)
    f = codecs.open(file_name, 'w', 'utf-8')
    writer = csv.writer(f)
    writer.writerow(['uid', 'gender', 'province', 'city', 'weibo_id', 'created_at', 'source', 'text'])
    for status in statuses:
        writer.writerow(status)
    f.close()
    logging.info("Written all statuses into %s " % file_name)
    g_stored_counter += 1
    #TODO: need to handle the exception here
    return True


#    cursor = conn.cursor()
#    sql = "insert into statuses (uid, gender, province, city, weibo_id, created_at, source, text) values(%s,%s,%s,%s,%s,%s,%s,%s)"
#    for s in statuses:
#        #logging.info("one of them statuses: " + str(s))
#        if (not is_exist(conn, s[1])):
#            #logging.info("This is a new status")
#            #logging.info("current status: %s" % str(s))
#            param = s
#            n = cursor.execute(sql, param)
#            if (1 == n):
#                #logging.info("Store statuses uid = %s  weibo_id = %s OK!!" % (uid, s[1]))
#                g_stored_counter += 1
#            else:
#                logging.error("Error Occured when store the status of uid = %s, weibo_id = %s +++=================------>>>>>>>>>>><<<<<<<<<<<------===============" % (s[0], s[1]))
#                cursor.close()
#                return False
#        else:
#            pass
#    cursor.close()
#    return True



def fetch_users(conn):
    logging = Logging.get_logger('fetch_users')
    if (Mode.FROM_DB == g_mode):
        logging.info("DB MODE!!! ")
        sql = "select uid from users limit %s"
        param = int(g_fetch_users_number)
    elif (Mode.FROM_NAME == g_mode):
        return [(g_name,)]
    else:
        logging.error("MODE IS NOT EXIST!!! ====================<><><><><><><><><><>==================== ")
        return False
    cursor = conn.cursor()
    n = cursor.execute(sql, param)
    if (Mode.FROM_DB == g_mode and g_fetch_users_number == n):
        logging.info("Fetch %d users Successfully" % n)
        uids = cursor.fetchall()
        cursor.close()
        logging.info("To Process Users: " + str(uids))
        return uids
    elif (Mode.FROM_DB == g_mode and n >= 0):
        logging.info("There is less than %d users, Fetched %d users Successfully" % (g_fetch_users_number, n))
        uids = cursor.fetchall()
        cursor.close()
        return uids
    elif (Mode.FROM_NAME == g_mode and 1 == n):
        logging.info("Fetched user: %s Successfully!" % g_name)
        uid = cursor.fetchone()
        logging.info("name: %s    uid: %s" % (g_name, str(uid)))
        cursor.close()
        return [uid]
    elif (0 == n):
        logging.warning("NO SUCH USER in DB!")
        cursor.close()
        return False
    else:
        logging.error("Database Operation ERROR!! n = %d" % n)
        cursor.close()
        return False
        

def fetch_store_one_user_statuses(conn, api, uid):
    logging = Logging.get_logger('fetch_store_one_user_statuses')
    fetch_result = fetch_one_user_statuses(api, uid)
    #logging.info("fetch_result: %s" % fetch_result)
    if (False == fetch_result):
        logging.error("ERROR Occured when fetching statuses")
        return False
    else:
        logging.info("Fetch statuses of uid: %s OK!!" % uid)
        if (False == store_one_user_statuses(conn, fetch_result, uid)):
            logging.error("ERROR Occured when storing statuses!")
            return False
        else:
            logging.info("Store statuses of uid: %s OK!!" % uid)
            return True


def fetch_store_statuses(conn, api, uids):
    global g_person_counter
    logging = Logging.get_logger('fetch_store_statuses')
    logging.info("uids: %s" % str(uids))
    for uid in uids:
        g_person_counter += 1
        logging.info("----------=-=-=-=-=-=-=-=-=-=========================--==-=-=-=-=->.>.>.>.>.>.>>>>>> person: %d START!!" % g_person_counter)
        if (True == fetch_store_one_user_statuses(conn, api, uid[0])):
            logging.info("-----------=-=-=-=-=-=-=-=-=-==========================---=-=-=-=-=-=-=-=-=--=-=-=-=-=-=-=>>>>>>>>>>> person: %d END!!" % g_person_counter)
        else:
            logging.error("Error Occured when process the person: %d   uid: %s", (g_person_counter, uid[0]))
            return False 
    logging.info("Fetch and Store %d persons Successfully!" % g_person_counter)
    return True

def fetch_statuses_to_database(conn):
    logging = Logging.get_logger('fetch_statuses_to_database')
    fetch_users_result = fetch_users(conn)
    if (False == fetch_users_result):
        logging.error("Error Occured When Fetching Users!!")
        logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
        sys.exit(1)
    else:
        logging.info("Fetch users OK!!")
        uids = fetch_users_result
    logging.info("Start to do Auth!!! ==============>>>>> ^_^")
    api = do_auth()
    logging.info("Done Auth!!! ==============>>>>> ^_^")
    if (True == fetch_store_statuses(conn, api, uids)):
        logging.info("Store All statuses Successfully!!!")
        return True
    else:
        logging.error("Store All statuses Failed!!!")
        return False




def main():
    global g_one_page_count, g_fetch_users_number, g_mode, g_name
    logging = Logging.get_logger('main')
    try:
        opts,args = getopt.getopt(sys.argv[1:],"p:c:u:n:")
        for op,value in opts:
            if op == "-p":
                g_one_page_count = int(value)
            elif op == "-u":
                g_fetch_users_number = int(value)
            elif op == "-n":
                g_name = str(value)
                logging.info(g_name)
                g_mode = Mode.FROM_NAME
        print(opts)  
        print(args) 
    except getopt.GetoptError:
        logging.error("Params are not defined well!")
        logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
        sys.exit(1)

    logging.info("START")
    conn = pymysql.connect(host="localhost", user="root", passwd="bubargain2012", db="spider", charset="utf8")
    fetch_statuses_to_database(conn)
    conn.close()
    logging.info("Stored " + str(g_stored_counter) + " New Statuses In Total!")
    logging.info("END")




if __name__ == "__main__":
    main()


