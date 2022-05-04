from peewee import *

db = SqliteDatabase('pw.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    user_id = CharField(unique=True)
    twsms_username = CharField()
    twsms_password = CharField()


class Mobile(BaseModel):
    police_department = CharField()
    sms_number = CharField()


class Setting(BaseModel):
    user_id = ForeignKeyField(User, backref='settings')