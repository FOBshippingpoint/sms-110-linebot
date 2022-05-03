from flask import Flask, request, abort

from urllib import parse
import time
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import *
import os

# mine
import db
import message
from twsms import TwsmsClient
from sms_num_crawler import get_numbers
from config import Config
import tempfile

app = Flask(__name__)

config = Config()
line_bot_api = config.line_bot_api
handler = config.handler
imgur = config.imgur


static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# function for create tmp dir for download content


def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        pass


make_static_tmp_dir()


sessions = {}
db.init()
numbers = db.find_numbers()
if not numbers:
    numbers = get_numbers()
    db.insert_numbers(numbers)
numbers = dict(numbers)
CAR_TYPES = ['汽車', '機車', '汽機車', '大型車', '自行車']
CAR_NUMS = ['單輛', '多輛']
SITUATIONS = ['於紅線違規停車', '長時間佔用黃線停車', '違規併排停車', '於交岔路口處違規停車', '於黃網狀線違規停車', '於槽化線違規停車', '於卸貨格違規停車', '於人行道違規停車', '於騎樓違規停車',
              '於騎樓綠色標線違規停車', '於行人穿越道違規停車', '未緊靠右側停車', '未順向停車', '於公車站牌十公尺內停車', '於消防栓五公尺內停車', '佔用機車停車格違規停車', '佔用汽車停車格違規停車', '佔用公車停靠區違規停車', '佔用身障停車格違規停車']
MAX_BUTTON_NUM = 13


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(
        text=f'你好啊！{event.source.user_id}'))
    user_id = event.source.user_id

    line_bot_api.reply_message(event.reply_token, TextSendMessage(
        text=f'請輸入您的台灣簡訊帳號：'))


@ handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text

    if user_id not in sessions:
        user = db.find_user_by_user_id(user_id)
        sessions[user_id] = {
            'username': user[1] if user is not None else None,
            'password': user[2] if user is not None else None,
            'action': '',
            'user': user,
        }
        if user is not None:
            sessions[user_id]['twsms_client'] = TwsmsClient(user[1], user[2])
    user_session = sessions[user_id]

    if user_session['action'].startswith('input'):
        if user_session['action'] == 'input.username':
            user_session['username'] = text
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text=f'請輸入您的台灣簡訊密碼：'))
            user_session['action'] = 'input.password'
        elif user_session['action'] == 'input.password':
            user_session['password'] = text
            msg = FlexSendMessage(alt_text='請確認您的帳號密碼是否正確？', contents=message.create_confirm_twsms_info_context(
                username=user_session['username'], password=user_session['password']))
            line_bot_api.reply_message(event.reply_token, msg)
        return

    if text == '輸入帳密':  # 沒帳號or密碼
        if sessions[user_id]['username'] is not None and sessions[user_id]['password'] is not None:
            msg = TextSendMessage(text='帳號密碼已經存在',
                                  quick_reply=QuickReply(items=[
                                      QuickReplyButton(
                                          action=PostbackAction(label='重新設定帳號密碼', data='event=reset_twsms')),
                                  ]))
            line_bot_api.reply_message(event.reply_token, msg)
            return

        sessions[user_id]['action'] = 'input.username'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='請輸入您的台灣簡訊帳號：'))
        return

    if text == '報案':
        user_session['action'] = 'report.address'
        msg = TextSendMessage(text='請用手機按下方的"傳送我的所在位置"按鈕',
                              quick_reply=QuickReply(items=[
                                  QuickReplyButton(
                                      action=LocationAction(label="傳送我的所在位置"))
                              ]))
        line_bot_api.reply_message(event.reply_token, msg)
        return

    if text == '取消':
        user_session['action'] = ''
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text='已取消'))
        return

    if text == '查詢餘額':
        if user_session['twsms_client'] is not None:
            twsms = user_session['twsms_client']
            try:
                balance = twsms.get_balance()
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=f'您還剩下{balance}點'))
            except Exception as e:
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=f'查詢餘額時發生錯誤，請稍後再試'))
            return
        # twsms not set

    if text == '重設帳密':
        db.delete_user_by_user_id(user_id)
        user_session['username'] = None
        user_session['password'] = None
        user_session['twsms_client'] = None
        user_session['action'] = 'input.username'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='請輸入您的台灣簡訊帳號：'))

    # 報案過程
    if user_session['action'].startswith('report'):
        # 車種
        if user_session['action'] == 'report.car_type':
            if text in CAR_TYPES:
                user_session['report']['car_type'] = text
                user_session['action'] = 'report.car_num'
                items = [QuickReplyButton(action=MessageAction(
                    label=t, text=t)) for t in CAR_NUMS]
                msg = TextSendMessage(
                    text='請輸入單輛或多輛：', quick_reply=QuickReply(items=items))
                line_bot_api.reply_message(event.reply_token, msg)
                return
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text='請輸入以下車種：\n' + '\n'.join(CAR_TYPES) + '或輸入"取消"'))
        # 單輛/多輛
        elif user_session['action'] == 'report.car_num':
            if text in CAR_NUMS:
                user_session['report']['car_num'] = text
                user_session['action'] = 'report.license_plates'
                msg = TextSendMessage(text='請輸入"以空白分隔的車牌號碼"或輸入"跳過"：', quick_reply=QuickReply(
                    items=[QuickReplyButton(action=MessageAction(label='跳過', text='跳過'))]))
                line_bot_api.reply_message(event.reply_token, msg)

                # items = [QuickReplyButton(action=MessageAction(
                #     label=t, text=t)) for t in SITUATIONS]

                # line_bot_api.reply_message(event.reply_token, TextSendMessage(
                #     text='請輸入違規情形：', quick_reply=QuickReply(items=items)))
                return
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text='請輸入以下車種：\n' + '\n'.join(CAR_NUMS) + '或輸入"取消"'))
        # 車牌號碼
        elif user_session['action'] == 'report.license_plates':
            if text == '跳過':
                user_session['action'] = 'report.situation'

                page_num = 1
                sliced = SITUATIONS[(page_num-1) * (MAX_BUTTON_NUM-1):page_num * (MAX_BUTTON_NUM-1)]
                items = [QuickReplyButton(action=MessageAction(
                    label=t, text=t)) for t in sliced]
                items.insert(0, QuickReplyButton(action=PostbackAction(
                    label='更多', data='event=change_page&page_num='+str(page_num+1))))
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text='請輸入違規情形：', quick_reply=QuickReply(items=items)))
                return
            license_plates = text.split(' ')
            # todo validate license plates?
            user_session['report']['license_plates'] = license_plates
            items = [QuickReplyButton(action=MessageAction(
                label=t, text=t)) for t in SITUATIONS]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text='請輸入違規情形：', quick_reply=QuickReply(items=items)))
            # 違規情形
        elif user_session['action'] == 'report.situation':
            if text in SITUATIONS:
                user_session['report']['situation'] = text
                user_session['action'] = 'report.image'

                msg = TextSendMessage(text='請上傳照片或輸入"跳過"：', quick_reply=QuickReply(
                    items=[QuickReplyButton(action=MessageAction(label='跳過', text='跳過'))]))
                line_bot_api.reply_message(event.reply_token, msg)
                return
            # line_bot_api.reply_message(event.reply_token, TextSendMessage(
            #     text='請輸入以下違規情形：\n' + '\n'.join(SITUATIONS) + '或輸入"取消"'))
        elif user_session['action'] == 'report.image':
            if text == '跳過':
                user_session['action'] = 'report.preview'
                # generate message
                report = user_session['report']
                sms_msg = report['address'] + '有'
                if report['car_num'] != '單輛':
                    sms_msg += '多輛'
                sms_msg += report['car_type']
                sms_msg += report['situation']
                if report['license_plates']:
                    sms_msg += '，車牌號碼' + '、'.join(report['license_plates'])
                report['sms_msg'] = sms_msg

                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='簡訊內容：\n' + sms_msg + f'\n即將傳送至"{report["police_department"]}"({report["mobile"]})', quick_reply=QuickReply(
                    items=[QuickReplyButton(action=MessageAction(label='發送', text='發送')), QuickReplyButton(action=MessageAction(label='編輯', text='編輯')), QuickReplyButton(action=MessageAction(label='取消', text='取消'))])))
                return
            # line_bot_api.reply_message(
            #     event.reply_token, TextSendMessage(text='請輸入您的聯絡電話：'))
        elif user_session['action'] == 'report.preview':
            if text == '發送':
                twsms = user_session['twsms_client']
                report = user_session['report']
                r = twsms.send_message(report['sms_msg'], '0953907292')
                print(r)
                # twsms.send_message(
                #     message=report['sms_msg'], mobile=report['mobile'])
            elif text == '編輯':
                user_session['action'] = 'report.address'
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text='請輸入您的地址：'))
            elif text == '取消':
                user_session['action'] = 'report.done'
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text='已取消'))


@ handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print(event.message.id, ' start at ', time.time())
    ext = 'jpg'
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    os.rename(tempfile_path, dist_path)

    uploaded_image = imgur.upload_image(dist_path, title="upload")
    print(uploaded_image.title)
    print(uploaded_image.link)
    print(uploaded_image.size)
    print(uploaded_image.type)
    print(event.message.id, ' end at ', time.time())

    os.remove(dist_path)


@ handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    user_id = event.source.user_id
    user_session = sessions[user_id]
    # location
    address = event.message.address
    for k, v in numbers.items():
        location = k[:2]  # 取地址前兩個字
        if location in address or location.replace('臺', '台') in address:
            print('address: ', address, ', match: ', k, v)
            mobile = v
            user_session['report'] = {
                'police_department': k,
                'mobile': mobile,
                'address': address,
                'latitude': event.message.latitude,
                'longitude': event.message.longitude,
                'car_type': None,
                'car_num': None,
                'license_plates': [],
                'image_links': []
            }
            user_session['action'] = 'report.car_type'
            items = [QuickReplyButton(action=MessageAction(
                label=t, text=t)) for t in CAR_TYPES]
            msg = TextSendMessage(
                text='請輸入車種：', quick_reply=QuickReply(items=items))
            line_bot_api.reply_message(event.reply_token, msg)
            return

    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='您的所在位置無法使用簡訊報案功能'))


@ handler.add(PostbackEvent)
def handle_postback(event):
    data = dict(parse.parse_qsl(event.postback.data))
    user_id = event.source.user_id
    user_session = sessions[user_id]

    if data['event'] == 'confirm_twsms':
        if 'username' in data:
            # 正確
            db.insert_user(event.source.user_id,
                           data['username'], data['password'])
            user_session['username'] = data['username']
            user_session['password'] = data['password']
            user_session['action'] = ''
            # init twsms
            user_session['twsms_client'] = TwsmsClient(
                username=user_session['username'], password=user_session['password'])
            msg = TextSendMessage(text='台灣簡訊設定完成，可以開始報案囉！',
                                  quick_reply=QuickReply(items=[
                                      QuickReplyButton(
                                          action=MessageAction(label='報案', text='報案')),
                                  ]))
            line_bot_api.reply_message(event.reply_token, msg)
    elif user_session['action'] == 'report.situation' and data['event'] == 'change_page':
        # page_num >= 1
        page_num = int(data['page_num'])
        sliced = SITUATIONS[(page_num-1) * (MAX_BUTTON_NUM-1)                            :page_num * (MAX_BUTTON_NUM-1)]
        items = [QuickReplyButton(action=MessageAction(
            label=t, text=t)) for t in sliced]
        if page_num * MAX_BUTTON_NUM >= len(SITUATIONS):
            new_page_num = 1
        else:
            new_page_num = page_num + 1
        items.insert(0, QuickReplyButton(action=PostbackAction(
            label='更多', data='event=change_page&page_num='+str(new_page_num))))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text='請輸入違規情形：', quick_reply=QuickReply(items=items)))
        # else:
        #     # 帳密有誤

        #     line_bot_api.reply_message(
        #         event.reply_token, TextSendMessage(text='請重新輸入您的台灣簡訊帳號：'))
    # elif data['event'] == 'cancel_twsms':
    #     # 取消
    #     del sessions[event.source.user_id]


if __name__ == "__main__":
    app.run(host="localhost", port=8000)
