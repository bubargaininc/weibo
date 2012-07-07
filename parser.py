#!/usr/bin/python

import re
import os
from bs4 import BeautifulSoup
import HTMLParser
import sys
import MySQLdb
import getopt

# to solve ansii encode problem
reload(sys)
sys.setdefaultencoding('utf-8')

g_person_number = 0
g_failed_counter = 0
g_failed_ids = []

def parseHTML(conn, file_name):
	global g_person_number, g_failed_counter, g_failed_ids
	
	# make the HTMLParser works for labels of chinese character
	HTMLParser.attrfind = re.compile(
	    ur'\s*([a-zA-Z_][-.:a-zA-Z_0-9]*)(\s*=\s*'
	    ur'(\'[^\']*\'|"[^"]*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~@\u4e00-\u9fa5]*))?')
	
	with open(file_name, 'r') as f:
		soup = BeautifulSoup(f)
		
	raw_user_info = soup('dd', 'person_info')
	for person in raw_user_info:
		g_person_number += 1
		print "[PARSE_HTML]: ======================-------===========>>>>>  processing person %d" % (g_person_number)
		if not parseOnePerson(conn, person):
			g_failed_counter += 1
			g_failed_ids.append(g_person_number)
			print "[PARSE_HTML] the %dth person failed" % (g_person_number)
		

def parseOnePerson(conn, raw):
	# process uid, screen_name, url, label begin with <a
	raw_user = raw.find('a')
	uid = raw_user.get('uid')
	if not uid:
		return False
	else:
		if checkExist(uid, conn):
			print "[PARSE_INFO]: =====>>>>> user %d already in database" % (g_person_number)
			return True

	screen_name = raw_user.get('title')
	if not screen_name:
		screen_name = "(screen_name not found)"
		
	url = raw_user.get('href')
	if not url:
		url = "(url not found)"
	
	# process gender, label begin with <img, title
	raw_gender = raw.find('img',title=True)
	gender = raw_gender.get('title')
	if not gender:
		gender = "N"
	
	#process description, label begin with <p, W_textb
	if raw.find('p','W_textb'):
		if raw.find('p','W_textb').get_text().strip() == '':
			description = ''
		else:
			description = raw.find('p','W_textb').get_text().strip().split(u"\uff1a")[1]
	else:
		description = ''
	
	#process location, label begin with <span addr
    # can also use u'\uff0c' for split
	location = raw.find('span','addr').get_text().strip().split(u'\uff0c')
	if not location:
		 province= "(province not found)"
	else:
		province = location[0]
	
	if len(location) == 2:
		city = location[1]
	else:
		city = '(city not found)'	
	
	# process career_info_head, label begin with <p, p_d
	if raw.find('p','p_d'):
		career_info_head = raw.find('p','p_d').get_text().strip()
	else:
		career_info_head = ''
	
	# process tags, education, career_info_tail, 
	# label begin with < p W_textb W_linkd_a
	info_list = raw.find_all('p','W_textb W_linkd_a')
		
	if '' == info_list[0].get_text().strip():
		tag_id_list = []
	else:
		tags = info_list[0].get_text().strip().split(u"\uff1a")[1].split(' ')
		tags = filter (lambda tag: tag != '...', tags)
		tag_id_list = checkTags(conn, tags)
	
	if '' == info_list[1].get_text().strip():
		education = ""
	else:
		education = info_list[1].get_text().strip().split(u"\uff1a")[1]
		
	if '' == info_list[2].get_text().strip():
		career_info_tail = ''
	else:
		career_info_tail = info_list[2].get_text().strip().split(u"\uff1a")[1]
	
	if career_info_head and career_info_tail:
		career_info = r" // ".join([career_info_head, career_info_tail])
	elif career_info_head:
		career_info = career_info_head
	elif career_info_tail:
		career_info = career_info_tail
	else:
		career_info = ''
	
	# store user data
	user_data = (uid, screen_name, gender, province, city, url, 
		career_info, education, description)
	user_id = checkUser(conn, user_data)
	
	#store user_tag_map
	if not tag_id_list or not user_id:
		print "[PARSE_WARNING]: no tags or user store failed"
	else:
		user_tag_map = [user_id, tag_id_list]
		if storeUserTagMap(user_tag_map, conn):
			print "[PARSE_HTML]: store all ok"
		else:
			print "[PARSE_HTML]: store failed"
	return True

def checkExist(uid, conn):
	sql = "select id from users where uid = %s"
	param = (uid)
	cursor = conn.cursor()
	n = cursor.execute(sql, param)
	if n == 1:
		print "[CHECK_EXIST]: user exist"
		cursor.close()
		return True
	else:
		cursor.close()
		return False
	

def storeUserTagMap(user_tag_map, conn):
	records = []
	cursor = conn.cursor()
	tags_num = len(user_tag_map[1])
	for tag_id in user_tag_map[1]:
		records.append((user_tag_map[0], tag_id))
	sql = "insert into user_tag_map (user_id, tag_id) values(%s, %s)"
	param = records
	n = cursor.executemany(sql, param)
	if n == tags_num:
		print "[STORE_TAG_USER_MAP]: store tag user map success"
		conn.commit()
		cursor.close()
		return True
	else:
		print "[STORE_TAG_USER_MAP]: store tag user map failed"
		cursor.close()
		return False
		
def checkUser(conn, user_data):
	sql = "select id from users where uid = %s"
	cursor = conn.cursor()
	param = (user_data[0])
	n = cursor.execute(sql, param)
	if 1 == n:
		print "[CHECK_USER]: already in the database"
		row = cursor.fetchone()
		user_id = row[0]
		cursor.close()
		return user_id
	else:
		print "[CHECK_USER]: this is a new user"
		user_id = storeUser(conn, user_data)
		cursor.close()
		return user_id
	
def storeUser(conn, user_data):
	sql = """insert into users (uid,nick_name,gender,province,city,url,career,
		education, description) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
	cursor = conn.cursor()
	param = user_data
	n = cursor.execute(sql, param)
	if n == 1:
		print "[STORE_USER]: store user success"
		user_id = conn.insert_id()
		conn.commit()
		cursor.close()
		return user_id
	else:
		print "[STORE_USER]: store user failed"
		cursor.close()
		conn.close()
		sys.exit(1)

def checkTags(conn, tag_list):
	tag_ids = []
	sql = "select id from tags where name = %s"
	cursor = conn.cursor()
	for tag in tag_list:
		param = (tag)
		n = cursor.execute(sql, param)
		if 1 == n:
			print "[CHECK_TAG]: already in the database"
			row = cursor.fetchone()
			tag_ids.append(row[0])
		else:
			print "[CHECK_TAG]: this is a new tag"
			tag_id = storeTags(conn, tag)
			tag_ids.append(tag_id)
	cursor.close()
	return tag_ids

def storeTags(conn, tag):			
	sql = "insert into tags (name) values(%s)"
	cursor = conn.cursor()
	param = (tag)
	n = cursor.execute(sql, param)
	if n == 1:
		tag_id = conn.insert_id()
		conn.commit()
		cursor.close()
		return tag_id
	else:
		print "[STORE_TAG]: store tag failed"
		cursor.close()
		conn.close()
		sys.exit(1)
			
#def storeToDB():
#	conn = MySQLdb.connect(host="ec2-204-236-172-73.us-west-1.compute.amazonaws.com", 
#			user="root", passwd="RooT", db="spider", charset="utf8")
#	parseHTML(conn, file_name)
#	conn.close()

if __name__ == "__main__":
        file_name = None
	try:
	    opts,args = getopt.getopt(sys.argv[1:],"f:")
	    for op,value in opts:
	      if op == "-f":
	        file_name = value
	except getopt.GetoptError:
	    print("[ERROR]: Params are not defined well!")
	    print "[INFO]: Stored " + str(g_person_number) + " New Person In Total!"
	    sys.exit(1)
	if (None == file_name):
	    print "[ERROR]: Please give the parsed file name and path."
	    print "[INFO]: Stored " + str(g_person_number) + " New Person In Total!"
	    sys.exit(1)
	
	conn = MySQLdb.connect(host="ec2-204-236-172-73.us-west-1.compute.amazonaws.com", user="root", passwd="RooT", db="spider", charset="utf8")
	parseHTML(conn, file_name)
	conn.close()
	
