# -*- coding: utf-8 -*-
from cgbeacon2.cli.commands import cli


def test_add_demo(mock_app, database):
    """Test the command line function that adds demo data"""

    # Given an empty demo database
    assert database["dataset"].find_one() is None

    # When calling the demo function to populate database with demo data
    runner = mock_app.test_cli_runner()
    result = runner.invoke(cli, ["add", "demo"])

    # The command shour run without errors
    assert result.exit_code == 0

    # A new dataset should have been inserted
    assert database["dataset"].find_one()

    # Variants should have been inserted into database
    result = database["variant"].find()
    assert sum(1 for i in result) > 0

    # A new user should have been created
    assert database["user"].find_one()
