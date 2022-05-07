class UserSession:
    def __init__(
        self,
        username=None,
        password=None,
        twsms_client=None,
        action="",
        report=None,
    ):
        self.username = username
        self.password = password
        self.twsms_client = twsms_client
        self.action = action
        self.report = Report() if report is None else report


class Report:
    def __init__(
        self,
        police_department=None,
        mobile=None,
        address=None,
        latitude=None,
        longitude=None,
        car_type=None,
        car_num=None,
        situation=None,
        license_plates=[],
        image_links=[],
        sms_msg="",
    ):
        self.police_department = police_department
        self.mobile = mobile
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.car_type = car_type
        self.car_num = car_num
        self.situation = situation
        self.license_plates = license_plates
        self.image_links = image_links
        self.sms_msg = sms_msg
