#!/usr/bin/python
import os
import getopt
import sys

def traverseDir(dir_name, parser):
	city_dir_list = []
	province_dir_list = os.listdir(dir_name)
	print province_dir_list
	for d in province_dir_list:
		city_dir_list.append(os.path.join(dir_name, d))
		print city_dir_list
	for city in city_dir_list:
		for index in range(1,51):
		    file_name = parser + " -f " + str(os.path.join(city,str(index)+".txt"))
		    print file_name
		    os.system(file_name)

def main():
	dir_name = None
	parser = None
	try:
	    opts,args = getopt.getopt(sys.argv[1:],"d:p:")
	    for op,value in opts:
			if op == "-d":
				dir_name = value
			elif op == "-p":
				parser = value
	except getopt.GetoptError:
	    print("[ERROR]: Params are not defined well!")
	    print "[INFO]: Stored "  + " New Person In Total!"
	    sys.exit(1)
	if (None == dir_name or None == parser):
	    print "[ERROR]: Please give the parsed file name and path."
	    print "[INFO]: Stored " + " New Person In Total!"
	    sys.exit(1)

	traverseDir(dir_name, parser)

if __name__ == "__main__":
    main()

