#!/usr/bin/python
#-*- coding=utf-8 -*-

import os
import sys
import getopt
import webbrowser
import MySQLdb
import time
import weibo
import urllib2

DEFAULT_FETCH_USERS_NUMBER = 10
DEFAULT_ONE_PAGE_COUNT     = 10
DEFAULT_CITY_CODE          = 11 # beijing

APP_KEY                    = 3983759328
APP_SECRET                 = """36d1bd885bb6553c201b50fc9912b756"""
CALLBACK_URL               = "http://www.uhquan.com:8888/callback"

class Mode:
    FROM_DB     = 1
    FROM_NAME   = 2


# global vars:
g_city_code          = DEFAULT_CITY_CODE
g_one_page_count     = DEFAULT_ONE_PAGE_COUNT
g_fetch_users_number = DEFAULT_FETCH_USERS_NUMBER
g_stored_counter     = 0
g_mode               = Mode.FROM_DB
g_name               = ""
g_person_counter     = 0


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
    #command = "curl " + url
    #logging.info(command)
    #os.system(command)
    # verifier = input("Verifier: ").strip()
    # verifier = get_code(conn)
    #client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)

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
    if not client.is_expires():
        try:
            uid = client.get.account__get_uid().uid
        except weibo.APIError as apierr:
            logging.error(str(apierr))
            logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
            time.sleep(150)
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
            time.sleep(150)
        logging.info("uid = %s " % uid)
        try:
            u = client.get.users__show(uid=uid)
        except weibo.APIError as apierr:
            logging.error(str(apierr))
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
            sys.exit(1)
        #logging.info(str(u))
        logging.info("We are uing API from account: [uid = %s, name = %s]" % (u.id, u.screen_name))
    return client


def fetch_one_user_bilaterals(api, _uid):
    logging = Logging.get_logger('fetch_one_user_bilaterals')
    all_bilaterals = []
    page_number = 1
    #logging.info("count = %s" % g_one_page_count)
    #logging.info("page = %s" % page_number)
    while not api.is_expires():
        try:
            bilaterals = api.friendships__friends__bilateral(uid=_uid, count=g_one_page_count, page=page_number)
        except weibo.APIError as apierr:
            logging.error(str(apierr))
            logging.info("So Far, ---> Stored " + str(g_stored_counter) + " New Person In Total!")
            sleep(300)
            # sys.exit(1)
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            logging.info("So Far, ---> Stored " + str(g_stored_counter) + " New Person In Total!")
            sleep(300)
            # sys.exit(1)
        else:
            break

    bilaterals_number = len(bilaterals.users)
    logging.info("Get %d bilaterals this time." % bilaterals_number)
    all_bilaterals.extend(get_bilaterals_data(bilaterals, bilaterals_number))
    while (bilaterals_number > 0):
        page_number += 1
        while not api.is_expires():
            try:
                bilaterals = api.friendships__friends__bilateral(uid=_uid, count=g_one_page_count, page=page_number)
            except weibo.APIError as apierr:
                logging.error(str(apierr))
                logging.info("I am tired, I am sleeping during the next 5 minutes...")
                sleep(300)
            except urllib2.HTTPError as httperr:
                logging.error(str(httperr))
                logging.error(str(httperr.read()))
                logging.info("I am tired, I am sleeping during the next 5 minutes...")
                sleep(300)
            else:
                break
        # bilaterals = api.friendships__friends__bilateral(uid=_uid, count=g_one_page_count, page=page_number)
        bilaterals_number = len(bilaterals.users)
        logging.info("Get %d bilaterals this time." % bilaterals_number)
        if (0 == bilaterals_number):
            logging.info("Have got all bilaterals of the user: %s" % _uid)
            break;
        else:
            all_bilaterals.extend(get_bilaterals_data(bilaterals, bilaterals_number))
    #logging.info("all_bilaterals:  %s " % all_bilaterals)
    return all_bilaterals


def set_boolean(value):
    if (True == value):
        return "T"
    else:
        return "F"


def get_bilaterals_data(bilaterals, number):
    logging = Logging.get_logger('get_bilaterals_data')
    data = []
    for index in range(0, number):
        uid = bilaterals.users[index]['id']
        #logging.info("current uid = %s " % str(uid))
        name = bilaterals.users[index]['name']
        if ('' == name or None == name):
            continue
        description = bilaterals.users[index]['description']
        #logging.info(description)
        url = bilaterals.users[index]['url']
        gender = bilaterals.users[index]['gender']
        if ('m' == gender):
            gender = 'male'
        else:
            gender = 'female'
        location = bilaterals.users[index]['location']
        loc = location.split(' ')
        if (2 == len(loc)):
            province = loc[0]
            city = loc[1]
        elif (1 == len(loc)):
            province = loc[0]
            city = ''
        else:
            logging.info("location info error!!")

        followers_count    = bilaterals.users[index]['followers_count']
        followers_count    = str(followers_count)
        friends_count      = bilaterals.users[index]['friends_count']
        friends_count      = str(friends_count)
        statuses_count     = bilaterals.users[index]['statuses_count']
        statuses_count     = str(statuses_count)
        favourites_count   = bilaterals.users[index]['favourites_count']
        favourites_count   = str(favourites_count)
        created_at         = bilaterals.users[index]['created_at']
        allow_all_act_msg  = bilaterals.users[index]['allow_all_act_msg']
        allow_all_act_msg  = set_boolean(allow_all_act_msg)
        geo_enabled        = bilaterals.users[index]['geo_enabled']
        geo_enabled        = set_boolean(geo_enabled)
        verified           = bilaterals.users[index]['verified']
        verified           = set_boolean(verified)
        allow_all_comment  = bilaterals.users[index]['allow_all_comment']
        allow_all_comment  = set_boolean(allow_all_comment)
        verified_reason    = bilaterals.users[index]['verified_reason']
        bi_followers_count = bilaterals.users[index]['bi_followers_count']
        bi_followers_count = str(bi_followers_count)
        data.append((uid,name,gender,province,city,url,description,followers_count,friends_count,statuses_count,favourites_count,created_at,allow_all_act_msg,geo_enabled,verified,allow_all_comment,verified_reason,bi_followers_count))
    #logging.info("Get bilaterals data OK!! ====----====---->>> data: %s" % data)
    #logging.info("Get bilaterals data OK!! ")
    return data


def is_exist(conn, uid):
    logging = Logging.get_logger('is_exist')
    cursor = conn.cursor()
    sql = "select id from users where uid = %s"
    param = uid
    n = cursor.execute(sql, param)
    if (0 == n):
        #logging.info("The user does not exist in users, uid = %s" % uid)
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


def reset_extended(conn, uid):
    logging = Logging.get_logger('reset_extended')
    cursor = conn.cursor()
    sql = "update users set extended='T' where uid = %s"
    param = uid
    n = cursor.execute(sql, param)
    if (n >= 0):
        logging.info("Reset Extended Flag OK!")
        cursor.close()
        return True
    else:
        logging.error("Reset Extended Flag FAILED!!!")
        cursor.close()
        return False


def store_one_user_bilaterals(conn, bilaterals):
    global g_stored_counter
    logging = Logging.get_logger('store_one_user_bilaterals')
    cursor = conn.cursor()
    #sql = "insert into temp_users (uid, nick_name) values(%s,%s)"
    sql = "insert into users (uid, nick_name, gender, province, city, url, description, followers_count, friends_count, statuses_count, favourites_count, created_at, allow_all_act_msg, geo_enabled, verified, allow_all_comment, verified_reason, bi_followers_count) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    logging.info("Storing ...")
    for b in bilaterals:
        #logging.info("one of them b: " + str(b))
        if (not is_exist(conn, b[0])):
            #logging.info("This is a new user!!!")
            param = b
            #logging.info(str(param))
            #logging.info(param[6])
            n = cursor.execute(sql, param)
            if (1 == n):
                #logging.info("Store bilateral uid = %s, name= %s OK!!" % (b[0], b[1]))
                g_stored_counter += 1
            else:
                logging.error("Error Occured when store the user of uid = %s, name= %s +++=================------>>>>>>>>>>><<<<<<<<<<<------===============" % (b[0], b[1]))
                cursor.close()
                return False
        else:
            pass
            #logging.info("This user has been stored!!! uid = %s, name = %s" % (b[0], b[1]))
    cursor.close()
    logging.info("Storing Accomplished!")
    return True


def set_selected(cursor, uids):
    logging = Logging.get_logger('set_selected')
    sql = "update users set selected='T' where uid in"
    all_uid = '('
    for u in uids:
        all_uid += str(u[0]) + ','
    uid_set = all_uid.rstrip(',')
    uid_set += ');'
    logging.info("All uids: " + uid_set)
    sql += uid_set
    n = cursor.execute(sql)
    #logging.info(sql)
    #logging.info("len(uids) = %s, n = %s" % (len(uids), n))
    if (len(uids) == n):
        logging.info("Set Selected Flag Successfully!")
        return True
    else:
        logging.error("Set Selected Flag False!")
        return False


def fetch_users(conn):
    logging = Logging.get_logger('fetch_users')
    if (Mode.FROM_DB == g_mode):
        logging.info("DB MODE!!! ")
        lock_sql = "lock table users write;"
        sql_fetch = "select uid from users where extended='F' and selected='F' limit %s"
        unlock_sql = "unlock tables;"
        param = int(g_fetch_users_number)
    elif (Mode.FROM_NAME == g_mode):
        return [(g_name,)]
        #logging.info("[FETCH_USERS_NAME]: NAME MODE!!! ")
        #sql = "select uid from users where nick_name = %s"
        #param = g_name
    else:
        logging.info("MODE IS NOT EXIST!!! ====================<><><><><><><><><><>==================== ")
        return False
    logging.info("Preparing Cursor...")
    cursor = conn.cursor()
    logging.info("Ready to get the lock...")
    cursor.execute(lock_sql)
    logging.info("Got the LOCK!!!!!!!! GREAT!!!")
    n = cursor.execute(sql_fetch, param)
    logging.info("Fetch Users OK!")
    if (Mode.FROM_DB == g_mode and g_fetch_users_number == n):
        logging.info("Fetch %d users Successfully" % n)
        uids = cursor.fetchall()
        if not set_selected(cursor, uids):
            cursor.execute(unlock_sql)
            logging.info("UNLOCK 1")
            cursor.close()
            return False
        else:
            cursor.execute(unlock_sql)
            logging.info("UNLOCK 2")
            cursor.close()
            logging.info("To Process Users: " + str(uids))
            return uids
    elif (Mode.FROM_DB == g_mode and n >= 0):
        logging.info("There is less than %d users, Fetched %d users Successfully" % (g_fetch_users_number, n))
        uids = cursor.fetchall()
        if not set_selected(cursor, uids):
            cursor.execute(unlock_sql)
            logging.info("UNLOCK 3")
            cursor.close()
            return False
        else:
            cursor.execute(unlock_sql)
            logging.info("UNLOCK 4")
            cursor.close()
            return uids
    # elif (Mode.FROM_NAME == g_mode and 1 == n):
    #     logging.info("Fetched user: %s Successfully!" % g_name)
    #     uid = cursor.fetchone()
    #     logging.info("name: %s    uid: %s" % (g_name, str(uid)))
    #     cursor.close()
    #     return [uid]
    elif (0 == n):
        logging.warning("NO SUCH USER in DB!")
        cursor.execute(unlock_sql)
        logging.info("UNLOCK 5")
        cursor.close()
        return False
    else:
        logging.error("Database Operation ERROR!! n = %d" % n)
        cursor.execute(unlock_sql)
        logging.info("UNLOCK 6")
        cursor.close()
        return False


def fetch_store_one_user_bilaterals(conn, api, uid):
    logging = Logging.get_logger('fetch_store_one_user_bilaterals')
    fetch_result = fetch_one_user_bilaterals(api, uid)
    time.sleep(4)
    #logging.info("[FETCH_STORE_ONE]: fetch_result: %s" % fetch_result)
    if (False == fetch_result):
        logging.error("ERROR Occured when fetching bilaterals!")
        return False
    else:
        logging.info("Fetch bilaterals of uid: %s OK!!" % uid)
        if (False == store_one_user_bilaterals(conn, fetch_result)):
            logging.error("ERROR Occured when storing bilaterals!")
            return False
        else:
            logging.info("Store bilaterals of uid: %s OK!!" % uid)
            return True


def fetch_store_bilaterals(conn, api, uids):
    global g_person_counter
    logging = Logging.get_logger('fetch_store_bilaterals')
    #logging.info("uids: %s" % str(uids))
    for uid in uids:
        g_person_counter += 1
        logging.info("----------=-=-=-=-=-=-=-=-=-=========================--==-=-=-=-=->.>.>.>.>.>.>>>>>> person: %d START!!" % g_person_counter)
        if (True == fetch_store_one_user_bilaterals(conn, api, uid[0])):
            if(True == reset_extended(conn, uid[0])):
                logging.info("Reset extended flag for the person: %d   uid: %s OK!" % (g_person_counter, uid[0]))
                logging.info("-----------=-=-=-=-=-=-=-=-=-==========================---=-=-=-=-=-=-=-=-=--=-=-=-=-=-=-=>>>>>>>>>>> person: %d END!!" % g_person_counter)
            else:
                logging.error("Error! Occured when reset extended flag for the person: %d   uid: %s", (g_person_counter, uid[0]))
        else:
            logging.error("Error! Occured when process the person: %d   uid: %s", (g_person_counter, uid[0]))
            return False
    logging.info("Fetch and Store %d persons Successfully!" % g_person_counter)
    return True


def fetch_bilaterals_to_database(conn):
    logging = Logging.get_logger('fetch_bilaterals_to_database')
    fetch_users_result = fetch_users(conn)
    if (False == fetch_users_result):
        logging.error("Error Occured When Fetching Users!!")
        logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
        sys.exit(1)
    else:
        logging.info("Fetch users OK!!")
        uids = fetch_users_result
    logging.info("Start to do Auth!!! ==============>>>>> ^_^")
    api = do_auth(conn)
    logging.info("Done Auth!!! ==============>>>>> ^_^")
    #bilaterals = fetch_bilaterals(api, uids)
    if (True == fetch_store_bilaterals(conn, api, uids)):
        logging.info("Store All Bilaterals Successfully!!!")
        return True
    else:
        logging.error("Store All Bilaterals Failed!!!")
        return False


def main():
    global g_city_code, g_one_page_count, g_fetch_users_number, g_mode, g_name
    logging = Logging.get_logger('main')
    try:
        opts,args = getopt.getopt(sys.argv[1:],"p:c:u:n:")
        for op,value in opts:
            if op == "-p":
                g_one_page_count = int(value)
            elif op == "-c":
                g_city_code = str(value)
            elif op == "-u":
                g_fetch_users_number = int(value)
            elif op == "-n":
                g_name = str(value)
                logging(g_name)
                g_mode = Mode.FROM_NAME
        print(opts)
        print(args)
    except getopt.GetoptError:
        logging.error("Params are not defined well!")
        logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
        sys.exit(1)

    logging.info("START")
    conn = MySQLdb.connect(host="localhost", user="root", passwd="RooT", db="spider", charset="utf8")
    fetch_bilaterals_to_database(conn)
    conn.close()
    logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
    logging.info("END")




if __name__ == "__main__":
    main()


