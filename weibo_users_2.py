#!/usr/bin/python
#-*- coding=utf-8 -*-

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

APP_KEY                    = 1145738428
APP_SECRET                 = """275b151558a7007b0c8dab0060588f42"""
CALLBACK_URL               = "http://76.116.64.145:8888/callback"

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
    # u = client.get.statuses__friends_timeline(count=1)
    # print u
    # print u.total_number
    # print u.statuses
    # print u.statuses[0].user.id
    # print u.statuses[0].user.screen_name
    if not client.is_expires():
        try:
            uid = client.get.account__get_uid().uid
        except weibo.APIError as apierr:
            logging.error(str(apierr))
            logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
            sys.exit(1)
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
            sys.exit(1)
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
    # auth = OAuthHandler(APP_KEY, APP_SECRET, BACK_URL)
    # auth_url = auth.get_authorization_url()
    # request_token_key = auth.request_token.key
    # request_token_secret = auth.request_token.secret
    # auth.set_request_token(request_token_key, request_token_secret)
    # webbrowser.open(auth_url)
    # verifier = input("Verifier: ").strip()
    # access_token = auth.get_access_token(verifier)
    # ATK = access_token.key
    # ATS = access_token.secret
    # auth.setAccessToken(ATK, ATS)
    # api = API(auth)
    # user = api.verify_credentials()
    # logging("[AUTH]: We are uing API from account: [uid = %s, name = %s]" % (user.id, user.screen_name))
    # return api



def fetch_one_user_bilaterals(api, _uid):
    logging = Logging.get_logger('fetch_one_user_bilaterals')
    all_bilaterals = []
    page_number = 1
    #logging.info("count = %s" % g_one_page_count)
    #logging.info("page = %s" % page_number)
    if not api.is_expires():
        try:
            bilaterals = api.friendships__friends__bilateral(uid=_uid, count=g_one_page_count, page=page_number)
        except weibo.APIError as apierr:
            logging.error(str(apierr))
            logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
            sys.exit(1)
        except urllib2.HTTPError as httperr:
            logging.error(str(httperr))
            logging.error(str(httperr.read()))
            logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
            sys.exit(1)

    bilaterals_number = len(bilaterals.users)
    logging.info("Get %d bilaterals this time." % bilaterals_number)
    all_bilaterals.extend(get_bilaterals_data(bilaterals, bilaterals_number))
    while (bilaterals_number > 0):
        page_number += 1
        if not api.is_expires():
            try:
                bilaterals = api.friendships__friends__bilateral(uid=_uid, count=g_one_page_count, page=page_number)
            except weibo.APIError as apierr:
                logging.error(str(apierr))
            except urllib2.HTTPError as httperr:
                logging.error(str(httperr))
                logging.error(str(httperr.read()))
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


def get_bilaterals_data(bilaterals, number):
    logging = Logging.get_logger('get_bilaterals_data')
    data = []
    for index in range(0, number):
        #logging.info("province = %s" % bilaterals.users[index]['province'])
        if (bilaterals.users[index]['province'] == str(g_city_code)):
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
            #logging.info("uid = %s    name = %s   description = %s  url = %s  gender = %s  province=%s  city=%s" % (uid, name,description,url,gender,province,city))
            data.append((uid, name, gender, province, city, url, description))
            #logging.info(data)
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
    sql = "insert into users (uid, nick_name, gender, province, city, url, description) values(%s,%s,%s,%s,%s,%s,%s)"
    logging.info("Storing ...")
    for b in bilaterals:
        #logging.info("one of them b: " + str(b))
        if (not is_exist(conn, b[0])):
            #logging.info("This is a new user!!!")
            param = b
            logging.info(str(param))
            logging.info(param[6])
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



def fetch_users(conn):
    logging = Logging.get_logger('fetch_users')
    if (Mode.FROM_DB == g_mode):
        logging.info("DB MODE!!! ")
        sql = "select uid from users where extended='F' limit %s"
        param = int(g_fetch_users_number)
    elif (Mode.FROM_NAME == g_mode):
        return [(g_name,)]
        #logging.info("[FETCH_USERS_NAME]: NAME MODE!!! ")
        #sql = "select uid from users where nick_name = %s"
        #param = g_name
    else:
        logging.info("MODE IS NOT EXIST!!! ====================<><><><><><><><><><>==================== ")
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
        

def fetch_store_one_user_bilaterals(conn, api, uid):
    logging = Logging.get_logger('fetch_store_one_user_bilaterals')
    fetch_result = fetch_one_user_bilaterals(api, uid)
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


