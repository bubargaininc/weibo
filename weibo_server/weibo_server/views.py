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
	print "1"
	cursor = conn.cursor()
	print "2"
	sql = "update code set verifier=%s, is_valid=1 where id=1"
	print ("sql = %s" % sql)
	param = code
	n = cursor.execute(sql, param)
	print("n = %s" % n)
	cursor.close()
	conn.close()
	if (1 != n):
		print "ERROR!"
		return HttpResponse('<center><a href="'+ "sina.com" +'"><h1>ERROR!!!</h1></a></center>')
	return HttpResponse('<center><a href="'+ "sina.com" +'"><h1>Code Fetched!</h1></a></center>')

