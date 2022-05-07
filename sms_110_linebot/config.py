import configparser
import pyimgur
import os
from linebot import LineBotApi, WebhookHandler, WebhookParser
from dotenv import load_dotenv

load_dotenv()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class Config(metaclass=Singleton):
    def __init__(self, file="config.ini"):
        self.config = configparser.ConfigParser()
        self.check_file(file)
        # self.LINE_CHANNEL_ACCESS_TOKEN = self.config["line"][
        #     "channel_access_token"
        # ]
        # self.LINE_CHANNEL_SECRET = self.config["line"]["channel_secret"]
        # self.CLIENT_ID = self.config["imgur"]["client_id"]
        
        # environment variables
        self.LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
        self.IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

        # config.ini
        self.CAR_TYPES = self.config["report"]["car_types"].split(" ")
        self.CAR_NUMS = self.config["report"]["car_nums"].split(" ")
        self.SITUATIONS = self.config["report"]["situations"].split(" ")
        self.phone_number = self.config["my"]["phone_number"]

        self.handler = None
        self.parser = None
        self.line_bot_api = None
        self.line_bot_init()
        self.imgur_init()

    def check_file(self, file="config.ini"):
        self.config.read(file, encoding="utf-8")
        if not self.config.sections():
            raise configparser.Error("config.ini not exists")

    def line_bot_init(self):
        self.handler = WebhookHandler(self.LINE_CHANNEL_SECRET)
        self.parser = WebhookParser(self.LINE_CHANNEL_SECRET)
        self.line_bot_api = LineBotApi(self.LINE_CHANNEL_ACCESS_TOKEN)

    def imgur_init(self):
        self.imgur = pyimgur.Imgur(self.IMGUR_CLIENT_ID)
