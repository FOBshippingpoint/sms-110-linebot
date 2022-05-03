import configparser
from linebot import (
    LineBotApi, WebhookHandler
)
import pyimgur


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    def __init__(self, file='config.ini'):
        self.config = configparser.ConfigParser()
        self.check_file(file)
        self.LINE_CHANNEL_ACCESS_TOKEN = self.config["line"]["channel_access_token"]
        self.LINE_CHANNEL_SECRET = self.config["line"]["channel_secret"]
        self.CLIENT_ID = self.config["imgur"]["client_id"]
        self.handler = None
        self.line_bot_api = None
        self.imgur = pyimgur.Imgur(self.CLIENT_ID)
        self.line_bot_init()

    def check_file(self, file='config.ini'):
        self.config.read(file)
        if not self.config.sections():
            raise configparser.Error('config.ini not exists')

    def line_bot_init(self):
        self.handler = WebhookHandler(self.LINE_CHANNEL_SECRET)
        self.line_bot_api = LineBotApi(self.LINE_CHANNEL_ACCESS_TOKEN)
