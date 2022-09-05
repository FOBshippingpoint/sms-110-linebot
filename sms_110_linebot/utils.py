from sms_110_linebot.models.user_session import Setting as UserSessionSetting


def get_next_report_action(current_action, setting: UserSessionSetting):
    print('send by twsms', setting.send_by_twsms)
    if current_action == "report.address":
        return "report.car_type"
    elif current_action == "report.car_type":
        return "report.car_num"
    elif current_action == "report.car_num":
        if setting.ask_for_license_plates:
            return "report.license_plates"
        else:
            return "report.situation"
    elif current_action == "report.license_plates":
        return "report.situation"
    elif current_action == "report.situation":
        if setting.ask_for_images:
            return "report.upload_image"
        else:
            if setting.send_by_twsms:
                return "report.preview"
            else:
                return "report.copy"
    elif current_action == "report.upload_image":
        if setting.send_by_twsms:
            return "report.preview"
        else:
            return "report.copy"
    elif current_action == "report.preview":
        return ""
    elif current_action == "report.copy":
        return ""
    elif current_action == "report.edit":
        return "report.preview"
    else:
        return ""


def find_police_department_mobile_by_address(mobiles, address):
    for police_department, sms_number in mobiles.items():
        # 地區是警局名稱前二字
        location = police_department[:2]
        if location in address or location.replace("臺", "台") in address:
            print(
                "address: ",
                address,
                ", match: ",
                police_department,
                sms_number,
            )

            word = "台灣"
            from_ = address.find(word)
            if from_ != -1:
                address = address[from_ + len(word) :]
            return police_department, sms_number, address


def create_sms_msg(report, signature):
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
    if signature != "":
        sms_msg += "(" + signature + ")"
    return sms_msg


def chunks(lst, n):
    """Yield successive n-sized chunks from lst.

    link: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks?page=1&tab=scoredesc#tab-top
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
