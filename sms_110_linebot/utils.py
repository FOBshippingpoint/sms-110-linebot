from sms_110_linebot.models.user_session import Setting as UserSessionSetting


def get_next_report_action(current_action, setting: UserSessionSetting):
    actions = [
        "report.address",
        "report.car_type",
        "report.car_num",
        "report.license_plates",
        "report.situation",
        "report.images",
    ]
    if setting.ask_for_license_plates:
        actions.remove("report.license_plates")
    if setting.ask_for_images:
        actions.remove("report.images")

    if current_action == "report.images" and setting.send_by_twsms:
        actions += ["report.preview"]
    else:
        actions += ["report.copy"]

    next_action_index = actions.index(current_action) + 1
    return (
        actions[next_action_index] if next_action_index < len(actions) else ""
    )


def find_police_department_mobile_by_address(mobiles, address):
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

            word = "台灣"
            from_ = address.find(word)
            if from_ != -1:
                address = address[from_ + len(word) :]
            return police_department, mobile


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
