from configparser import ConfigParser

from flask import Flask, request, abort

from urllib import parse

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
# from linebot.models import (
#     MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
# )

from linebot.models import *

# mine
import db
import message

app = Flask(__name__)

config = ConfigParser()
config.read('config.ini')
LINE_CHANNEL_ACCESS_TOKEN = config["SECRET"]["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = config["SECRET"]["LINE_CHANNEL_SECRET"]


line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/", methods=['POST'])
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
    # if db.select_user(user_id) is None:

    line_bot_api.reply_message(event.reply_token, TextSendMessage(
        text=f'請輸入您的台灣簡訊帳號：'))


twsms = {}


@ handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    if user_id not in twsms:
        twsms[user_id] = {
            'account': None,
            'password': None
        }
    print(twsms)
    text = event.message.text
    if twsms[user_id]['password'] is None:
        if twsms[user_id]['account'] is None:
            twsms[user_id]['account'] = text
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text='請輸入您的台灣簡訊密碼：'))
        else:
            twsms[user_id]['password'] = text
            flex_message = FlexSendMessage(
                alt_text='confirm twsms info',
                contents=message.create_confirm_twsms_info_context(
                    twsms[user_id])
            )
            line_bot_api.reply_message(
                event.reply_token, flex_message)
    if event.message.text == '報案':
        text_message = TextSendMessage(text='Hello, world',
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(action=MessageAction(
                                               label="label", text="text"))
                                       ]))
        line_bot_api.reply_message(
            event.reply_token,
            text_message)


@ handler.add(PostbackEvent)
def handle_postback(event):
    data = dict(parse.parse_qsl(event.postback.data))
    if data['event'] == 'confirm_twsms':
        if 'account' in data:
            # 正確
            db.insert_user(event.source.user_id,
                           data['account'], data['password'])
        else:
            # 帳密有誤
            twsms[event.source.user_id] = {
                'account': None,
                'password': None
            }
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='請重新輸入您的台灣簡訊帳號：'))


if __name__ == "__main__":
    db.init()
    app.run(host="localhost", port=8000)
