# -*- coding: utf-8 -*-
from cgbeacon2.server import create_app
from cgbeacon2.instance import config_file_path


def test_create_app_from_envar(monkeypatch):
    """Test option to create app from a file specified by an environment variable"""

    # GIVEN a a config file defined in the environment
    monkeypatch.setenv("CGBEACON2_CONFIG", config_file_path, prepend=False)
    # THEN the app should connect to a database on localhost, port 27017 as defined on config file
    app = create_app()
    assert app
    db_attrs = str(vars(app.db))  # convert database attributes to string
    assert "host=['127.0.0.1:27017']" in db_attrs


def test_create_app_in_container(monkeypatch):
    """Test creating app from inside a container, when an env varianble named 'MONGODB_HOST' ovverides the host provided in config file"""

    # GIVEN an env var named MONGODB_HOST
    monkeypatch.setenv("MONGODB_HOST", "mongodb")
    # THEN the app should connect to a mongo host named mongodb on port 27017
    app = create_app()
    assert app
    db_attrs = str(vars(app.db))  # convert database attributes to string
    assert "host=['mongodb:27017']" in db_attrs
