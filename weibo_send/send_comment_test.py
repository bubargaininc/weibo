#!/usr/bin/python
#-*- coding=utf-8 -*-
import sys
import getopt 
import webbrowser
import MySQLdb
import time
import urllib
import weibo
import json
import httplib

APP_KEY = '3196917096'
APP_SECRET= 'a434c8f6aa1986ae0363b86065e5fce6'
CALLBACK_URL = 'http://www.bubargain.com/callback.php'
access_token ='2.00A1YbCDyKw2UDbfafb0f763K3GhyC'
mid = '3481616523610958'
COMMENT_ORI = 1


def send_comment():
    print "let's start!"
    client = weibo.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    print "1st sen ok!"
    client.set_access_token(access_token, 500000)
    print ""
    r= client.post.comments__create(comment=u'1  同时转发到我的微',id=mid)
    print r
    print "finish!"


if __name__ == "__main__":
    send_comment()