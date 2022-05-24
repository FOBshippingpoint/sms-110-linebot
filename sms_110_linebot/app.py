from collections import defaultdict
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
from models.user_session import (
    Report,
    UserSession,
    Setting as UserSessionSetting,
)
from msg_template import (
    please_enter_situation,
    confirm_twsms_info_template,
    please_enter_twsms_username_template,
    send_location_template,
    confirm_send_sms_template,
    user_setting_template,
)
from twsms_client import TwsmsClient
from sms_num_crawler import crawl_mobiles
from config import Config
from shorten_msg import (
    push_many_msg,
    text_msg,
    text_postback_msg,
    text_quick_msg,
)
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
if False:
    for police_department, sms_number in crawl_mobiles():
        mobile = Mobile.get_or_none(
            Mobile.police_department == police_department
        )
        if mobile is None:
            Mobile.create(
                police_department=police_department, sms_number=sms_number
            )
        elif mobile.sms_number != mobile:
            mobile.sms_number = mobile
            mobile.save()
        mobiles[police_department] = sms_number
else:
    for mobile in Mobile.select():
        mobiles[mobile.police_department] = mobile.sms_number


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
        Setting.get_or_create(user_id=user_id)
    user_session = sessions[user_id]

    if isinstance(event, MessageEvent):
        if isinstance(event.message, TextMessage):
            text = event.message.text

    return (user_id, text, user_session)


# @app.route("/liff/set-twsms-account", methods=["POST"])
# def set_twsms_account():
#     print("hello")
#     token_type, access_token = request.headers.get("Authorization").split(" ")
#     print(token_type, access_token)
#     print(request.get_json())
#     if token_type != "Bearer" or token_type is None:
#         return
#     r = requests.get(
#         "https://api.line.me/oauth2/v2.1/verify",
#         params={"access_token": access_token},
#     )
#     if r.status_code != 200:
#         return abort(400)
#     # save to username, password to database
#     data = request.get_json()
#     user, created = User.get_or_create(
#         user_id=data["user_id"],
#         twsms_username=data["username"],
#         twsms_password=data["password"],
#     )
#     if user:
#         # if exist, update
#         user.twsms_username = data["username"]
#         user.twsms_password = data["password"]


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
    messages = [
        text_msg("我的任務是幫助您輕鬆用簡訊向警方報案違規停車"),
        text_msg('在使用前您必須先申請"台灣簡訊"帳號，由此去👉https://www.twsms.com/accjoin.php'),
        text_msg("台灣簡訊是一個能幫助您代發簡訊的付費服務，透過簡訊代發警方無法得知您的電話號碼"),
        text_postback_msg(
            "您也可以選擇透過自己的門號發送簡訊，由我替您快速生成報案簡訊",
            [
                ("我已經有帳號了", "event=already_had_account"),
                ("我要用自己的門號發送簡訊", "event=send_by_myself"),
            ],
        ),
    ]
    push_many_msg(line_bot_api, user_id, messages)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = g.user_id
    text = g.text
    user_session = g.user_session
    action = user_session.action
    setting = user_session.setting

    if text == "設定":
        msg = user_setting_template(setting)
        line_bot_api.reply_message(event.reply_token, msg)
    elif text.startswith("broadcast:"):
        # broadcast message
        # ! 測試用
        broadcast_message = text[10:]
        line_bot_api.broadcast(text_msg(broadcast_message))
    # 設定台灣簡訊帳號過程
    elif action.startswith("twsms_setting"):
        if action == "twsms_setting.username":
            user_session.username = text
            user_session.action = "twsms_setting.password"
            line_bot_api.reply_message(
                event.reply_token, text_msg("請輸入您的台灣簡訊密碼")
            )
        elif action == "twsms_setting.password":
            user_session.password = text
            msg = confirm_twsms_info_template(
                username=user_session.username, password=user_session.password
            )
            line_bot_api.reply_message(event.reply_token, msg)
    elif text == "重新設定台灣簡訊帳號密碼":
        user_session.action = "twsms_setting.username"
        msg = please_enter_twsms_username_template()
        line_bot_api.reply_message(event.reply_token, msg)
    elif text == "取消":
        user_session.action = ""
        line_bot_api.reply_message(event.reply_token, text_msg("已取消"))
    elif action.startswith("set_user_setting"):
        if action == "set_user_setting.signature":
            setting.signature = text
            user_session.action = ''
            msg = text_msg("設定完成")
            line_bot_api.reply_message(event.reply_token, msg)
            Thread(
                target=save_setting,
                args=(user_id, setting),
                daemon=True,
            ).start()
    if user_session.twsms_client is None:
        line_bot_api.reply_message(event.reply_token, text_msg("您還沒有設定台灣簡訊帳號"))

        user_session.action = "twsms_setting.username"
        msg = please_enter_twsms_username_template()
        line_bot_api.push_message(user_id, msg)
        return
    # ==============Need Twsms account set==============================
    elif text == "報案":
        user_session.action = "report.address"
        msg = send_location_template()
        line_bot_api.reply_message(event.reply_token, msg)
    elif text == "查詢餘額":
        line_bot_api.reply_message(event.reply_token, text_msg("查詢餘額中..."))
        Thread(
            target=get_balance_and_reply,
            args=(user_id, user_session.twsms_client),
            daemon=True,
        ).start()
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

                msg = text_quick_msg("請輸入車種", CAR_TYPES + ["取消"])
                line_bot_api.push_message(user_id, msg)
        # 單輛/多輛
        elif action == "report.car_num":
            if text in CAR_NUMS:
                user_session.report.car_num = text
                user_session.action = "report.license_plates"
                msg = text_quick_msg('請輸入"以空白分隔的車牌號碼"或"跳過"', ["跳過"])
                line_bot_api.reply_message(event.reply_token, msg)
            else:
                msg = text_quick_msg('請輸入單輛或多輛或"取消"', CAR_NUMS + ["取消"])
                line_bot_api.reply_message(event.reply_token, msg)
        # 車牌號碼
        elif action == "report.license_plates":
            if text != "跳過":
                # TODO: validate license plates
                license_plates = text.split(" ")
                user_session.report.license_plates = license_plates
            user_session.action = "report.situation"
            msg = please_enter_situation(page_num=1)
            line_bot_api.reply_message(event.reply_token, msg)
        # 違規情形
        elif action == "report.situation":
            if text in SITUATIONS:
                user_session.report.situation = text
                user_session.action = "report.image"

                msg = text_quick_msg('請上傳照片或輸入"跳過"', ["跳過"])
                line_bot_api.reply_message(event.reply_token, msg)
            else:
                msg = text_msg("請輸入以下違規情形\n" + "\n".join(SITUATIONS) + '或"取消"')
        elif action == "report.image":
            if text == "跳過" or text == "完成":
                user_session.action = "report.preview"
                report = user_session.report
                report.sms_msg = create_sms_msg(report)

                msg = confirm_send_sms_template(
                    police_department=report.police_department,
                    mobile=report.mobile,
                    sms_msg=report.sms_msg,
                )
                line_bot_api.reply_message(event.reply_token, msg)
        elif action == "report.preview":
            if text == "發送" or text == "重新發送":
                twsms = user_session.twsms_client
                report = user_session.report
                if len(report.sms_msg) > 335:
                    line_bot_api.reply_message(
                        event.reply_token, text_msg("簡訊長度不能超過335字，請重新輸入")
                    )
                    return

                line_bot_api.reply_message(
                    event.reply_token, text_msg("發送中...")
                )
                Thread(
                    target=send_sms_msg_and_reply,
                    args=(user_id, twsms, report.mobile, report.sms_msg),
                    daemon=True,
                ).start()
            elif text == "編輯":
                user_session.action = "report.edit"
                line_bot_api.reply_message(event.reply_token, report.sms_msg)
                messages = [
                    text_msg("您可以複製以上簡訊內容"),
                    text_quick_msg('請輸入新的簡訊內容，或"取消"', ["取消"]),
                ]
                push_many_msg(line_bot_api, user_id, messages)
            elif text == "取消":
                user_session.action = ""
                line_bot_api.reply_message(event.reply_token, text_msg("已取消"))
        elif action == "report.edit":
            # Don't know how Twsms calculates "char" length.
            # check Twsms API DOCs
            # 👉https://www.twsms.com/dl/TwSMS_SMS_API_4.0.pdf
            if len(text) > 335:
                line_bot_api.reply_message(
                    event.reply_token, text_msg("簡訊長度不能超過335字，請重新輸入")
                )
            else:
                report = user_session.report
                report.sms_msg = text
                user_session.action = "report.preview"

                msg = confirm_send_sms_template(
                    police_department=report.police_department,
                    mobile=report.mobile,
                    sms_msg=report.sms_msg,
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
        line_bot_api.reply_message(event.reply_token, text_msg("上傳中..."))
        Thread(
            target=upload_image_and_reply,
            args=(message_content, user_id, user_session),
            daemon=True,
        ).start()


def upload_image_and_reply(message_content, user_id, user_session):
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
    d = dict(parse.parse_qsl(event.postback.data))
    data = defaultdict(lambda: None, d)
    my_event = data["event"]

    user_id = g.user_id
    user_session = g.user_session
    action = user_session.action
    setting = user_session.setting

    if my_event == "already_had_account":
        if user_session.twsms_client is None:
            user_session.action = "twsms_setting.username"
            msg = please_enter_twsms_username_template()
            line_bot_api.reply_message(event.reply_token, msg)
        else:
            msg = text_quick_msg("您可以開始報案囉！", ["報案"])
            line_bot_api.reply_message(event.reply_token, msg)
    elif my_event.startswith("confirm_twsms"):
        # 正確
        if my_event == "confirm_twsms.correct":
            user = User.get_or_none(User.user_id == user_id)
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
            twsms = TwsmsClient(
                username=data["username"], password=data["password"]
            )
            user_session.twsms_client = twsms
            line_bot_api.reply_message(event.reply_token, text_msg("驗證中..."))
            Thread(
                target=validate_twsms_and_reply,
                args=(user_id, twsms),
                daemon=True,
            ).start()
        # 有誤
        elif my_event == "confirm_twsms.incorrect":
            user_session.action = "twsms_setting.username"
            msg = please_enter_twsms_username_template()
            line_bot_api.reply_message(event.reply_token, msg)
    elif my_event == "set_user_setting":
        if data["send_by_twsms"] is not None:
            setting.send_by_twsms = (
                True if data["send_by_twsms"] == "true" else False
            )
        elif data["ask_for_license_plates"] is not None:
            setting.ask_for_license_plates = (
                True if data["ask_for_license_plates"] == "true" else False
            )
        elif data["ask_for_images"] is not None:
            setting.ask_for_images = (
                True if data["ask_for_images"] == "true" else False
            )

        msg = text_msg("設定完成")
        line_bot_api.reply_message(event.reply_token, msg)
        Thread(
            target=save_setting, args=(user_id, setting), daemon=True
        ).start()
    elif my_event == "set_user_setting.signature":
        user_session.action = "set_user_setting.signature"
        msg = text_msg("請輸入要附加的簽名檔：")
        line_bot_api.reply_message(event.reply_token, msg)
    elif my_event == "send_by_myself":
        msg = text_quick_msg("報案助手已設定為簡訊產生模式，可以開始報案囉！", ["報案"])
        line_bot_api.reply_message(event.reply_token, msg)

        new_setting = UserSessionSetting()
        new_setting.send_by_twsms = False
        user_session.setting = new_setting
        Thread(
            target=save_setting,
            args=(user_id, new_setting),
            daemon=True,
        ).start()
    elif my_event == "get_balance":
        line_bot_api.reply_message(event.reply_token, text_msg("查詢餘額中..."))
        Thread(
            target=get_balance_and_reply,
            args=(user_id, user_session.twsms_client),
            daemon=True,
        ).start()
    elif action == "report.situation" and my_event == "change_page":
        msg = please_enter_situation(page_num=int(data["page_num"]))
        line_bot_api.reply_message(event.reply_token, msg)


def validate_twsms_and_reply(user_id, twsms):
    """Validate twsms account."""
    r = twsms.get_balance()
    if r["success"]:
        msg = text_quick_msg("台灣簡訊設定完成", ["報案"])
    elif r["error"] == "帳號或密碼錯誤":
        msg = text_postback_msg(
            '您的台灣簡訊帳號密碼有誤，請"重新輸入"', [("重新輸入", "event=reinput_twsms")]
        )
    else:
        msg = text_postback_msg(
            '您的台灣簡訊驗證過程錯誤，請"重新驗證"或稍後再試', [("重新驗證", "event=revalidate_twsms")]
        )

    line_bot_api.push_message(user_id, msg)


def get_balance_and_reply(user_id, twsms):
    r = twsms.get_balance()
    if r["success"]:
        msg = text_msg(f"您還剩下{r['quota']}點")
    else:
        msg = text_postback_msg(
            f'查詢餘額發生錯誤，原因"{r["error"]}"，請稍後再試', [("查詢餘額", "event=get_balance")]
        )
    line_bot_api.push_message(user_id, msg)


def send_sms_msg_and_reply(user_id, twsms, mobile, sms_msg):
    r = twsms.send_message(sms_msg, config.phone_number)
    if r["success"]:
        msg = text_msg("報案簡訊發送成功！")
    else:
        msg = text_quick_msg(
            f'報案簡訊發送失敗，原因"{r["error"]}"，請稍候再試', ["重新發送", "取消"]
        )
    line_bot_api.push_message(user_id, msg)


def create_sms_msg(report):
    sms_msg = report.address + "有"
    if report.car_num != "單輛":
        sms_msg += "多輛"
    sms_msg += report.car_type
    sms_msg += report.situation
    if report.license_plates:
        sms_msg += "，車牌號碼" + "、".join(report.license_plates)
    if report.image_links:
        # white space can split links highlighting in LINE.
        sms_msg += "，附圖連結" + " 、".join(report.image_links)
        sms_msg += " ，請派員處理。"
    else:
        sms_msg += "，請派員處理。"
    return sms_msg


def save_setting(user_id, session_setting):
    setting = Setting.get_or_create(user_id=user_id)
    setting.send_by_twsms = session_setting.send_by_twsms
    setting.ask_for_license_plates = session_setting.ask_for_license_plates
    setting.ask_for_images = session_setting.ask_for_images
    setting.signature = session_setting.signature
    setting.save()


if __name__ == "__main__":
    app.run(host="localhost", port=8000, threaded=True)
