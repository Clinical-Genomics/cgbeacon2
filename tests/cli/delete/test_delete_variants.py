# -*- coding: utf-8 -*-
from cgbeacon2.cli.commands import cli
from cgbeacon2.resources import panel1_path, test_snv_vcf_path


def test_delete_variants_confirm(mock_app):
    """Test confirm question in delete variants command"""

    runner = mock_app.test_cli_runner()
    # When invoking the command without confirming the action
    result = runner.invoke(cli, ["delete", "variants", "-ds", "foo", "-sample", "bar"])
    # Then the command should exit
    assert result.exit_code == 1
    assert "Do you want to continue?" in result.output


def test_delete_variant_non_existing_dataset(mock_app):
    """Test the command to delete variants when the dataset provided doesn't exist in database"""

    runner = mock_app.test_cli_runner()

    # When invoking the command with a dataset not present in database
    result = runner.invoke(cli, ["delete", "variants", "-ds", "foo", "-sample", "bar"], input="y\n")

    assert result.exit_code == 1
    assert "Couldn't find any dataset with id 'foo' in the database" in result.output


def test_delete_variants_non_existing_sample(mock_app, public_dataset, database):
    """Test the command to delete variants when the sample is not found in database"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    # When invoking the command without a sample not present in dataset samples
    result = runner.invoke(
        cli,
        ["delete", "variants", "-ds", public_dataset["_id"], "-sample", "bar"],
        input="y\n",
    )

    assert result.exit_code == 1
    assert "Couldn't find any sample 'bar' in the sample list of dataset" in result.output


def test_delete_variants(mock_app, public_dataset, database):
    """Test the command to delete variants"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    # And a variants from 2 different samples of a dataset
    sample = "ADM1059A1"
    sample2 = "ADM1059A2"

    # When the load command is invoked with the right params
    runner.invoke(
        cli,
        [
            "add",
            "variants",
            "--ds",
            dataset["_id"],
            "--vcf",
            test_snv_vcf_path,
            "--sample",
            sample,
            "--sample",
            sample2,
            "--panel",
            panel1_path,
        ],
    )
    initial_vars = sum(1 for i in database["variant"].find())
    assert initial_vars > 0

    # There should be variants called for both samples in database
    condition = {"$exists": True}
    test_variant = database["variant"].find_one(
        {
            "$and": [
                {".".join(["datasetIds", dataset["_id"], "samples", sample]): condition},
                {".".join(["datasetIds", dataset["_id"], "samples", sample2]): condition},
            ]
        }
    )
    assert test_variant is not None
    samples = test_variant["datasetIds"][dataset["_id"]]["samples"]
    # Whose allele count contribute to the general variant call count
    cumulative_allele_count = samples[sample]["allele_count"] + samples[sample2]["allele_count"]
    assert test_variant["call_count"] == cumulative_allele_count

    # When one of the samples is removed using the command line
    runner.invoke(
        cli,
        ["delete", "variants", "-ds", public_dataset["_id"], "-sample", sample],
        input="y\n",
    )

    # Then there should be less variants left in the database
    remaining_vars = sum(1 for i in database["variant"].find())
    assert remaining_vars > 0
    assert remaining_vars < initial_vars

    # And the allele count of the test variant above should decrease
    updated_variant = database["variant"].find_one({"_id": test_variant["_id"]})
    assert updated_variant["call_count"] < test_variant["call_count"]

    # And the sample should disappear from the list of dataset samples
    dataset_obj = database["dataset"].find_one({"_id": dataset["_id"]})
    assert sample not in dataset_obj["samples"]

    # A total number of 2 events should have been also saved to database:
    # 1 for adding the variants to the beacon
    # 1 for removing the variants of first sample
    saved_events = sum(1 for i in database["event"].find())
    assert saved_events == 2
