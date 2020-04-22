# -*- coding: utf-8 -*-
import pytest
from cgbeacon2.resources import test_snv_vcf_path, test_empty_vcf_path, panel1_path, panel2_path
from cgbeacon2.cli.commands import cli


def test_add_variants_no_dataset(mock_app):
    """Test the cli command which adds variants when no dataset is present in database"""

    runner = mock_app.test_cli_runner()

    # When invoking the add variants with a random dataset ID
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            "a_dataset",
            "-vcf",
            test_snv_vcf_path,
            "-sample",
            "a_sample",
        ],
    )

    # Then the command should return error
    assert result.exit_code == 1
    # And a specific error message
    assert f"Couldn't find any dataset with id 'a_dataset'" in result.output


def test_add_variants_empty_vcf(mock_app, test_dataset_cli, database):
    """Test the cli command to add variants when the VCF file is empty"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = test_dataset_cli
    database["dataset"].insert_one(dataset)

    # When invoking the add variants with an existing but empty VCF file
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            dataset["_id"],
            "-vcf",
            test_empty_vcf_path,
            "-sample",
            "ADM1059A2",
        ],
    )

    # Then the command should return error
    assert result.exit_code == 1
    # And a specific error message
    assert f"Provided VCF file doesn't contain any variant" in result.output

@pytest.mark.skip(reason="This test doesn't seem to work for Travis CI")
def test_add_variants_wrong_samples(mock_app, test_dataset_cli, database):
    """Test the cli command to add variants providing samples that are not in the VCF file"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = test_dataset_cli
    database["dataset"].insert_one(dataset)

    # When invoking the add variants for a sample not in the VCF file
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            dataset["_id"],
            "-vcf",
            test_snv_vcf_path,
            "-sample",
            "foo",
        ],
    )
    # Then the command should return error
    assert result.exit_code == 1
    # And a specific error message
    assert (
        f"Coundn't extract variants from provided VCF file"
        in result.output
    )


def test_add_variants_snv_vcf(mock_app, test_dataset_cli, database):
    """Test the cli command to add SNV variants from VCF file"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = test_dataset_cli
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants from a VCF file
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            dataset["_id"],
            "-vcf",
            test_snv_vcf_path,
            "-sample",
            sample,
        ],
    )

    # Then the command should NOT return error
    assert result.exit_code == 0
    assert f"variants loaded into the database" in result.output

    # and variants parsed correctly have been saved to database
    test_variant = database["variant"].find_one()
    assert isinstance(test_variant["referenceName"], str)
    assert isinstance(test_variant["start"], int)
    assert isinstance(test_variant["startMin"], int)
    assert isinstance(test_variant["startMax"], int)
    assert isinstance(test_variant["end"], int)
    assert isinstance(test_variant["endMin"], int)
    assert isinstance(test_variant["endMax"], int)
    assert isinstance(test_variant["referenceBases"], str)
    assert isinstance(test_variant["alternateBases"], str)
    assert test_variant["assemblyId"] == "GRCh37"
    assert test_variant["datasetIds"] == {dataset["_id"]: {"samples": [sample]}}


def test_add_variants_twice(mock_app, test_dataset_cli, database):
    """Test to add variants from the same sample twice"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = test_dataset_cli
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants from a VCF file for the first time
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            dataset["_id"],
            "-vcf",
            test_snv_vcf_path,
            "-sample",
            sample,
        ],
    )

    # Then a number of variants should have been saved to database
    saved_vars = sum(1 for i in database["variant"].find())

    # WHEN the variants for the same sample are added again
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            dataset["_id"],
            "-vcf",
            test_snv_vcf_path,
            "-sample",
            sample,
        ],
    )

    # Then the number of total variants in the database should NOT increase
    assert saved_vars == sum(1 for i in database["variant"].find())

    # And test sample should be the only sample with variants present for this dataset
    dataset_obj = database["dataset"].find_one({"_id": dataset["_id"]})
    assert dataset_obj["samples"] == [sample]
    assert "updated" in dataset_obj


def test_add_other_sample_variants(mock_app, test_dataset_cli, database):
    """Test adding variants for another sample, same VCF file"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = test_dataset_cli
    database["dataset"].insert_one(dataset)

    # AND 2 samples to add
    sample = "ADM1059A1"
    sample2 = "ADM1059A2"

    # When invoking the add variants from a VCF file for the first time
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            dataset["_id"],
            "-vcf",
            test_snv_vcf_path,
            "-sample",
            sample,
        ],
    )

    # Then a number of variants should have been saved to database
    saved_vars = sum(1 for i in database["variant"].find())

    # WHEN the variants for the other sample are added
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            dataset["_id"],
            "-vcf",
            test_snv_vcf_path,
            "-sample",
            sample2,
        ],
    )

    # Then the number of total variants in the database should increase
    assert saved_vars < sum(1 for i in database["variant"].find())

    # There should be variants called for both samples
    shared_var = database["variant"].find_one(
        {".".join(["datasetIds", dataset["_id"]]): [sample, sample2]}
    )

    # And the samples saved for the dataset should be 2
    dataset_obj = database["dataset"].find_one({"_id": dataset["_id"]})
    assert sample in dataset_obj["samples"]
    assert sample2 in dataset_obj["samples"]
    assert "updated" in dataset_obj


def test_add_panel_filtered_variants(mock_app, test_dataset_cli, database):
    """Test adding variants filtered by panels"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = test_dataset_cli
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants command filtering by panel
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            dataset["_id"],
            "-vcf",
            test_snv_vcf_path,
            "-sample",
            sample,
            "-panel",
            panel1_path,
            "-panel",
            panel2_path
        ],
    )
    # Then the command should return error
    #assert result.exit_code == 1
    # And a specific error message
    #assert f"Couldn't find any dataset with id 'a_dataset'" in result.output
