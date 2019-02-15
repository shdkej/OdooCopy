# -*- coding: utf-8 -*-
from urllib2 import Request, urlopen
from urllib import urlencode, quote_plus
from datetime import datetime

def _parse_holiday():
        url = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo'
        #url = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getHoliDeInfo'
	apiKey = 'j2DHSm20GZ4MePk9FTTUwxHfq7DcShJcARMRP6pvlWbw1pxUBkQPCxp8LAFmgl4uGJq%2Fk%2F8ueK8zt2GOv9QS8g%3D%3D'
	str_tmp = ''
	solYear = str(datetime.today().year)

	for i in range(1,13):
	  if i<10:
	    i = '0'+str(i)
	  solMonth = str(i)
	  query = '?'+'ServiceKey='+apiKey+'&solYear='+solYear+'&solMonth='+solMonth
	  print query

	  request = Request(url + query)
	  request.get_method = lambda: 'GET'
	  response = urlopen(request).read()
	  str_tmp += (response + '\n')

	filename = '/usr/lib/python2.7/dist-packages/odoo/addons/gvm/test_'+solYear+'.xml'
	with open(filename, 'w') as f:
	  f.write(str_tmp)

def isHoliday(date):

	state = False
	filename = '/usr/lib/python2.7/dist-packages/odoo/addons/gvm/test_2018.xml'
	f = open(filename)
	info = f.read()
	holiday = []

	split_s = info.split('<locdate>')
	for s in split_s:
	  holiday.append(s[0:8])

	if date in holiday:
	  state = True
	  print state

	print holiday

	return state



if __name__ == '__main__':
  _parse_holiday()
  isHoliday("20190101")
