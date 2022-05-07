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

config = Config()
SITUATIONS = config.SITUATIONS
MAX_BUTTON_NUM = 13


def change_page_template(page_num):
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
                            "data": "event=confirm_twsms&"
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
                            "data": f"event=confirm_twsms",
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
