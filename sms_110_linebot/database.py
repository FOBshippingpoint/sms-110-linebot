from peewee import (
    SqliteDatabase,
    CharField,
    ForeignKeyField,
    BooleanField,
    Model,
)

database = SqliteDatabase("pw_data.db")


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    user_id = CharField(unique=True)
    twsms_username = CharField(default='')
    twsms_password = CharField(default='')


class Mobile(BaseModel):
    police_department = CharField()
    sms_number = CharField()


class Setting(BaseModel):
    user_id = ForeignKeyField(User, backref="settings")
    send_by_twsms = BooleanField(default=True)
    ask_for_license_plates = BooleanField(default=True)
    ask_for_images = BooleanField(default=True)
    signature = CharField(default="")


def create_tables():
    with database:
        database.create_tables([User, Mobile, Setting])
