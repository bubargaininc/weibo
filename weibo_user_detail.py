#! /usr/bin/python
#coding=utf8
import urllib, urllib2
import cookielib
import base64
import re
import json
import hashlib
import os, time, getopt, sys
import MySQLdb


postdata = {
    'entry': 'weibo',
    'gateway': '1',
    'from': '',
    'savestate': '7',
    'userticket': '1',
    'ssosimplelogin': '1',
    'vsnf': '1',
    'vsnval': '',
    'su': '',
    'service': 'miniblog',
    'servertime': '',
    'nonce': '',
    'pwencode': 'wsse',
    'sp': '',
    'encoding': 'UTF-8',
    'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
    'returntype': 'META'
}



DEFAULT_FETCH_USERS_NUMBER      = 10
DEFAULT_WAITING_BASE		= 2
DEFAULT_PAGES_LOCATION		= "./user_pages"
DEFAULT_PATH_PARSER		= "./parser.py"
DEFAULT_COOKIE_FILE		= "./cookiesflyin.txt"
DEFAULT_WAITING_TIME_MAX	= 240 # 8 min
DEFAULT_USER_NAME		= "flyingjoe2010@gmail.com"
DEFAULT_PASSWORD		= "wonderful1989"



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

# global var
g_fetch_users_number    = DEFAULT_FETCH_USERS_NUMBER
g_waiting_base          = DEFAULT_WAITING_BASE
g_pages_location	= DEFAULT_PAGES_LOCATION
g_path_parser		= DEFAULT_PATH_PARSER
g_cookie_file		= DEFAULT_COOKIE_FILE
g_max_waiting_time	= DEFAULT_WAITING_TIME_MAX
g_mode                  = Mode.FROM_DB
g_stored_counter        = 0
g_name                  = ""
g_user			= DEFAULT_USER_NAME
g_pwd			= DEFAULT_PASSWORD
g_manually_pages	= []


def get_servertime():
    url = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=dW5kZWZpbmVk&client=ssologin.js(v1.3.22)&_=1335601819416'
    data = urllib2.urlopen(url).read()
    p = re.compile('\((.*)\)')
    try:
        json_data = p.search(data).group(1)
        data = json.loads(json_data)
        servertime = str(data['servertime'])
        nonce = data['nonce']
        return servertime, nonce
    except:
        print 'Get severtime error!'
        return None

def get_pwd(pwd, servertime, nonce):
    pwd1 = hashlib.sha1(pwd).hexdigest()
    pwd2 = hashlib.sha1(pwd1).hexdigest()
    pwd3_ = pwd2 + servertime + nonce
    pwd3 = hashlib.sha1(pwd3_).hexdigest()
    return pwd3

def get_user(username):
    username_ = urllib.quote(username)
    username = base64.encodestring(username_)[:-1]
    return username


def login():
    global postdata
    #username = 'flyingjoe2010@gmail.com'
    #pwd = 'wonderful1989'
    username = g_user
    pwd = g_pwd
    url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.3.22)'
    cookiefile = g_cookie_file
    cookies = cookielib.LWPCookieJar(cookiefile)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies), urllib2.HTTPHandler)
    urllib2.install_opener(opener)
    try:
        servertime, nonce = get_servertime()
    except:
        print "ERROR [LOGIN]: get servertime and nonce FAILED!"
        return
    postdata['servertime'] = servertime
    postdata['nonce'] = nonce
    postdata['su'] = get_user(username)
    postdata['sp'] = get_pwd(pwd, servertime, nonce)
    postdata = urllib.urlencode(postdata)
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:9.0.1) Gecko/20100101 Firefox/9.0.1'}
    req  = urllib2.Request(
        url = url,
        data = postdata,
        headers = headers
    )
    result = urllib2.urlopen(req)
    text = result.read()
    print "INFO [LOGIN]: login result: " + text
    p = re.compile('location\.replace\(\'(.*?)\'\)')
    try:
        login_url = p.search(text).group(1)
        print "INFO [LOGIN]: login_url = " + login_url
        openresult = urllib2.urlopen(login_url)
        opentxt =openresult.read()
        print "INFO [LOGIN]: opentext = " + opentxt
        cookies.save(cookiefile)
        print "Login Successful!"
        return True
    except:
        print 'Login error!'
        return False




def get_one_user_detail_page(user):
    logging = Logging.get_logger('get_one_user_detail_page')
    try:
        waiting_counter = 0
        #searchUrl = 'http://s.weibo.com/user/&keytime=1336285139672&nickname=%s&Refer=User_mid'% (user.encode('utf-8'))
        searchUrl = 'http://s.weibo.com/user/&keytime=1336439152946&nickname=%s&region=custom:11:1000&Refer=User_mid'% (user.encode('utf-8'))
        #logging.info("searchUrl is: " + searchUrl)
        while (True):
            content =urllib2.urlopen(searchUrl).read()
            if not '你搜索的太頻繁了'  and not '抱歉，没有找到相关的结果' in content:
                f = open(os.path.join(g_pages_location, user), 'w')
                f.write(content)
                f.close()
                logging.info("User " + user + " detail page has been written into file.")
                return True
            else:
                logging.warning("Access server too many times, we need to wait for a while!")
                logging.info("waiting_counter = %s" % waiting_counter)
                logging.info("waiting_base = %s" % g_waiting_base)
                logging.info("waiting_base**waiting_counter = %s" % g_waiting_base**waiting_counter)
                waiting_period = int(g_waiting_base)**waiting_counter*60
                if (waiting_period > g_max_waiting_time):
                    logging.info("Reached Maxmum Waiting Time! Roll Back!!")
                    return False
                logging.info("Start to wait for " + str(waiting_period) + " seconds!")
                time.sleep(waiting_period)
                waiting_counter += 1
    except Exception:
        logging.error("Error Occured When fetch user: %s details!" % user)




def get_user_detail_pages(user_list):
    logging = Logging.get_logger('get_user_detail_pages')
    get_page_number = 0
    process_detail_page_counter = 0
    cookiejar = cookielib.LWPCookieJar(g_cookie_file)
    cookiejar.load(g_cookie_file)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar), urllib2.HTTPHandler)
    urllib2.install_opener(opener)
    content = urllib2.urlopen('http://www.weibo.com/').read()
    #logging.info(content)
    p = re.compile('location\.replace\(\'(.*?)\'\)')
    try:
        login_url = p.search(content).group(1)
        #logging.info("login_url = %s" % login_url)
        opentxt = urllib2.urlopen(login_url).read()
        for user in user_list:
            process_detail_page_counter += 1
            logging.info("-----=======================-------==============================--->>>> Current --> %s user: %s" % (str(process_detail_page_counter), user[0]))
            if (True == get_one_user_detail_page(user[0])):
                logging.info("Get user: " + user[0] + " detail page OK!")
                get_page_number += 1
            else:
                logging.error("Get user: " + user[0] + " detail page FAILED!")
                break
    except Exception:
        logging.error("Error Occured!")
    return get_page_number
            

def get_user_details(user_list):
    logging = Logging.get_logger('get_user_details')
    if (len(user_list) == 0):
        logging.error("There is no users in the list!")
        return False
    get_page_number = get_user_detail_pages(user_list)
    waiting_counter = 0
    while (0 == get_page_number):
        logging.warning(str(waiting_counter+1) + " Times Fetch <<<>>> * 0 * <<<>>> page!!! Please Check the Network or The fetch times so far!")
        waiting_period = (g_waiting_base**waiting_counter) * 60
        time.sleep(waiting_period)
        waiting_counter += 1
        get_page_number = get_user_detail_pages(user_list)
    else:
        if (len(user_list) == g_fetch_users_number):
            logging.info("Fetch users detail OK! Fetch All!")
        else:
            logging.warning("NOT Fetch All of users, only %s out of %s" % (str(len(user_list)), str(g_fetch_users_number)))
        return True

def check_parsing_env():
    logging = Logging.get_logger('check_parsing_env')
    if (os.path.exists(g_pages_location) == True and os.path.isfile(g_path_parser) == True):
        logging.info("Parser and pages are ready!")
        return True
    else:
        logging.error("Missing parser or pages!")
        return False

def is_exist(conn, user):
    logging = Logging.get_logger('is_exist')
    cursor = conn.cursor()
    sql = "select id from users where nick_name = %s"
    param = user
    n = cursor.execute(sql, param)
    if (1 == n):
        logging.info("The user is existing in users table!!")
        cursor.close()
        return True
    elif (0 == n):
        logging.info("The user is NOT existing in users table!!")
        cursor.close()
        return False
    else:
        logging.error("Error Occured when check user existing!!")
        cursor.close()
        return False


def clean_temp_users(conn, users):
    global g_stored_counter
    logging = Logging.get_logger('clean_temp_users')
    if (len(users) == 0):
        logging.error("There is no users in the list!!")
        return False
    #logging.info(str(users))
    for u in users:
        logging.info(u)
    cursor = conn.cursor()
    sql = "delete from temp_users where nick_name = %s"
    params = users
    n = cursor.executemany(sql, params)
    if (len(users) == n):
        logging.info("Cleaned all users!")
        g_stored_counter += n
        return True
    elif (len(users) > n):
        logging.warning("Cleaned " + str(n) + " users out of " + str(len(users)))
        g_stored_counter += n
        return False
    else:
        logging.error("Error Occured When cleaning users!")
        return False


def parse_store_user_details(conn):
    global g_manually_pages
    logging = Logging.get_logger('parse_store_user_details')
    process_user_counter = 0
    if (False == check_parsing_env()):
        logging.error("The environment for parsing pages is not OK! Please check the parser and the pages!")
        sys.exit(1) 
    else:
        page_list = os.listdir(g_pages_location)
        pages_done = []
        for page in page_list: # page name is user name
           process_user_counter += 1
           logging.info("====-=======-============-========--======----===--->>>>> To process --> %s: user: %s" % (str(process_user_counter), page))
           parse_user_page = g_path_parser + " -f " + str(os.path.join(g_pages_location, str(page)))
           logging.info("Start to do parsing with command: parser_user_page: " + parse_user_page)
           os.system(parse_user_page)
           logging.info("Parsing Done... To check if it exists or not...")
           if (True == is_exist(conn, page)):
               logging.info("The user " + page + " has been parsed and stored into db!")
               pages_done.append(page)
               os.remove(str(os.path.join(g_pages_location, str(page))))
               if (False == os.path.isfile(str(os.path.join(g_pages_location, page)))):
                   logging.info("Remove the detail page of user: %s OK!!" % page)
               else:
                   logging.warning("Remove the detail page of user: %s FAILED!! Need to remove it manully!" % page)
           else:
               #logging.error("The user " + page + " storing FAILED!!!")
               logging.warning("Cannot find the user: " + page + " in database, Please Check: the nickname has been changed; the user has been deleted.")
               logging.info("Keeping the page file for user: " + page + "; Need process this user manually!!")
               g_manually_pages.append(page)
               #if (True == clean_temp_users(conn, pages_done)):
               #    logging.info("Only storing " + str(len(pages_done)) + " users: " + str(pages_done))
               #    logging.info("Cleaned these temp Users!!")
               #else:
               #    logging.error("Clean temp users ERROR!")
               #return False
        logging.info("Done with all of pages! Total user number: %s" % len(pages_done))
        if (True == clean_temp_users(conn, pages_done)):
            logging.info("Cleaned these temp Users!!")
            return True
        else:
            logging.error("Clean temp users ERROR!")
            return False

def fetch_temp_users(conn):
    global g_fetch_users_number
    logging = Logging.get_logger('fetch_temp_users')
    if (Mode.FROM_DB == g_mode):
        cursor = conn.cursor()
        logging.info("DB MODE!!! ")
        sql = "select nick_name from temp_users limit %s"
        param = int(g_fetch_users_number)
    elif (Mode.FROM_NAME == g_mode):
        logging.info("NAME MODE!!! ")
        logging.info("Process user: %s" % g_name)
        g_fetch_users_number = 1
        return [(g_name,),]
    else:
        logging.error("Error Mode!! Mode: " + str(g_mode))
        return False
    n = cursor.execute(sql, param)
    if (Mode.FROM_DB == g_mode and g_fetch_users_number == n):
        logging.info("Fetch %d users Successfully" % n)
        users = cursor.fetchall()
        cursor.close()
        logging.info("Going To Process Users: " + str(users))
        return users
    elif (Mode.FROM_DB == g_mode and n > 0):
        logging.warning("There is less than %d users, Fetched %d users Successfully" % (g_fetch_users_number, n))
        users = cursor.fetchall()
        cursor.close()
        return users
    elif (0 == n):
        logging.warning("NO SUCH USER in temp_users!")
        cursor.close()
        return False
    else:
        logging.error("Database Operation ERROR!! n = %d" % n)
        cursor.close()
        return False


def get_temp_users_detail_into_db(conn):
    logging = Logging.get_logger('get_detail_into_db')
    fetch_users_result = fetch_temp_users(conn)
    if (False == fetch_users_result):
        logging.error("Fetch temp users FAILED!!")
        return False
    else:
        logging.info("Fetch temp users OK!!!")
        if (False == get_user_details(fetch_users_result)):
            logging.error("Get User details page FAILED!!")
            return False
        else:
            logging.info("Get User details page OK!")
            if (False == parse_store_user_details(conn)):
                logging.error("Parse Store user details into db FAILED!!")
                return False
            else:
                logging.info("Parse Store user details OK!")
                return True


def is_env_ready():
    logging = Logging.get_logger('is_env_ready')
    if (os.path.exists(g_pages_location) == True):
        logging.info("User details Location is ready!")
    else:
        logging.info("No User details Location, Creating: %s" % g_pages_location)
        os.mkdir(g_pages_location)
        logging.info("User details Location is Ready!")
    if (os.path.isfile(g_path_parser) == True):
        logging.info("Parser is ready!")
    else:
        logging.error("Parser is NOT Ready!")
        return False
    if (os.path.isfile(g_cookie_file) == True):
        logging.info("Cookie file is ready!")
        return True
    else:
        logging.error("Cookie file is NOT Ready!")
        return False



def main():
    global g_fetch_users_number, g_mode, g_name, g_waiting_base, g_pages_location, g_path_parser, g_cookie_file, g_max_waiting_time, g_user, g_pwd
    logging = Logging.get_logger('main')
    try:
        opts,args = getopt.getopt(sys.argv[1:],"u:n:w:d:c:t:p:a:b:l:")
        for op,value in opts:
            if op == "-u":
                g_fetch_users_number = int(value)
            elif op == "-n":
                g_name = str(value)
                logging.info(g_name)
                g_mode = Mode.FROM_NAME
            elif op == "-w":
                g_waiting_base = int(value)
            elif op == "-d":
                if (False == os.path.exists(value)):
                    logging.error("The location you input is not existing!")
                    logging.info("Creating ... %s" % value)
                    os.mkdir(str(value))
                    if (False == os.path.exists(value)):
                        logging.error("Creating FAILED!!")
                        sys.exit(1)
                    else:
                        logging.info("Created!")
                        g_pages_location = str(value)
                else:
                    g_pages_location = str(value)
            elif op == "-c":
                if (False == os.path.isfile(value)):
                    logging.error("The cookie file is not existing!")
                    sys.exit(1);
                else:
                    g_cookie_file = str(value)
            elif op == "-t":
                g_max_waiting_time = int(value)
            elif op == "-p":
                if (False == os.path.isfile(value)):
                    logging.error("The parser is not existing!")
                else:
                    g_path_parser = value
            elif op == "-a":
                g_user = str(value)
            elif op == "-b":
                g_pwd = str(value)
            elif op == "-l":
                login()
        print(opts)
        print(args)
    except getopt.GetoptError:
        logging.error("Params are not defined well!")
        logging.info("Stored " + str(g_stored_counter) + " New Person In Total!")
        sys.exit(1)

    
    logging.info("========------------>>> ENV CHECK <<<-----------==========")
    if (True == is_env_ready()):
        logging.info("========------------>>> ENV CHECK DONE <<<-----------==========")
        logging.info("ENV is ready!!")
        logging.info("START")
        conn = MySQLdb.connect(host="ec2-204-236-172-73.us-west-1.compute.amazonaws.com", user="root", passwd="RooT", db="spider", charset="utf8")
        get_temp_users_detail_into_db(conn)
        conn.close()
        logging.info("Processed " + str(g_stored_counter) + " Temp Users In Total!")
        logging.info("Users need to be processed manually: ")
        for u in g_manually_pages:
            logging.info(u)
        logging.info("END")
    else:
        logging.info("========------------>>> ENV CHECK DONE <<<-----------==========")
        logging.error("ENV is not ready!! Please Check the parser, cookie file and user detail pages location...")

if __name__ == "__main__":
    main()

