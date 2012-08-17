#!/usr/bin/python
#coding:utf-8
import os
import sys
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
	logging = Logging.get_logger('do_auth')
	client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
	code = raw_input ('input code you got:')
	r = client.request_access_token(code)
	access_token = r.access_token
	logging.info(access_token)
	expires_in = r.expires_in
	client.set_access_token(access_token,expires_in)
	print client.get.account__rate_limit_status()

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


if __name__ == "__main__":
	do_auth()
