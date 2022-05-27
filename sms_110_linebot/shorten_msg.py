from linebot.models import (
    TextSendMessage,
    MessageAction,
    PostbackAction,
    QuickReplyButton,
    QuickReply,
    FlexSendMessage,
)

from sms_110_linebot.utils import chunks


def text_msg(text):
    return TextSendMessage(text=text)


def text_quick_msg(text, quick_reply_text_list):
    items = [
        QuickReplyButton(action=MessageAction(label=t, text=t))
        for t in quick_reply_text_list
    ]
    msg = TextSendMessage(text=text, quick_reply=QuickReply(items=items))
    return msg


def text_postback_msg(text, postback_list):
    """Create TextSendMessage with PostbackAction

    :param text: text message
    :param postback_list: list of postback action (label, data)
    """
    items = [
        QuickReplyButton(
            action=PostbackAction(label=t[0], display_text=t[0], data=t[1])
        )
        for t in postback_list
    ]
    msg = TextSendMessage(text=text, quick_reply=QuickReply(items=items))
    return msg


def push_many_msg(line_bot_api, user_id, messages):
    """Push many messages to user."""
    for message_chunk in chunks(messages, 5):
        line_bot_api.push_message(user_id, message_chunk)


def button_mapper(b):
    """A mapper func for buttons_msg"""
    if isinstance(b, str):
        return {
            "type": "button",
            "style": "primary",
            "height": "sm",
            "action": {
                "type": "message",
                "label": b,
                "text": b,
            },
        }
    elif "type" in b:
        if "style" not in b:
            b["style"] = "link"
        result = {"type": "button", "style": b["style"], "height": "sm"}

        if "color" in b:
            result["color"] = b["color"]

        if b["type"] == "postback":
            result["action"] = {
                "type": "postback",
                "label": b["text"],
                "data": b["data"],
                "displayText": b["text"],
            }
        elif b["type"] == "message":
            result["action"] = {
                "type": "message",
                "label": b["text"],
                "text": b["text"],
            }

        return result


def button_msg(title, button_list, alt_text=None):
    """FlexMessage with buttons

    :param alt_text: alt text
    :param title: title
    :param buttons: iterable of dicts(style, type, text, data, color) or str
    """
    button_list = map(button_mapper, button_list)
    if alt_text is None:
        alt_text = title
    msg = FlexSendMessage(
        alt_text=alt_text,
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "xl",
                    }
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": button_list,
                "flex": 0,
            },
        },
    )
    return msg
