# -*- coding: utf-8 -*-
from cgbeacon2.cli.commands import cli


def test_delete_non_existing_dataset(mock_app):
    """Test the command to delete a dataset when dataset doesn't exist"""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    # When invoking the command without the -id parameter
    result = runner.invoke(cli, ["delete", "dataset", "-id", "foo"])

    # Then the command should run
    assert result.exit_code == 0

    # and return a warning
    assert "Coundn't find a dataset with id 'foo' in database" in result.output


def test_delete_existing_dataset(public_dataset, mock_app, database):
    """Test the command line to delete an existing dataset"""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    dataset = public_dataset

    # When a dataset is inserted into database
    result = runner.invoke(
        cli,
        [
            "add",
            "dataset",
            "-id",
            dataset["_id"],
            "-name",
            dataset["name"],
            "-authlevel",
            dataset["authlevel"],
        ],
    )

    new_dataset = database["dataset"].find_one()
    assert new_dataset is not None

    # If the dataset delete command is invoked providing the right database id
    result = runner.invoke(cli, ["delete", "dataset", "-id", new_dataset["_id"],])

    # Then the command should be executed with no errors
    assert result.exit_code == 0
    assert "Dataset was successfully deleted" in result.output

    # And the dataset should be removed from the database
    new_dataset = database["dataset"].find_one()
    assert new_dataset is None

    # And 2 events should have been saved: one for the added dataset and one for the deleted dataset
    saved_events = sum(1 for i in database["event"].find())
    assert saved_events == 2
