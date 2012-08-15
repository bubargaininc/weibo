from django.http import HttpResponse
from django.http import HttpRequest
import MySQLdb


def home(request):
	# client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri="http://68.45.60.44/callback")
	# url = client.get_authorize_url()
	return HttpResponse('<center><a href="'+ "sina.com" +'"><h1>weibo</h1></a></center>')

def fetch(request):
	# print request.GET.__getitem__(u'code')
	# if hasattr(request.GET, 'code'):
	print ("******************************************")
	code = str(request.GET.get('code'))
	print ("code = %s " % code)
	conn = MySQLdb.connect(host="localhost", user="root", passwd="RooT", db="spider", charset="utf8")
	cursor = conn.cursor()
	sql_clear = "delete from code where is_valid = 0;"
	sql_add = "insert into code (verifier, is_valid) value(%s, 1)"
	cursor.execute(sql_clear)
	n = cursor.execute(sql_add, code)
	print("n = %s" % n)
	cursor.close()
	conn.close()
	if (1 != n):
		print "ERROR!"
		return HttpResponse('<center><a href="'+ "sina.com" +'"><h1>ERROR!!!</h1></a></center>')
	return HttpResponse('<center><a href="'+ "sina.com" +'"><h1>Code Fetched!</h1></a></center>')

