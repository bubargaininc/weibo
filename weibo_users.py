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
import httplib

DEFAULT_FETCH_USERS_NUMBER = 10
DEFAULT_ONE_PAGE_COUNT     = 10
DEFAULT_CITY_CODE          = 11 # beijing

# Using at uhquan.com
APP_KEY                    = 3983759328
APP_SECRET                 = """36d1bd885bb6553c201b50fc9912b756"""
CALLBACK_URL               = "http://www.uhquan.com:8888/callback"

# Using at local
#APP_KEY                    = 1145738428
#APP_SECRET                 = """275b151558a7007b0c8dab0060588f42"""
#CALLBACK_URL               = "http://76.116.64.145:8888/callback"

class Mode:
    FROM_DB     = 1
    FROM_NAME   = 2


# global vars:
g_city_code               = DEFAULT_CITY_CODE
g_one_page_count          = DEFAULT_ONE_PAGE_COUNT
g_fetch_users_number      = DEFAULT_FETCH_USERS_NUMBER
g_stored_current_counter  = 0
g_stored_overall_counter  = 0
g_mode                    = Mode.FROM_DB
g_name                    = ""
g_person_counter          = 0
g_person_current_received = 0
g_person_overall_received = 0
g_api_current_counter     = 0
g_api_overall_counter     = 0
g_flag                    = 0
g_token_number            = 0
g_api                     = ""
g_current_token           = ""


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

def get_E(received, stored):
    if (received <= 0 or stored < 0):
        return "0"
    else:
        return str(float(stored)/float(received)*100) + "%"

def get_apiE(api_counter, stored):
    if (api_counter <= 0 or stored < 0):
        return "0"
    else:
        return str(float(stored)/float(api_counter))

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

# def get_access_token():
#     global g_flag
#     tokens= ['2.00A1YbCDim8b2E487325fa560MJttB',\
# 	    '2.00veBuDDim8b2E2832acfdc5_EIRXE',\
#         '2.00_6x7CDim8b2E8729c251e67UnBMB',
#         '2.00RKc2ADim8b2E7362f844ffXIm5IB',\
# 		'2.00AReKdCim8b2E7a057b89be2qOh8E',\
# 		'2.00JF42GDim8b2Eb34140ba67w_C4UE',\
# 		'2.00Fo3V3Bim8b2E51c210b31c0rW4ly',\
# 		'2.00xPQAoBim8b2E2cc3735ae3N65PAC']
#     g_flag += 1
#     if(g_flag > len(tokens)):
#         g_flag = 0
#     print(Logging.timestamp() + 'get_access_token:' + tokens[g_flag]).encode('utf8')
#     return tokens[g_flag]


def set_current_token_invalid(conn):
    logging = Logging.get_logger('set_current_token_invalid')
    cursor = conn.cursor()
    sql = "update tokens set is_valid='F' where token=%s"
    n = cursor.execute(sql, g_current_token)
    if (1 == n):
        logging.info("Set Current Token Invalid Successfully!")
        cursor.close()
    else:
        logging.error("ERROR Occured When Set Current Token Invalid!")
        cursor.close()
        print_statistic(logging)
        sys.exit(0)

def get_token_expire(conn):
    logging = Logging.get_logger('get_token_expire')
    cursor = conn.cursor()
    sql = "select token, expire from tokens where is_valid='T'"
    n = cursor.execute(sql)
    if (n >= 1):
        to_ex = cursor.fetchall()
        for te in to_ex:
            #if (time.time() > te[1]):
            if True: # which means this is not expired!!!
                cursor.close()
                return te
            else:
                logging.warning("The token fetched just now is expired!!!")
                n = cursor.execute("delete from tokens where token = %s", te[0])
                if (1 == n):
                    logging.info("Deleted Expired Token Successfully!")
                else:
                    logging.error("Error Occured When Delete Expired Token!!! Check the database!")
                    cursor.close()
                    print_statistic(logging)
                    sys.exit(0)
        logging.warning("There is no valid token in database!")
        cursor.close()
        return False
    elif (0 == n):
        logging.warning("There is no valid token in database!")
        cursor.close()
        print_statistic(logging)
        return False
    else:
        logging.error("Error Occured When Select Token!!! Check the database!")
        cursor.close()
        print_statistic(logging)
        sys.exit(0)



def get_api(conn):
    global g_api_current_counter, g_stored_current_counter, g_person_current_received, g_current_token, g_token_number
    logging = Logging.get_logger('get_api')
    g_token_number += 1
    to_ex = get_token_expire(conn)
    while not to_ex:
        logging.error("There is no valid token currently!!!")
        # call_fetch_new_token()
        time.sleep(60)
        to_ex = get_token_expire(conn)
    else:
        logging.info("Got Token: " + str(to_ex[0]) + "; Got Expire Time: " + str(to_ex[1]))
        g_current_token = to_ex[0]
        api = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
        api.set_access_token(to_ex[0], to_ex[1])
        logging.info("Get API Successfully!")
        g_api_current_counter     = 0
        g_stored_current_counter  = 0
        g_person_current_received = 0
        return api

def print_statistic(logging):
    logging.info("<<<<< START >>>>> ----------------- STATISTIC ----------------- <<<<< START >>>>>")
    logging.info("CURRENT => Stored   : " + str(g_stored_current_counter))
    logging.info("           Received : " + str(g_person_current_received))
    logging.info("           API Call : " + str(g_api_current_counter))
    logging.info("           E        : " + get_E(g_person_current_received, g_stored_current_counter))
    logging.info("           apiE     : " + get_apiE(g_api_current_counter, g_stored_current_counter))
    logging.info("-----------------------------------------------------------------------------")
    logging.info("OVERALL => Stored   : " + str(g_stored_overall_counter))
    logging.info("           Received : " + str(g_person_overall_received))
    logging.info("           API Call : " + str(g_api_overall_counter))
    logging.info("           E        : " + get_E(g_person_overall_received, g_stored_overall_counter))
    logging.info("           apiE     : " + get_apiE(g_api_overall_counter, g_stored_overall_counter))
    logging.info("-----------------------------------------------------------------------------")
    logging.info("Number of Token used: " + str(g_token_number))
    logging.info("<<<<< END >>>>> -------------------- STATISTIC -------------------- <<<<< END >>>>>")



# def do_auth_new():
#     logging = Logging.get_logger('do_auth')
#     client = weibo.APIClient(app_key=APP_KEY,app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
#     client.set_access_token(get_access_token(), 99999)
#     return client

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
    while not client.is_expires():
        try:
            uid = client.get.account__get_uid().uid
        except weibo.APIError as apierr:
            logging.error(str(apierr))
            print_statistic(logging)
            time.sleep(300)
            if(g_api_current_counter >= 999):
                g_api = do_auth_new()
                g_api_current_counter = 0
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            print_statistic(logging)
            time.sleep(300)
        else:
            break
        logging.info("uid = %s " % uid)
    while not client.is_expires():
        try:
            u = client.get.users__show(uid=uid)
        except weibo.APIError as apierr:
            logging.error(str(apierr))
            print_statistic(logging)
            time.sleep(300)
            if(g_api_current_counter >= 999):
                g_api = do_auth_new()
                g_api_current_counter = 0
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            print_statistic(logging)
            time.sleep(300)
        else:
            logging.info("We are uing API from account: [uid = %s, name = %s]" % (u.id, u.screen_name))
            break
    return client


def fetch_one_user_followers(conn, _uid):
    global g_api, g_person_current_received, g_person_overall_received, g_api_current_counter, g_api_overall_counter
    logging = Logging.get_logger('fetch_one_user_followers')
    all_followers = []
    page_number = 1
    while not g_api.is_expires():
        try:
            followers = g_api.friendships__followers(uid=_uid, count=g_one_page_count, cursor=0, trim_status=0)
            g_api_current_counter += 1
            g_api_overall_counter += 1
        except weibo.APIError as apierr:
            logging.error(str(apierr))
            print_statistic(logging)
            if (10023 == apierr['error_code']):
                logging.error("OUT OF RATE! WTF!")
                logging.info("Applying New API ...")
                set_current_token_invalid()
                g_api = get_api(conn)
            else:
                logging.error("This Exception From Sina has not been handled! ***************---==-->> MARK!! <<--==---***************") 
                time.sleep(60)
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            print_statistic(logging)
            time.sleep(60)
        except urllib2.URLError as urlerr:
            logging.error(str(urlerr))
            print_statistic(logging)
            if hasattr(urlerr,"reason"):
                logging.error(str(urlerr.reason))
            elif hasattr(urlerr,"code"):
                logging.error("Error Code:" + str(urlerr.code))
                logging.error("Error Reason: " + str(urlerr.read()))
                time.sleep(60)
        except httplib.BadStatusLine as bslerr:
            logging.error("httplib.BadStatusLine ERROR!!!")
            logging.error("Error Code:" + str(bslerr.code))
            logging.error("Error Reason: " + str(urlerr.read()))
            print_statistic(logging)
            time.sleep(5)
        except Exception as e:
            logging.error(str(e))
            print_statistic(logging)
            logging.error("This Exception has not been handled! ***************---==-->> MARK!! MARK!! MARK!! <<--==---***************")
            time.sleep(5)
        else:
            if (g_api_current_counter >= 999):
                print_statistic(logging)
                logging.warning("The Current API has been used for >= 999 times!")
                logging.info("Applying New API ...")
                set_current_token_invalid()
                g_api = get_api(conn)
            break
    # next_cursor       = followers.next_cursor
    followers_number  = len(followers.users)
    g_person_overall_received += followers_number
    g_person_current_received += followers_number
    logging.info("Get %d followers this time." % followers_number)
    all_followers.extend(get_followers_data(followers, followers_number))
    # for 200 limitation
    next_cursor = 200
    while not 0 == next_cursor:
        while not g_api.is_expires():
            try:
                followers = g_api.friendships__followers(uid=_uid, count=g_one_page_count, cursor=next_cursor, trim_status=0)
                g_api_current_counter += 1
                g_api_overall_counter += 1
            except weibo.APIError as apierr:
                logging.error(str(apierr))
                print_statistic(logging)
                if (10023 == apierr['error_code']):
                    logging.error("OUT OF RATE! WTF!")
                    logging.info("Applying New API ...")
                    set_current_token_invalid()
                    g_api = get_api(conn)
                else:
                    logging.error("This Exception From Sina has not been handled! ***************---==-->> MARK!! <<--==---***************") 
                    time.sleep(60)
            except urllib2.HTTPError as httperr:
                logging.error(str(httperr))
                logging.error(str(httperr.read()))
                print_statistic(logging)
                time.sleep(60)
            except urllib2.URLError as urlerr:
                logging.error(str(urlerr))
                print_statistic(logging)
                if hasattr(urlerr,"reason"):
                    logging.error(str(urlerr.reason))
                elif hasattr(urlerr,"code"):
                    logging.error("Error Code:" + str(urlerr.code))
                    logging.error("Error Reason: " + str(urlerr.read()))
                    time.sleep(60)
            except httplib.BadStatusLine as bslerr:
                logging.error("httplib.BadStatusLine ERROR!!!")
                logging.error("Error Code:" + str(bslerr.code))
                logging.error("Error Reason: " + str(urlerr.read()))
                print_statistic(logging)
                time.sleep(5)
            except Exception as e:
                logging.error(str(e))
                print_statistic(logging)
                logging.error("This Exception has not been handled! ***************---==-->> MARK!! MARK!! MARK!! <<--==---***************")
                time.sleep(5)
            else:
                if (g_api_current_counter >= 999):
                    print_statistic(logging)
                    logging.warning("The Current API has been used for >= 999 times!")
                    logging.info("Applying New API ...")
                    set_current_token_invalid()
                    g_api = get_api(conn)
                break
        next_cursor       = followers.next_cursor
        followers_number  = len(followers.users)
        g_person_overall_received += followers_number
        g_person_current_received += followers_number
        logging.info("Get %d followers this time." % followers_number)
        all_followers.extend(get_followers_data(followers, followers_number))
    else:
        logging.info("Have got all followers of the user: %s" % _uid)
        return all_followers



def set_boolean(value):
    if (True == value):
        return "T"
    else:
        return "F"


def get_followers_data(followers, number):
    logging = Logging.get_logger('get_followers_data')
    data = []
    for index in range(0, number):
        uid = followers.users[index]['id']
        #logging.info("current uid = %s " % str(uid))
        name = followers.users[index]['name']
        if ('' == name or None == name):
            continue
        description = followers.users[index]['description']
        #logging.info(description)
        url = followers.users[index]['url']
        gender = followers.users[index]['gender']
        if ('m' == gender):
            gender = 'm'
        else:
            gender = 'f'
        location = followers.users[index]['location']
        loc = location.split(' ')
        if (2 == len(loc)):
            province = loc[0]
            city = loc[1]
        elif (1 == len(loc)):
            province = loc[0]
            city = ''
        else:
            logging.info("location info error!!")

        followers_count    = followers.users[index]['followers_count']
        followers_count    = str(followers_count)
        friends_count      = followers.users[index]['friends_count']
        friends_count      = str(friends_count)
        statuses_count     = followers.users[index]['statuses_count']
        statuses_count     = str(statuses_count)
        favourites_count   = followers.users[index]['favourites_count']
        favourites_count   = str(favourites_count)
        created_at         = followers.users[index]['created_at']
        allow_all_act_msg  = followers.users[index]['allow_all_act_msg']
        allow_all_act_msg  = set_boolean(allow_all_act_msg)
        geo_enabled        = followers.users[index]['geo_enabled']
        geo_enabled        = set_boolean(geo_enabled)
        verified           = followers.users[index]['verified']
        verified           = set_boolean(verified)
        allow_all_comment  = followers.users[index]['allow_all_comment']
        allow_all_comment  = set_boolean(allow_all_comment)
        verified_reason    = followers.users[index]['verified_reason']
        bi_followers_count = followers.users[index]['bi_followers_count']
        bi_followers_count = str(bi_followers_count)
        data.append((uid,name,gender,province,city,url,description,followers_count,friends_count,statuses_count,favourites_count,created_at,allow_all_act_msg,geo_enabled,verified,allow_all_comment,verified_reason,bi_followers_count))
    #logging.info("Get followers data OK!! ====----====---->>> data: %s" % data)
    #logging.info("Get followers data OK!! ")
    return data


def is_exist(cursor, uid):
    logging = Logging.get_logger('is_exist')
    # cursor = conn.cursor()
    sql = "select id from users where uid = %s"
    param = uid
    n = cursor.execute(sql, param)
    if (0 == n):
        #logging.info("The user does not exist in users, uid = %s" % uid)
        # cursor.close()
        return False
    elif (1 == n):
        #logging.info("Exist in users, uid = %s" % uid)
        # cursor.close()
        return True
    else:
        logging.error("Error Occured when check the uid = %s in users" % uid)
        # cursor.close()
        # conn.close()
        print_statistic(logging)
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


def store_one_user_followers(cursor, followers):
    global g_stored_current_counter, g_stored_overall_counter
    logging = Logging.get_logger('store_one_user_followers')
    # cursor = conn.cursor()
    # sql = "INSERT INTO users (uid, nick_name, gender, province, city, url, description, followers_count, friends_count, statuses_count, favourites_count, created_at, allow_all_act_msg, geo_enabled, verified, allow_all_comment, verified_reason, bi_followers_count) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE nick_name=VALUES(nick_name), gender=VALUES(gender), province=VALUES(province), city=VALUES(city), url=VALUES(url), description=VALUES(description), followers_count=VALUES(followers_count), friends_count=VALUES(friends_count), statuses_count=VALUES(statuses_count), favourites_count=VALUES(favourites_count), allow_all_act_msg=VALUES(allow_all_act_msg), geo_enabled=VALUES(geo_enabled), verified=VALUES(verified), allow_all_comment=VALUES(allow_all_comment), verified_reason=VALUES(verified_reason), bi_followers_count=VALUES(bi_followers_count)"
    sql = "INSERT INTO users (uid, nick_name, gender, province, city, url, description, followers_count, friends_count, statuses_count, favourites_count, created_at, allow_all_act_msg, geo_enabled, verified, allow_all_comment, verified_reason, bi_followers_count) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    logging.info("Storing ...")
    for b in followers:
        #logging.info("one of them b: " + str(b))
        if (not is_exist(cursor, b[0])):
            param = b
            n = cursor.execute(sql, param)
            if (1 == n or 2 == n):
                g_stored_overall_counter += 1
                g_stored_current_counter += 1
            else:
                logging.info("n = %s" % n)
                logging.error("Error Occured when store the user of uid = " + str(b[0]).encode('utf8') + "name = " + str(b[1]).encode('utf8') + " +++=================------>>>>>>>>>>><<<<<<<<<<<------===============")
                return False
        else:
            pass
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


def fetch_store_one_user_followers(conn, uid):
    global g_api
    logging = Logging.get_logger('fetch_store_one_user_followers')
    fetch_result = fetch_one_user_followers(conn, uid)
    #time.sleep(4)
    if (False == fetch_result):
        logging.error("ERROR Occured when fetching followers!")
        return False
    else:
        logging.info("Fetch followers of uid: %s OK!!" % uid)
        cursor = conn.cursor()
        cursor.execute("SET AUTOCOMMIT = 0")
        if (False == store_one_user_followers(cursor, fetch_result)):
            logging.error("ERROR Occured when storing followers!")
            cursor.close()
            return False
        else:
            #logging.info("Store followers of uid: %s OK!!" % uid)
            cursor.execute("commit")
            cursor.close()
            return True


def fetch_store_followers(conn, uids):
    global g_person_counter,g_api
    logging = Logging.get_logger('fetch_store_followers')
    #logging.info("uids: %s" % str(uids))
    for uid in uids:
        g_person_counter += 1
        logging.info("----------=-=-=-=-=-=-=-=-=-=========================--==-=-=-=-=->.>.>.>.>.>.>>>>>> person: %d START!!" % g_person_counter)
        if (True == fetch_store_one_user_followers(conn, uid[0])):
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


def fetch_followers_to_database(conn):
    global g_api
    logging = Logging.get_logger('fetch_followers_to_database')
    fetch_users_result = fetch_users(conn)
    if (False == fetch_users_result):
        logging.error("Error Occured When Fetching Users!!")
        print_statistic(logging)
        sys.exit(1)
    else:
        logging.info("Fetch users OK!!")
        uids = fetch_users_result
    logging.info("Start to Get API!!! ==============>>>>> ^_^")
    #api = do_auth(conn)
    # g_api = do_auth_new()
    g_api = get_api(conn)
    logging.info("Got API OK!!! ==============>>>>> ^_^")
    if (True == fetch_store_followers(conn, uids)):
        logging.info("Store All Followers Successfully!!!")
        return True
    else:
        logging.error("Store All Followers Failed!!!")
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
        #print(opts)
        #print(args)
    except getopt.GetoptError:
        logging.error("Params are not defined well!")
        print_statistic(logging)
        sys.exit(1)

    logging.info("START")
    conn = MySQLdb.connect(host="localhost", user="root", passwd="RooT", db="spider", charset="utf8")
    fetch_followers_to_database(conn)
    conn.close()
    print_statistic(logging)
    logging.info("END")




if __name__ == "__main__":
    main()


