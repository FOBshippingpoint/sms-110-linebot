from linebot.models import (
    TextSendMessage,
    MessageAction,
    PostbackAction,
    QuickReplyButton,
    QuickReply,
)


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
        QuickReplyButton(action=PostbackAction(label=t[0], data=t[1]))
        for t in postback_list
    ]
    msg = TextSendMessage(text=text, quick_reply=QuickReply(items=items))
    return msg
