import os
from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "pw_data.db"),
        STATIC_TEMP_PATH=os.path.join(app.instance_path, "static", "tmp"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(os.path.join(app.instance_path, "static", "tmp"))
    except OSError:
        pass

    # a simple page that says hello
    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # register the database commands
    from sms_110_linebot import db

    db.init_app(app)

    # apply the blueprints to the app
    from sms_110_linebot import bot

    app.register_blueprint(bot.bp)

    return app
