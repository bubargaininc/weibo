#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2012-9-15
use to provide applications a useful token 
@author: Daniel Ma
'''

import MySQLdb


class weibo_token:
    
    
    def __init__(self,hostAdd='192.168.1.104',user='root',passwd='RooT',db='spider'):
        self.hostAdd=hostAdd
        self.user=user
        self.passwd=passwd
        self.db=db
       
    '''
        acqurie an access_token
    '''
    def get(self,appName,num):
        conn = MySQLdb.Connect(host=self.hostAdd,user=self.user,passwd=self.passwd,db=self.db)
        sql = "select * from tokens where is_valid='T' and appkey = %s limit %s,1"
        cursor = conn.cursor()
        cursor.execute(sql,(appName,num))
        cds= cursor.fetchall()
        print cds
        cursor.close()
        conn.close()

    '''
        return how many access_token we can use
    '''
    
    def getTotalNum(self,appName):
        conn = MySQLdb.Connect(host=self.hostAdd,user=self.user,passwd=self.passwd,db=self.db)
        sql="select count(*) from tokens where is_valid='T' and appkey =%s"
        cursor = conn.cursor()
        try:
            cursor.execute(sql,(appName,))
            cds = cursor.fetchall()
            return cds[0][0]
        except:
            return 0    
        cursor.close()
        conn.close()
    
    '''
        set certain access_token valid or not
    '''
    def setTokenValid(self,token,valid='N'):
        conn = MySQLdb.Connect(host=self.hostAdd,user=self.user,passwd=self.passwd,db=self.db)
        sql="update tokens set is_valid=%s where token =%s"
        cursor = conn.cursor()
        try:
            n=cursor.execute(sql,(valid,token))
            return n
        except:
            return False    
        cursor.close()
        conn.close()    
    
#p=weibo_token()
#print p.getTotalNum('qiming')

