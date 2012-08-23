#! /usr/bin/python
#coding:utf-8
from selenium import selenium
import unittest, time, re

class weibo_send(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://weibo.com/")
        self.selenium.start()
    
    def test_weibo_send(self):
        sel = self.selenium
        sel.open("/u/1655012125?wvr=3.6&lf=reg")
        sel.click(u"css=textarea[title=\"微博输入框\"]")
        sel.type(u"css=textarea[title=\"微博输入框\"]", "test2")
        sel.click("//div[@id='pl_content_publisherTop']/div/div[5]/a")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
