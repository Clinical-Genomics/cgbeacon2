# -*- coding: utf-8 -*-
import datetime

from cgbeacon2.cli.commands import cli


def test_add_dataset_no_id(public_dataset, mock_app):
    """Test the cli command which adds a dataset to db without a required param"""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    dataset = public_dataset

    # When invoking the command without the -id parameter
    result = runner.invoke(cli, ["add", "dataset", "--name", dataset["name"]])
    # Then the command should return error
    assert result.exit_code == 2
    assert "Missing option '--id'" in result.output


def test_add_dataset_no_name(public_dataset, mock_app):
    """Test the cli command which adds a dataset to db without a required param"""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    dataset = public_dataset

    # When invoking the command without the -name parameter
    result = runner.invoke(cli, ["add", "dataset", "--id", dataset["_id"]])
    # Then the command should return error
    assert result.exit_code == 2
    assert "Missing option '--name'" in result.output


def test_add_dataset_wrong_build(public_dataset, mock_app):
    """Test the cli command which adds a dataset to db without a required param"""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    dataset = public_dataset

    # When invoking the command without a valid genome build
    result = runner.invoke(
        cli,
        [
            "add",
            "dataset",
            "--id",
            dataset["_id"],
            "--name",
            dataset["name"],
            "--build",
            "meh",
        ],
    )
    # Then the command should return error
    assert result.exit_code == 2
    assert "Invalid value for '--build':" in result.output


def test_add_dataset_complete(public_dataset, mock_app, database):
    """Test the cli command which adds a dataset to db with all available params"""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    dataset = public_dataset

    # When invoking the command providing all parameters
    result = runner.invoke(
        cli,
        [
            "add",
            "dataset",
            "--id",
            dataset["_id"],
            "--name",
            dataset["name"],
            "--build",
            dataset["assembly_id"],
            "--authlevel",
            dataset["authlevel"],
            "--desc",
            dataset["description"],
            "--version",
            dataset["version"],
            "--url",
            dataset["url"],
            "--cc",
            dataset["consent_code"],
        ],
    )

    # Then the command should be successful
    assert result.exit_code == 0

    # The new dataset should have been inserted
    new_dataset = database["dataset"].find_one()

    # It should have the provided key/values
    assert new_dataset["_id"] == dataset["_id"]
    assert new_dataset["name"] == dataset["name"]
    assert new_dataset["assembly_id"] == dataset["assembly_id"]
    assert new_dataset["authlevel"] == dataset["authlevel"]
    assert new_dataset["description"] == dataset["description"]
    assert new_dataset["version"] == dataset["version"]
    assert new_dataset["external_url"] == dataset["url"]
    assert new_dataset["consent_code"] == dataset["consent_code"]
    assert new_dataset["created"]

    # And a new avent should have been created in the event collection
    event_obj = database["event"].find_one()
    assert event_obj


def test_add_dataset_wrong_consent(public_dataset, mock_app, database):
    """Test the cli command which adds a dataset to db without a valid consent code"""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    dataset = public_dataset

    # When invoking the command providing all params + non valid consent code
    result = runner.invoke(
        cli,
        [
            "add",
            "dataset",
            "--id",
            dataset["_id"],
            "--name",
            dataset["name"],
            "--build",
            dataset["assembly_id"],
            "--authlevel",
            dataset["authlevel"],
            "--desc",
            dataset["description"],
            "--version",
            dataset["version"],
            "--url",
            dataset["url"],
            "--cc",
            "MEH",  # Non valid consent code
        ],
    )

    # Then the command should print error
    assert result.exit_code == 1
    assert "Consent code seem to have a non-standard value" in result.output

    # and no dataset should be saved to database
    new_dataset = database["dataset"].find_one()
    assert new_dataset is None


def test_update_non_existent_dataset(public_dataset, mock_app, database):
    """Test try to update a dataset that doesn't exist. Should return error"""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    dataset = public_dataset

    # Having an empty dataset collection
    result = database["dataset"].find_one()
    assert result is None

    # When invoking the add command with the update flag to update a dataset
    result = runner.invoke(
        cli,
        [
            "add",
            "dataset",
            "--id",
            dataset["_id"],
            "--name",
            dataset["name"],
            "--build",
            dataset["assembly_id"],
            "--authlevel",
            dataset["authlevel"],
            "--desc",
            dataset["description"],
            "--version",
            dataset["version"],
            "--url",
            dataset["url"],
            "--cc",
            dataset["consent_code"],
            "--update",
        ],
    )
    # Then the command should print error
    assert result.exit_code == 0
    assert "An error occurred while updating dataset collection" in result.output


def test_update_dataset(public_dataset, mock_app, database):
    """Test try to update a dataset that exists."""

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    dataset = public_dataset
    dataset["created"] = datetime.datetime.now()

    # Having a database dataset collection with one item
    result = database["dataset"].insert_one(dataset)
    assert result is not None

    # When invoking the add command with the update flag to update a dataset
    result = runner.invoke(
        cli,
        [
            "add",
            "dataset",
            "--id",
            dataset["_id"],
            "--name",
            dataset["name"],
            "--build",
            dataset["assembly_id"],
            "--authlevel",
            dataset["authlevel"],
            "--desc",
            dataset["description"],
            "--version",
            2.0,  # update to version 2
            "--url",
            dataset["url"],
            "--cc",
            dataset["consent_code"],
            "--update",
        ],
    )

    # Then the command should NOT print error
    assert result.exit_code == 0
    assert "Dataset collection was successfully updated" in result.output

    # And the dataset should be updated
    updated_dataset = database["dataset"].find_one({"_id": dataset["_id"]})
    assert updated_dataset["version"] == 2
    assert updated_dataset["updated"] is not None
