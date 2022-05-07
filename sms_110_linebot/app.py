from flask import Flask, request, abort, g
from urllib import parse
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from linebot.models import (
    MessageEvent,
    PostbackEvent,
    FollowEvent,
    TextMessage,
    LocationMessage,
    ImageMessage,
)

import os
import tempfile
from threading import Thread
from models.user_session import Report, UserSession
from msg_template import (
    change_page_template,
    confirm_twsms_info_template,
    send_location_template,
)
from twsms_client import TwsmsClient
from sms_num_crawler import crawl_mobiles
from config import Config
from shortten_msg import text_msg, text_quick_msg
from database import create_tables, User, Mobile, Setting

app = Flask(__name__)

config = Config()
line_bot_api = config.line_bot_api
handler = config.handler
imgur = config.imgur
parser = config.parser

CAR_TYPES = config.CAR_TYPES
CAR_NUMS = config.CAR_NUMS
SITUATIONS = config.SITUATIONS
sessions = {}

static_tmp_path = os.path.join(os.path.dirname(__file__), "static", "tmp")


def make_static_tmp_dir():
    """Make static tmp dir for image uploads."""
    try:
        os.makedirs(static_tmp_path)
    except FileExistsError:
        pass


make_static_tmp_dir()
create_tables()

# Create mobiles from existing database or from crawler, and if there is no
# data in database, create new data.
mobiles = {}
for police_department, sms_number in crawl_mobiles():
    mobile = Mobile.get_or_none(Mobile.police_department == police_department)
    if mobile is None:
        Mobile.create(
            police_department=police_department, sms_number=sms_number
        )
    elif mobile.sms_number != mobile:
        mobile.sms_number = mobile
        mobile.save()


def get_data_from_event(event):
    """Returns (user_id, text, user_session) from event.

    If the event.message is not TextMessage, returns None.
    """
    user_id = event.source.user_id
    text = None
    # If user is not in sessions, create a new session.
    if user_id not in sessions:
        user = User.get_or_none(User.user_id == user_id)
        sessions[user_id] = UserSession()
        if user is not None:
            sessions[user_id].twsms_client = TwsmsClient(
                user.twsms_username, user.twsms_password
            )
    user_session = sessions[user_id]

    if isinstance(event, MessageEvent):
        if isinstance(event.message, TextMessage):
            text = event.message.text

    return (user_id, text, user_session)


@app.route("/liff/set-twsms-account", methods=["POST"])
def set_twsms_account():
    print("hello")
    # token_type, access_token = request.headers.get('Authorization').split(' ')
    # print(token_type, access_token)
    # print(request.get_json())
    # if token_type != 'Bearer' or token_type is None:
    #     return
    # r = requests.get('https://api.line.me/oauth2/v2.1/verify',
    #                  params={'access_token': access_token})
    # if r.status_code != 200:
    #     return abort(400)
    # # save to username, password to database
    # data = request.get_json()
    # user, created = User.get_or_create(user_id=data['user_id'],
    #                                    twsms_username=data['username'], twsms_password=data['password'])
    # if user:
    #     # if exist, update
    #     user.twsms_username = data['username']
    #     user.twsms_password = data['password']


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # Set g data(user_id, text, user_session) from event
        events = parser.parse(body, signature)
        if events:
            user_id, text, user_session = get_data_from_event(events.pop())
            g.user_id = user_id
            g.text = text
            g.user_session = user_session

        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel"
            + "secret."
        )
        abort(400)

    return "OK"


@handler.add(FollowEvent)
def handle_follow(event):
    user_id = g.user_id
    line_bot_api.reply_message(event.reply_token, text_msg("您好，歡迎使用簡訊違停報案助手"))

    # TODO: 說明運作流程，還有要錢
    line_bot_api.push_message(
        user_id,
        text_quick_msg(
            '在使用前您必須先申請"台灣簡訊"帳號，由此去👉https://www.twsms.com/accjoin.php',
            ["我已經有帳號了"],
        ),
    )
    line_bot_api.push_message(user_id, text_msg("請輸入您的台灣簡訊帳號"))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = g.user_id
    text = g.text
    user_session = g.user_session
    action = user_session.action

    # 設定台灣簡訊帳號過程
    if action.startswith("twsms_setting"):
        if action == "twsms_setting.username":
            user_session.username = text
            line_bot_api.reply_message(
                event.reply_token, text_msg("請輸入您的台灣簡訊密碼")
            )
            user_session.action = "twsms_setting.password"
        elif action == "twsms_setting.password":
            user_session.password = text
            msg = confirm_twsms_info_template(
                username=user_session.username, password=user_session.password
            )
            line_bot_api.reply_message(event.reply_token, msg)

    elif text == "輸入帳密":  # 沒帳號or密碼
        if user_session.twsms_client is not None:
            line_bot_api.reply_message(
                event.reply_token, text_quick_msg("帳號密碼已經存在", ["重新設定帳號密碼"])
            )
        else:
            user_session.action = "twsms_setting.username"
            line_bot_api.reply_message(
                event.reply_token, text_msg("請輸入您的台灣簡訊帳號")
            )

    elif text == "報案":
        user_session.action = "report.address"
        msg = send_location_template()
        line_bot_api.reply_message(event.reply_token, msg)

    elif text == "取消":
        user_session.action = ""
        line_bot_api.reply_message(event.reply_token, text_msg("已取消"))

    elif text == "查詢餘額":
        if user_session.twsms_client is not None:
            twsms = user_session.twsms_client
            r = twsms.get_balance()
            if r["success"]:
                line_bot_api.reply_message(
                    event.reply_token, text_msg(f'您還剩下{r["quota"]}點')
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    text_msg(f'查詢餘額時發生錯誤，原因"{r["error"]}"，請稍後再試'),
                )
            return
        # twsms not set

    elif text == "重設帳密":
        User.delete().where(User.user_id == user_id)
        user_session.username = None
        user_session.password = None
        user_session.twsms_client = None
        user_session.action = "twsms_setting.username"
        line_bot_api.reply_message(event.reply_token, text_msg("請輸入您的台灣簡訊帳號"))

    # 報案過程
    elif action.startswith("report"):
        # 車種
        if action == "report.car_type":
            if text in CAR_TYPES:
                user_session.report.car_type = text
                user_session.action = "report.car_num"
                msg = text_quick_msg("請輸入單輛或多輛", CAR_NUMS)
                line_bot_api.reply_message(event.reply_token, msg)
            else:
                msg = text_msg("請輸入以下車種\n" + "\n".join(CAR_TYPES) + '或"取消"')
                line_bot_api.reply_message(event.reply_token, msg)
        # 單輛/多輛
        elif action == "report.car_num":
            if text in CAR_NUMS:
                user_session.report.car_num = text
                user_session.action = "report.license_plates"
                msg = text_quick_msg('請輸入"以空白分隔的車牌號碼"或"跳過"', ["跳過"])
                line_bot_api.reply_message(event.reply_token, msg)
            else:
                msg = text_msg("請輸入以下車種\n" + "\n".join(CAR_NUMS) + '或"取消"')
                line_bot_api.reply_message(event.reply_token, msg)
        # 車牌號碼
        elif action == "report.license_plates":
            if text != "跳過":
                # TODO: validate license plates
                license_plates = text.split(" ")
                user_session.report.license_plates = license_plates
            user_session.action = "report.situation"

            msg = change_page_template(page_num=1)
            line_bot_api.reply_message(event.reply_token, msg)
            # 違規情形
        elif action == "report.situation":
            if text in SITUATIONS:
                user_session.report.situation = text
                user_session.action = "report.image"

                msg = text_quick_msg('請上傳照片或輸入"跳過"', ["跳過"])
                line_bot_api.reply_message(event.reply_token, msg)
        elif action == "report.image":
            if text == "跳過" or text == "完成":
                user_session.action = "report.preview"
                # generate message
                report = user_session.report
                sms_msg = report.address + "有"
                if report.car_num != "單輛":
                    sms_msg += "多輛"
                sms_msg += report.car_type
                sms_msg += report.situation
                if report.license_plates:
                    sms_msg += "，車牌號碼" + "、".join(report.license_plates)
                if report.image_links:
                    sms_msg += "，附圖連結" + " 、".join(report.image_links)
                sms_msg += " ，請派員處理。"
                report.sms_msg = sms_msg
                msg = text_quick_msg(
                    "簡訊內容\n"
                    + sms_msg
                    + f'\n即將傳送至"{report.police_department}"({report.mobile})',
                    ["發送", "編輯", "取消"],
                )
                line_bot_api.reply_message(event.reply_token, msg)
        elif action == "report.preview":
            if text == "發送" or text == "重新發送":
                twsms = user_session.twsms_client
                report = user_session.report
                r = twsms.send_message(report.sms_msg, "0953907292")
                if r["success"]:
                    msg = text_msg("報案簡訊已發送！")
                else:
                    msg = text_quick_msg(
                        f'報案簡訊發送失敗，原因"{r["error"]}"，是否要"重新發送"？', ["重新發送", "取消"]
                    )
                line_bot_api.reply_message(event.reply_token, msg)
            elif text == "編輯":
                user_session.action = "report.edit"
                msg = text_quick_msg('請輸入簡訊內容，或"取消"', ["取消"])
            elif text == "取消":
                user_session.action = ""
                line_bot_api.reply_message(event.reply_token, text_msg("已取消"))
        elif action == "report.edit":
            if len(text) > 335:
                line_bot_api.reply_message(
                    event.reply_token, text_msg("簡訊長度不能超過335字，請重新輸入")
                )
            else:
                report = user_session.report
                report.sms_msg = text
                user_session.action = "report.preview"
                msg = text_quick_msg(
                    "簡訊內容\n"
                    + report.sms_msg
                    + f'\n即將傳送至"{report.police_department}"({report.mobile})',
                    ["發送", "編輯", "取消"],
                )
                line_bot_api.reply_message(event.reply_token, msg)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = g.user_id
    user_session = g.user_session
    action = user_session.action

    if action == "report.image":
        message_content = line_bot_api.get_message_content(event.message.id)

        # 盡快回覆LINE平台正確的HTTP狀態碼
        # https://engineering.linecorp.com/zh-hant/blog/line-device-10/
        # upload image will take times
        Thread(
            target=upload_image,
            args=(message_content, user_id, user_session),
            daemon=True,
        ).start()
        line_bot_api.reply_message(event.reply_token, text_msg("上傳中..."))


def upload_image(message_content, user_id, user_session):
    """Upload image to imgur and push message to user."""
    ext = "jpg"
    with tempfile.NamedTemporaryFile(
        dir=static_tmp_path, prefix=ext + "-", delete=False
    ) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + "." + ext
    os.rename(tempfile_path, dist_path)
    try:
        uploaded_image = imgur.upload_image(dist_path, title="upload")
        user_session.report.image_links += [uploaded_image.link]
        msg = text_quick_msg('上傳成功，請繼續上傳或"完成"', ["完成"])
    except Exception as err:
        print(err)
        msg = text_quick_msg('上傳失敗，請重新上傳或"跳過"', ["跳過"])
    finally:
        try:
            os.remove(dist_path)
        except Exception as err:
            print(err)
        finally:
            line_bot_api.push_message(user_id, msg)


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    user_session = g.user_session
    action = user_session.action

    if action == "report.address":
        address = event.message.address
        for police_department, mobile in mobiles.items():
            # 地區是警局名稱前二字
            location = police_department[:2]
            if location in address or location.replace("臺", "台") in address:
                print(
                    "address: ",
                    address,
                    ", match: ",
                    police_department,
                    mobile,
                )
                mobile = mobile

                word = "台灣"
                from_ = address.find(word)
                if from_ != -1:
                    address = address[from_ + len(word) :]

                user_session.report = Report(
                    police_department=police_department,
                    mobile=mobile,
                    address=address,
                    latitude=event.message.latitude,
                    longitude=event.message.longitude,
                )
                user_session.action = "report.car_type"
                msg = text_quick_msg("請輸入車種", CAR_TYPES)
                line_bot_api.reply_message(event.reply_token, msg)
                return
        line_bot_api.reply_message(
            event.reply_token, text_msg("您的所在位置無法使用簡訊報案功能")
        )
        user_session.action = ""


@handler.add(PostbackEvent)
def handle_postback(event):
    data = dict(parse.parse_qsl(event.postback.data))

    user_id = g.user_id
    user_session = g.user_session
    action = user_session.action

    if data["event"] == "confirm_twsms":
        if "username" in data:
            # 正確
            user = User.get_or_none(user_id=user_id)
            if user is None:
                User.create(
                    user_id=user_id,
                    twsms_username=data["username"],
                    twsms_password=data["password"],
                )
            else:
                user.twsms_username = data["username"]
                user.twsms_password = data["password"]
                user.save()
            user_session.action = ""
            # init twsms
            twsms = TwsmsClient(
                username=data["username"], password=data["password"]
            )
            twsms.get_balance()
            user_session.twsms_client = twsms
            msg = text_quick_msg("台灣簡訊設定完成", ["報案"])
            line_bot_api.reply_message(event.reply_token, msg)
    elif action == "report.situation" and data["event"] == "change_page":
        msg = change_page_template(page_num=int(data["page_num"]))
        line_bot_api.reply_message(event.reply_token, msg)


if __name__ == "__main__":
    app.run(host="localhost", port=8000, threaded=True)
