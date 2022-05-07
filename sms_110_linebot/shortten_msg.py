from linebot.models import (
    TextSendMessage, MessageAction, QuickReplyButton, QuickReply)


def text_msg(text):
    return TextSendMessage(text=text)


def text_quick_msg(text, quick_reply_text_list):
    items = [QuickReplyButton(action=MessageAction(
        label=t, text=t)) for t in quick_reply_text_list]
    msg = TextSendMessage(text=text, quick_reply=QuickReply(items=items))
    return msg