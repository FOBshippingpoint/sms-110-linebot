# -*- coding: utf-8 -*-

import urllib
import urllib2

username = 'test'
password = '1234'
mobile = '09xxxxxxxx'
message = '簡訊內容測試'
message = urllib.quote(message)

msg = 'username='+username+'&password=' + \
    password+'&mobile='+mobile+'&message='+message
url = 'http://api.twsms.com/json/sms_send.php?'+msg

resp = urllib2.urlopen(url)
print(resp.read())
