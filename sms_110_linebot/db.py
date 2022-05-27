import click
from flask import current_app
from flask.cli import with_appcontext
from peewee import (
    SqliteDatabase,
    CharField,
    ForeignKeyField,
    BooleanField,
    Model,
)

from sms_110_linebot.sms_num_crawler import crawl_mobiles


database = SqliteDatabase(current_app.config["DATABASE"])


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    user_id = CharField(unique=True)
    twsms_username = CharField(default="")
    twsms_password = CharField(default="")


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
    """Create tables."""
    with database:
        database.create_tables([User, Mobile, Setting])


def init_mobiles():
    for police_department, sms_number in crawl_mobiles():
        mobile = Mobile.get_or_none(
            Mobile.police_department == police_department
        )
        if mobile is None:
            Mobile.create(
                police_department=police_department, sms_number=sms_number
            )
        elif mobile.sms_number != mobile:
            mobile.sms_number = mobile
            mobile.save()


@click.command("init-db")
@with_appcontext
def init_db_command():
    create_tables()
    init_mobiles()
    click.echo("Initialized the database.")


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    # app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
