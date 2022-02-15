# -*- coding: utf-8 -*-
from cgbeacon2.instance import config_file_path
from cgbeacon2.server import configure_email_error_logging, create_app
from cgbeacon2.utils.notify import TlsSMTPHandler


def test_configure_error_log_email(mock_app):
    """Test the app error logging via email"""

    # GIVEN an app with an ADMIN and configured email error logging params
    mail_host = "smtp.gmail.com"
    mail_port = 587
    server_email = "server_email"
    server_pw = "server_pw"

    mock_app.config["ADMINS"] = ["app_admin_email"]
    mock_app.config["MAIL_SERVER"] = mail_host
    mock_app.config["MAIL_PORT"] = mail_port
    mock_app.config["MAIL_USERNAME"] = server_email
    mock_app.config["MAIL_PASSWORD"] = server_pw

    configure_email_error_logging(mock_app)

    # Then a TlsSMTPHandler should be among the app loggers
    handler = mock_app.logger.handlers[0]
    assert isinstance(handler, TlsSMTPHandler)
    # And should contain the given settings
    assert handler.mailhost == mail_host
    assert handler.mailport == mail_port
    assert handler.fromaddr == server_email
    assert handler.password == server_pw
    assert handler.toaddrs == mock_app.config["ADMINS"]


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
