mport sys
import getopt 
import webbrowser
import MySQLdb
import time
import weibo
import urllib2



APP_KEY                    = 3983759328
APP_SECRET                 = """36d1bd885bb6553c201b50fc9912b756"""
CALLBACK_URL               = "http://www.uhquan.com:8888/callback.php"

def do_auth():
	logging = logging.get_logger('do_auth')
	client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
	code = raw_input ('input code you got:')
	r = client.request_access_token(code)
	access_token = r.access_token
	logging.info(access_token)
	expires_in = r.expires_in
	client.set_access_token(access_token,expires_in)
	print client.get.account__rate_limit_status()



if __name__ == "__main__":
	do_auth()
