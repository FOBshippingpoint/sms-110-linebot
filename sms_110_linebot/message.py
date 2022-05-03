def create_confirm_twsms_info_context(username, password):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "請確認您的帳號密碼是否正確？"
                },
                {
                    "type": "separator",
                    "margin": "xxl"
                },
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
                                  "flex": 0
                              },
                                {
                                  "type": "text",
                                  "text": username,
                                  "size": "sm",
                                  "color": "#111111",
                                  "align": "end"
                              }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "密碼",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": password,
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                            ]
                        }
                    ]
                }
            ]
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
                        "data": f"event=confirm_twsms&username={username}&password={password}",
                        "displayText": "正確"
                    },
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "有誤",
                        "data": f"event=confirm_twsms",
                        "displayText": "有誤"
                    },
                    "height": "sm"
                }
            ],
            "flex": 0
        },
        "styles": {
            "footer": {
                "separator": True
            }
        }
    }
