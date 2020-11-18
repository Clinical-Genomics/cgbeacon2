# -*- coding: utf-8 -*-
import datetime
from cgbeacon2.cli.commands import cli


def test_add_user_wrong_id(mock_app):
    """Test adding a user with a non-valid id (containing space)"""

    runner = mock_app.test_cli_runner()

    # When invoking the add user with an id that is not valid
    result = runner.invoke(cli, ["add", "user", "-id", "test id", "-name", "User Name"],)
    # The command should return error message
    assert "User ID should not contain any space" in result.output


def test_add_user(mock_app, mock_user, database):
    """Test command that adds a user with valid params"""

    runner = mock_app.test_cli_runner()

    # When invoking the add user with valid params
    result = runner.invoke(
        cli,
        [
            "add",
            "user",
            "-id",
            mock_user["id"],
            "-name",
            mock_user["name"],
            "-desc",
            mock_user["description"],
            "-url",
            mock_user["url"],
        ],
    )
    # The command should NOT return error
    assert result.exit_code == 0

    # And user is added to database
    new_user = database["user"].find_one()
    assert new_user["_id"] == mock_user["id"]
    assert new_user["name"] == mock_user["name"]
    assert new_user["description"] == mock_user["description"]
    assert new_user["url"] == mock_user["url"]
    assert new_user["created"]
    assert new_user["token"]


def test_add_user_twice(mock_app, mock_user, database):
    """test adding a user twice using the command line"""

    # Given a database that contains a user
    mock_user["_id"] = mock_user["id"]
    database["user"].insert_one(mock_user)

    runner = mock_app.test_cli_runner()

    # When invoking the add user with to save a user with the same id
    result = runner.invoke(
        cli, ["add", "user", "-id", mock_user["id"], "-name", mock_user["name"]],
    )
    # Then the user is not created
    result = database["user"].find()
    n_users = sum(1 for i in database["user"].find())
    assert n_users == 1
