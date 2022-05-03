import requests
from urllib import parse


class TwsmsClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.send_url = 'http://api.twsms.com/json/sms_send.php'
        self.query_url = 'http://api.twsms.com/json/sms_query.php'

    def get_balance(self):
        params = {
            'username': self.username,
            'password': self.password,
            'checkpoint': 'Y'
        }
        r = requests.get(self.query_url, params=params)
        r = r.json()
        if r['code'] != '00000':
            raise Exception(r['code'])
        return r['point']

    def send_message(self, message, mobile):
        # url encode
        message = parse.quote_plus(message)
        params = {
            'username': self.username,
            'password': self.password,
            'mobile': mobile,
            'message': message
        }
        r = requests.get(self.send_url, params=params)
        return r.json()
