#! /usr/bin/python
#coding:utf-8
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re

class WeiboSend2(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://weibo.com/"
        self.verificationErrors = []
    
    def test_weibo_send2(self):
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.find_element_by_css_selector("body").click()
        driver.find_element_by_name("loginname").click()
        driver.find_element_by_name("loginname").clear()
        driver.find_element_by_name("loginname").send_keys("marine_ma@yahoo.cn")
        driver.find_element_by_xpath("//div[@id='login_form']/div/div/div[2]").click()
        driver.find_element_by_name("password").click()
        driver.find_element_by_name("password").clear()
        driver.find_element_by_name("password").send_keys("tju129")
        driver.find_element_by_link_text("登录").click()
        driver.find_element_by_css_selector("textarea[title=\"微博输入框\"]").clear()
        driver.find_element_by_css_selector("textarea[title=\"微博输入框\"]").send_keys("test3")
        driver.find_element_by_xpath("//div[@id='pl_content_publisherTop']/div/div[5]/a").click()
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
