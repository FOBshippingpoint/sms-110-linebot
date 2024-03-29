from linebot.models import (
    TextSendMessage,
    FlexSendMessage,
    QuickReplyButton,
    QuickReply,
    PostbackAction,
    MessageAction,
    LocationAction,
)
from sms_110_linebot.config import Config
from sms_110_linebot.models.user_session import Setting
from sms_110_linebot.shorten_msg import text_msg, button_msg

config = Config()
SITUATIONS = config.SITUATIONS
MAX_BUTTON_NUM = 13
USER_GUIDE_LINK = config.USER_GUIDE_LINK


def welcome_template():
    messages = [
        text_msg("您好，歡迎使用簡訊違停報案助手"),
        text_msg("我的任務是幫助您輕鬆用簡訊向警方報案違規停車"),
        text_msg("使用前請詳閱本服務的隱私權條款：https://github.com/FOBshippingpoint/sms-110-linebot/wiki/%E9%9A%B1%E7%A7%81%E6%AC%8A%E6%A2%9D%E6%AC%BE"),
        text_msg(
            '如果您需要使用簡訊代發服務，必須先申請"台灣簡訊"帳號，申請帳號請點選：https://www.twsms.com/accjoin.php'
        ),
        text_msg("台灣簡訊是一個能幫助您代發簡訊的付費服務，透過簡訊代發警方無法得知您的電話號碼"),
        text_msg("您也可以選擇透過自己的門號發送簡訊，由我替您快速生成報案簡訊"),
        button_msg(
            title="是否要啟用簡訊代發功能",
            button_list=(
                {
                    "type": "postback",
                    "text": "我接受隱私權條款，使用簡訊代發",
                    "data": "event=already_had_account",
                },
                {
                    "type": "postback",
                    "text": "我接受隱私權條款，我要自行發送",
                    "data": "event=send_by_myself",
                },
            ),
        ),
    ]
    return messages


def please_enter_twsms_username_template():
    msg = TextSendMessage(text="請輸入您的台灣簡訊帳號")
    return msg


def please_enter_situation_template(page_num):
    sliced = SITUATIONS[
        (page_num - 1) * (MAX_BUTTON_NUM - 1) : page_num * (MAX_BUTTON_NUM - 1)
    ]
    items = [
        QuickReplyButton(action=MessageAction(label=t, text=t)) for t in sliced
    ]
    if page_num * MAX_BUTTON_NUM >= len(SITUATIONS):
        new_page_num = 1
    else:
        new_page_num = page_num + 1
    items.insert(
        0,
        QuickReplyButton(
            action=PostbackAction(
                label="更多",
                data="event=change_page&page_num=" + str(new_page_num),
            )
        ),
    )
    msg = TextSendMessage(text="請輸入違規情形", quick_reply=QuickReply(items=items))
    return msg


def send_location_template():
    msg = TextSendMessage(
        text='請用手機按下方的"傳送我的所在位置"按鈕，再按下右上角的"分享"',
        quick_reply=QuickReply(
            items=[QuickReplyButton(action=LocationAction(label="傳送我的所在位置"))]
        ),
    )
    return msg


def menu_template():
    msg = button_msg(
        title="主選單",
        button_list=(
            {
                "style": "primary",
                "type": "message",
                "text": "報案",
            },
            {
                "style": "primary",
                "type": "message",
                "text": "設定",
            },
            {
                "style": "primary",
                "type": "message",
                "text": "說明",
            },
        ),
    )
    return msg


def are_you_sure_to_reset_everything_template():
    msg = button_msg(
        title="確定要重置所有設定嗎？",
        button_list=(
            {
                "type": "postback",
                "text": "確定",
                "data": "event=set_user_setting.reset_everything_for_sure",
                "color": "#FA4A4D",
            },
            {
                "type": "message",
                "text": "取消",
                "color": "#979797",
            },
        ),
    )
    return msg


def guide_template():
    msg = text_msg("您可以到以下網址獲得詳細說明：" + USER_GUIDE_LINK)
    return msg


def user_setting_template(setting: Setting):
    msg = button_msg(
        title="偏好設定",
        button_list=(
            {
                "type": "postback",
                "text": negation_text(setting.send_by_twsms) + "簡訊代發",
                "data": "event=set_user_setting"
                + "&send_by_twsms="
                + negation(setting.send_by_twsms),
            },
            {
                "type": "postback",
                "text": negation_text(setting.ask_for_license_plates)
                + "詢問輸入車牌",
                "data": "event=set_user_setting"
                + "&ask_for_license_plates="
                + negation(setting.ask_for_license_plates),
            },
            {
                "type": "postback",
                "text": negation_text(setting.ask_for_images) + "詢問上傳照片",
                "data": "event=set_user_setting"
                + "&ask_for_images="
                + negation(setting.ask_for_images),
            },
            {
                "type": "postback",
                "text": "編輯簡訊簽名檔",
                "data": "event=set_user_setting.signature",
            },
            {
                "type": "postback",
                "text": "重設台灣簡訊帳號密碼",
                "data": "event=set_user_setting.reset_twsms",
            },
            {
                "style": "primary",
                "type": "postback",
                "text": "重置所有設定",
                "data": "event=set_user_setting.reset_everything",
                "color": "#FA4A4D",
            },
        ),
    )
    return msg


def negation(current_status):
    if current_status:
        return "false"
    else:
        return "true"


def negation_text(current_status):
    if current_status:
        return "關閉"
    else:
        return "開啟"


def confirm_twsms_template(username, password):
    msg = FlexSendMessage(
        alt_text="請確認您的帳號密碼是否正確？",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "請確認您的帳號密碼是否正確？"},
                    {"type": "separator", "margin": "xxl"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "帳號",
                                        "size": "sm",
                                        "color": "#555555",
                                        "flex": 0,
                                    },
                                    {
                                        "type": "text",
                                        "text": username,
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end",
                                    },
                                ],
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "密碼",
                                        "size": "sm",
                                        "color": "#555555",
                                    },
                                    {
                                        "type": "text",
                                        "text": password,
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end",
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "正確",
                            "data": "event=confirm_twsms.correct&"
                            + f"username={username}&"
                            + f"password={password}",
                            "displayText": "正確",
                        },
                        "height": "sm",
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "有誤",
                            "data": "event=confirm_twsms.incorrect",
                            "displayText": "有誤",
                        },
                        "height": "sm",
                    },
                ],
                "flex": 0,
            },
            "styles": {"footer": {"separator": True}},
        },
    )
    return msg


def confirm_send_sms_template(police_department, mobile, sms_msg):
    msg = FlexSendMessage(
        alt_text="請確認要傳送的訊息",
        contents={
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "即將傳送至",
                                "color": "#ffffff66",
                                "size": "sm",
                            },
                            {
                                "type": "text",
                                "text": police_department,
                                "color": "#ffffff",
                                "size": "lg",
                                "flex": 4,
                                "weight": "bold",
                            },
                            {
                                "type": "text",
                                "text": f"({mobile})",
                                "color": "#ffffff66",
                                "size": "md",
                            },
                        ],
                    }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#0367D3",
                "spacing": "md",
                "height": "114px",
                "paddingTop": "22px",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": sms_msg,
                                "color": "#363636",
                                "size": "md",
                                "wrap": True,
                            }
                        ],
                        "flex": 1,
                    }
                ],
                "spacing": "md",
                "paddingAll": "12px",
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "發送",
                            "text": "發送",
                        },
                        "height": "sm",
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "編輯",
                            "text": "編輯",
                        },
                        "height": "sm",
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "取消",
                            "text": "取消",
                        },
                        "height": "sm",
                    },
                ],
                "flex": 0,
            },
            "styles": {"footer": {"separator": True}},
        },
    )
    return msg
