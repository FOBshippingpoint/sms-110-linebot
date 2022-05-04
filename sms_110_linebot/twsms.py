import requests
from urllib import parse

CODE = {
    "00000": "完成",
    "00001": "狀態尚未回復",
    "00010": "帳號或密碼格式錯誤",
    "00011": "帳號錯誤",
    "00012": "密碼錯誤",
    "00020": "通數不足",
    "00030": "IP 無使用權限",
    "00031": "限制發送國際門號",
    "00040": "帳號已停用",
    "00041": "API 未啟用(請登入平台後至帳號設定內的 API 設定中啟用)",
    "00050": "sendtime 格式錯誤",
    "00060": "expirytime 格式錯誤",
    "00100": "手機號碼格式錯誤",
    "00110": "沒有簡訊內容",
    "00120": "長簡訊不支援國際門號",
    "00130": "簡訊內容超過長度",
    "00140": "drurl 格式錯誤",
    "00150": "sendtime 預約的時間已經超過",
    "00170": "drurl 帶入的網址無法連線(http code 必須為 200)",
    "00180": "簡訊內容帶有 Emoji 圖形",
    "00300": "找不到 msgid",
    "00310": "預約尚未送出",
    "00400": "找不到 snumber 辨識碼",
    "00410": "沒有任何 mo 資料",
    "00420": "smsQuery 指定查詢的格式錯誤",
    "00430": "moQuery 指定查詢的格式錯誤",
    "99998": "資料處理異常，請重新發送",
    "99999": "系統錯誤，請通知系統廠商",
}


class TwsmsClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.send_url = 'http://api.twsms.com/json/sms_send.php'
        self.query_url = 'http://api.twsms.com/json/sms_query.php'

    def set_account(self, username, password):
        self.username = username
        self.password = password

    def get_balance(self):
        params = {
            'username': self.username,
            'password': self.password,
            'checkpoint': 'Y'
        }
        r = requests.get(self.query_url, params=params)
        r = r.json()
        if r['code'] == '00000':
            return int(r['point'])
        else:
            return self.__code_to_message(r['code'])

    def send_message(self, message, mobile):
        # url encoding
        message = parse.quote_plus(message)
        params = {
            'username': self.username,
            'password': self.password,
            'mobile': mobile,
            'message': message
        }
        r = requests.post(self.send_url, params=params)
        r = r.json()
        return self.__code_to_message(r['code'])

    def __code_to_message(self, code):
        if code == '00000':
            return
        elif code in {'00011', '00012'}:
            return '帳號或密碼錯誤'
        elif code == '00020':
            return '點數不足'
        elif code == '00041':
            return 'API未啟用'
        else:
            raise Exception(CODE[code])
