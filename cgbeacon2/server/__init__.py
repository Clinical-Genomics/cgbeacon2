# -*- coding: utf-8 -*-
from flask import Flask
import logging
import os
from pymongo import MongoClient

from .blueprints import api_v1

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


def create_app():
    """Method that creates the Flask app"""

    app = None
    app = Flask(__name__)

    try:
        app.config.from_envvar("CGBEACON2_CONFIG")
        LOG.info("Starting app envirironmental variable CGBEACON2_CONFIG")
    except RuntimeError:
        LOG.info("Environment variable settings not found, configuring from instance file.")
        app_root = os.path.abspath(__file__).split("cgbeacon2")[0]

        # check if config file exists under ../instance:
        instance_path = os.path.join(app_root, "cgbeacon2", "instance")
        if not os.path.isfile(os.path.join(instance_path, "config.py")):  # running app from tests
            instance_path = os.path.join(app_root, "cgbeacon2", "cgbeacon2", "instance")

        app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)
        app.config.from_pyfile("config.py")

    if app.config.get("DB_URI") is None:
        LOG.warning("Please add database settings param in your config file.")
        quit()

    # If app is runned from inside a container, override host port
    db_uri = app.config["DB_URI"]
    if os.getenv("MONGODB_HOST"):
        db_uri = f"mongodb://{os.getenv('MONGODB_HOST')}:{'27017'}/{'cgbeacon2'}"

    client = MongoClient(db_uri)
    app.db = client[app.config["DB_NAME"]]
    LOG.info("database connection info:{}".format(app.db))

    app.register_blueprint(api_v1.api1_bp)

    return app
