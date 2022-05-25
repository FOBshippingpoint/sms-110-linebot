from sms_110_linebot.models.user_session import Setting as UserSessionSetting


def get_next_report_action(current_action, setting: UserSessionSetting):
    actions = [
        "report.address",
        "report.car_type",
        "report.car_num",
        "report.license_plates",
        "report.situation",
        "report.images",
        "report.preview",
    ]
    if setting.ask_for_license_plates:
        actions.remove("report.license_plates")
    if setting.ask_for_images:
        actions.remove("report.images")
    next_action = actions.index(current_action) + 1
    return next_action if next_action < len(actions) else None


def create_sms_msg(report, signature):
    sms_msg = report.address + "有"
    if report.car_num != "單輛":
        sms_msg += "多輛"
    sms_msg += report.car_type
    sms_msg += report.situation
    if report.license_plates:
        sms_msg += "，車牌號碼" + "、".join(report.license_plates)
    if report.images_links:
        # white space can split links highlighting in LINE.
        sms_msg += "，附圖連結" + " 、".join(report.images_links)
        sms_msg += " ，請派員處理。"
    else:
        sms_msg += "，請派員處理。"
    if signature != "":
        sms_msg += "(" + signature + ")"
    return sms_msg
