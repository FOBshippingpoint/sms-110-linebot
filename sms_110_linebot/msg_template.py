from linebot.models import (
    TextSendMessage,
    FlexSendMessage,
    QuickReplyButton,
    QuickReply,
    PostbackAction,
    MessageAction,
    LocationAction,
)
from config import Config
from sms_110_linebot.models.user_session import Setting
from sms_110_linebot.shorten_msg import text_msg, text_quick_msg

config = Config()
SITUATIONS = config.SITUATIONS
MAX_BUTTON_NUM = 13
USER_GUIDE_LINK = config.USER_GUIDE_LINK


def please_enter_twsms_username_template():
    msg = TextSendMessage(text="請輸入您的台灣簡訊帳號")
    return msg


def please_enter_situation(page_num):
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
        text='請用手機按下方的"傳送我的所在位置"按鈕',
        quick_reply=QuickReply(
            items=[QuickReplyButton(action=LocationAction(label="傳送我的所在位置"))]
        ),
    )
    return msg


def default_template():
    msg = text_quick_msg('若需要使用說明，請輸入"說明"', ["說明"])
    return msg


def guide_template():
    msg = text_msg("您可以到以下網址獲得詳細說明：" + USER_GUIDE_LINK)
    return msg


def user_setting_template(setting: Setting):
    msg = FlexSendMessage(
        alt_text="偏好設定",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "偏好設定",
                        "weight": "bold",
                        "size": "xl",
                    }
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": negation_text(setting.send_by_twsms)
                            + "簡訊代發",
                            "data": "event=set_user_setting.send_by_twsms"
                            + "&send_by_twsms="
                            + negation(setting.send_by_twsms),
                        },
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": negation_text(
                                setting.ask_for_license_plates
                            )
                            + "詢問輸入車牌",
                            "data": "event="
                            + "set_user_setting.ask_for_license_plates"
                            + "&ask_for_license_plates="
                            + negation(setting.ask_for_license_plates),
                        },
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": negation_text(setting.ask_for_images)
                            + "詢問上傳照片",
                            "data": "event=set_user_setting.ask_for_images"
                            + "&ask_for_images="
                            + negation(setting.ask_for_images),
                        },
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "編輯簡訊簽名檔",
                            "data": "event=set_user_setting.signature"
                        },
                    },
                ],
                "flex": 0,
            },
        },
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


def confirm_twsms_info_template(username, password):
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
                            "data": "event=confirm_twsms.correct"
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
