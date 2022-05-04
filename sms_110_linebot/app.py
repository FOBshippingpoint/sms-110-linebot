from flask import Flask, request, abort
from urllib import parse
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import *

import time
import os
import db
import message
import tempfile
from twsms import TwsmsClient
from sms_num_crawler import get_numbers
from config import Config
from shortten_msg import text_msg, text_quick_msg

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
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token, text_msg('您好，歡迎使用簡訊違停報案助手'))
    user_id = event.source.user_id

    line_bot_api.push_message(user_id, text_msg('請輸入您的台灣簡訊帳號：'))


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
            line_bot_api.reply_message(
                event.reply_token, text_msg('請輸入您的台灣簡訊密碼：'))
            user_session['action'] = 'input.password'
        elif user_session['action'] == 'input.password':
            user_session['password'] = text
            msg = FlexSendMessage(alt_text='請確認您的帳號密碼是否正確？', contents=message.create_confirm_twsms_info_context(
                username=user_session['username'], password=user_session['password']))
            line_bot_api.reply_message(event.reply_token, msg)
        return

    if text == '輸入帳密':  # 沒帳號or密碼
        user_session = sessions[user_id]
        if user_session['username'] is not None and user_session['password'] is not None:
            line_bot_api.reply_message(
                event.reply_token, text_quick_msg('帳號密碼已經存在', ['重新設定帳號密碼']))
        else:
            user_session['action'] = 'input.username'
            line_bot_api.reply_message(
                event.reply_token, text_msg('請輸入您的台灣簡訊帳號：'))

    elif text == '報案':
        user_session['action'] = 'report.address'
        msg = TextSendMessage(text='請用手機按下方的"傳送我的所在位置"按鈕',
                              quick_reply=QuickReply(items=[
                                  QuickReplyButton(
                                      action=LocationAction(label="傳送我的所在位置"))
                              ]))
        line_bot_api.reply_message(event.reply_token, msg)

    elif text == '取消':
        user_session['action'] = ''
        line_bot_api.reply_message(event.reply_token, text_msg('已取消'))

    elif text == '查詢餘額':
        if user_session['twsms_client'] is not None:
            twsms = user_session['twsms_client']
            try:
                balance = twsms.get_balance()
                line_bot_api.reply_message(
                    event.reply_token, text_msg(f'您還剩下{balance}點'))
            except Exception as e:
                line_bot_api.reply_message(
                    event.reply_token, text_msg('查詢餘額時發生錯誤，請稍後再試'))
            return
        # twsms not set

    elif text == '重設帳密':
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
                msg = text_quick_msg('請輸入單輛或多輛：', CAR_NUMS)
                line_bot_api.reply_message(event.reply_token, msg)
            else:
                msg = text_msg('請輸入以下車種：\n' + '\n'.join(CAR_TYPES) + '或"取消"')
                line_bot_api.reply_message(event.reply_token, msg)
        # 單輛/多輛
        elif user_session['action'] == 'report.car_num':
            if text in CAR_NUMS:
                user_session['report']['car_num'] = text
                user_session['action'] = 'report.license_plates'
                msg = text_quick_msg('請輸入"以空白分隔的車牌號碼"或"跳過"：', ['跳過'])
                line_bot_api.reply_message(event.reply_token, msg)
            else:
                msg = text_msg('請輸入以下車種：\n' + '\n'.join(CAR_NUMS) + '或"取消"')
                line_bot_api.reply_message(event.reply_token, msg)
        # 車牌號碼
        elif user_session['action'] == 'report.license_plates':
            if text != '跳過':
                # TODO: validate license plates?
                license_plates = text.split(' ')
                user_session['report']['license_plates'] = license_plates
            user_session['action'] = 'report.situation'

            page_num = 1
            sliced = SITUATIONS[(page_num-1) * (MAX_BUTTON_NUM-1)
                                 :page_num * (MAX_BUTTON_NUM-1)]

            items = [QuickReplyButton(action=MessageAction(
                label=t, text=t)) for t in sliced]
            items.insert(0, QuickReplyButton(action=PostbackAction(
                label='更多', data='event=change_page&page_num='+str(page_num+1))))
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text='請輸入違規情形：', quick_reply=QuickReply(items=items)))
            # 違規情形
        elif user_session['action'] == 'report.situation':
            if text in SITUATIONS:
                user_session['report']['situation'] = text
                user_session['action'] = 'report.image'

                msg = text_quick_msg('請上傳照片或輸入"跳過"：', ['跳過'])
                line_bot_api.reply_message(event.reply_token, msg)
        elif user_session['action'] == 'report.image':
            if text == '跳過' or text == '完成':
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
                if report['image_links']:
                    sms_msg += '，附圖連結：' + ' 、'.join(report['image_links'])
                sms_msg += ' ，請派員處理。'
                report['sms_msg'] = sms_msg
                msg = text_quick_msg(
                    '簡訊內容：\n' + sms_msg + f'\n即將傳送至"{report["police_department"]}"({report["mobile"]})', ['發送', '編輯', '取消'])
                line_bot_api.reply_message(event.reply_token, msg)
        elif user_session['action'] == 'report.preview':
            if text == '發送' or text == '重新發送':
                twsms = user_session['twsms_client']
                report = user_session['report']
                r = twsms.send_message(report['sms_msg'], '0953907292')
                if 'code' in r and r['code'] == '00000':
                    msg = text_msg('報案簡訊已發送！')
                    report['sms_msg'] = ''
                else:
                    msg = text_quick_msg('報案簡訊發送失敗，是否要"重新發送"？', ['重新發送', '取消'])
                line_bot_api.reply_message(event.reply_token, msg)
                print(r)
            elif text == '編輯':
                user_session['action'] = 'report.edit'
                msg = text_quick_msg('請輸入簡訊內容，或"取消"：', ['取消'])
            elif text == '取消':
                user_session['action'] = 'report.done'
                line_bot_api.reply_message(event.reply_token, text_msg('已取消'))
        elif user_session['action'] == 'report.edit':
            if len(text) > 335:
                line_bot_api.reply_message(
                    event.reply_token, text_msg('簡訊長度不能超過335字，請重新輸入：'))
            else:
                report = user_session['report']
                report['sms_msg'] = text
                user_session['action'] = 'report.preview'
                msg = text_quick_msg(
                    '簡訊內容：\n' + sms_msg + f'\n即將傳送至"{report["police_department"]}"({report["mobile"]})', ['發送', '編輯', '取消'])
                line_bot_api.reply_message(event.reply_token, msg)


@ handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    user_session = sessions[user_id]
    if user_session['action'] == 'report.image':
        print(event.message.id, ' start at ', time.time())
        ext = 'jpg'
        message_content = line_bot_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name

        dist_path = tempfile_path + '.' + ext
        os.rename(tempfile_path, dist_path)
        try:
            uploaded_image = imgur.upload_image(dist_path, title="upload")
            user_session['report']['image_links'] += [uploaded_image.link]
            print(uploaded_image.title)
            print(uploaded_image.link)
            print(uploaded_image.size)
            print(uploaded_image.type)
            print(event.message.id, ' end at ', time.time())

            os.remove(dist_path)
            msg = text_quick_msg('上傳成功，請繼續上傳或"完成"：', ['完成'])
        except Exception as err:
            print(err)
            msg = text_quick_msg('上傳失敗，請重新上傳或"跳過"：', ['跳過'])
        finally:
            line_bot_api.reply_message(event.reply_token, msg)


@ handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    user_id = event.source.user_id
    user_session = sessions[user_id]

    if user_session['action'] == 'report.address':
        # location
        address = event.message.address
        for k, v in numbers.items():
            location = k[:2]  # 取地址前兩個字
            if location in address or location.replace('臺', '台') in address:
                print('address: ', address, ', match: ', k, v)
                mobile = v

                word = '台灣'
                from_ = address.find(word)
                if from_ != -1:
                    address = address[from_ + len(word):]

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
                msg = text_quick_msg('請輸入車種：', CAR_TYPES)
                line_bot_api.reply_message(event.reply_token, msg)
                return
        line_bot_api.reply_message(
            event.reply_token, text_msg('您的所在位置無法使用簡訊報案功能'))
        user_session['action'] = ''


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
            twsms = TwsmsClient(
                username=user_session['username'], password=user_session['password'])
            twsms.get_balance()
            user_session['twsms_client'] = twsms
            msg = text_quick_msg('台灣簡訊設定完成', ['報案'])
            line_bot_api.reply_message(event.reply_token, msg)
    elif user_session['action'] == 'report.situation' and data['event'] == 'change_page':
        # page_num >= 1
        page_num = int(data['page_num'])
        sliced = SITUATIONS[(page_num-1) * (MAX_BUTTON_NUM-1)
                             :page_num * (MAX_BUTTON_NUM-1)]
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


if __name__ == "__main__":
    app.run(host="localhost", port=8000)
