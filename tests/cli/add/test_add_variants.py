# -*- coding: utf-8 -*-
from cgbeacon2.cli.commands import cli
from cgbeacon2.resources import (
    panel1_path,
    panel2_path,
    test_bnd_vcf_path,
    test_empty_vcf_path,
    test_snv_vcf_path,
    test_sv_vcf_path,
)


def test_add_variants_no_dataset(mock_app):
    """Test the cli command which adds variants when no dataset is present in database"""

    runner = mock_app.test_cli_runner()

    # When invoking the add variants with a random dataset ID
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "--ds",
            "a_dataset",
            "--vcf",
            test_snv_vcf_path,
            "--sample",
            "a_sample",
        ],
    )

    # Then the command should return error
    assert result.exit_code == 1
    # And a specific error message
    assert "Couldn't find any dataset with id 'a_dataset'" in result.output


def test_add_variants_empty_vcf(mock_app, public_dataset, database):
    """Test the cli command to add variants when the VCF file is empty"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    # When invoking the add variants with an existing but empty VCF file
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "--ds",
            dataset["_id"],
            "--vcf",
            test_empty_vcf_path,
            "--sample",
            "ADM1059A2",
        ],
    )

    # Then the command should return error
    assert result.exit_code == 1
    # And a specific error message
    assert "Provided VCF file doesn't contain any variant" in result.output


def test_add_variants_wrong_samples(mock_app, public_dataset, database):
    """Test the cli command to add variants providing samples that are not in the VCF file"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    # When invoking the add variants for a sample not in the VCF file
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "--ds",
            dataset["_id"],
            "--vcf",
            test_snv_vcf_path,
            "--sample",
            "foo",
        ],
    )
    # Then the command should return error
    assert result.exit_code == 1
    # And a specific error message
    assert "One or more provided sample was not found in the VCF file" in result.output


def test_add_variants_snv(mock_app, public_dataset, database):
    """Test the cli command to add SNV variants from a VCF file"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants from a VCF file
    # filtering using one gene panel
    result = runner.invoke(
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
        ],
    )

    # Then the command should NOT return error
    assert result.exit_code == 0
    assert f"variants loaded into the database" in result.output

    # Variants parsed correctly should have been saved to database
    test_variant = database["variant"].find_one()
    assert isinstance(test_variant["referenceName"], str)
    assert isinstance(test_variant["start"], int)
    assert isinstance(test_variant["end"], int)
    assert isinstance(test_variant["referenceBases"], str)
    assert isinstance(test_variant["alternateBases"], str)
    assert test_variant["assemblyId"] == "GRCh37"
    assert sample in test_variant["datasetIds"][dataset["_id"]]["samples"]

    # And one event should have been saved for the updated variant collection
    saved_events = sum(1 for i in database["event"].find({"updated_collection": "variant"}))
    assert saved_events == 1


def test_add_variants_snv_panel_filtered(mock_app, public_dataset, database):
    """Test the cli command to add SNV variants from a panel-filtered VCF file"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants from a VCF file
    # filtering using one gene panel
    result = runner.invoke(
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
            "--panel",
            panel1_path,
        ],
    )

    # Then the command should NOT return error
    assert result.exit_code == 0
    assert "variants loaded into the database" in result.output


def test_add_variants_twice(mock_app, public_dataset, database):
    """Test to add variants from the same sample twice"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants from a VCF file for the first time
    # filtering using 2 gene panels
    result = runner.invoke(
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
            "--panel",
            panel1_path,
            "--panel",
            panel2_path,
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
            "--ds",
            dataset["_id"],
            "--vcf",
            test_snv_vcf_path,
            "--sample",
            sample,
            "--panel",
            panel1_path,
            "--panel",
            panel2_path,
        ],
    )

    # Then the number of total variants in the database should NOT increase
    assert saved_vars == sum(1 for i in database["variant"].find())

    # And test sample should be the only sample with variants present for this dataset
    dataset_obj = database["dataset"].find_one({"_id": dataset["_id"]})
    assert dataset_obj["samples"] == [sample]
    assert "updated" in dataset_obj


def test_add_other_sample_variants(mock_app, public_dataset, database):
    """Test adding variants for another sample, same dataset, same VCF file"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    # AND 2 samples to add
    sample = "ADM1059A1"
    sample2 = "ADM1059A2"

    # When invoking the add variants from a VCF file for the first time
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
            "--panel",
            panel1_path,
        ],
    )

    # Then a number of variants should have been saved to database
    saved_vars = sum(1 for i in database["variant"].find())

    # And dataset should be updated with sampleCount, variantCount, and callCount
    dataset_obj = database["dataset"].find_one()
    assert len(dataset_obj["samples"]) == 1
    assert dataset_obj["variant_count"] == saved_vars
    assert dataset_obj["allele_count"] > 0

    # WHEN the variants for the other sample are added
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
            sample2,
            "--panel",
            panel1_path,
        ],
    )

    # Then the number of total variants in the database should increase
    assert saved_vars < sum(1 for i in database["variant"].find())

    # variantCount, sampleCount and callCount should be increased
    updated_dataset = database["dataset"].find_one()
    assert len(updated_dataset["samples"]) == 2
    assert sample in updated_dataset["samples"]
    assert sample2 in updated_dataset["samples"]
    assert updated_dataset["variant_count"] > dataset_obj["variant_count"]
    assert updated_dataset["allele_count"] > dataset_obj["allele_count"]
    assert "updated" in updated_dataset


def test_add_same_variant_different_datasets(
    mock_app, database, public_dataset, registered_dataset
):
    """Test adding the same variant for 2 samples from 2 distinct datasets"""

    runner = mock_app.test_cli_runner()

    # Having a database containing 2 datasets
    datasets = [public_dataset, registered_dataset]
    for ds in datasets:
        database["dataset"].insert_one(ds)

    # and samples belonging to each dataset
    samples = ["ADM1059A1", "ADM1059A2"]

    # When variants are loaded for each sample
    for (
        count,
        sample,
    ) in enumerate(samples):
        runner.invoke(
            cli,
            [
                "add",
                "variants",
                "--ds",
                datasets[count]["_id"],
                "--vcf",
                test_snv_vcf_path,
                "--sample",
                sample,
                "--panel",
                panel1_path,
            ],
        )

    # Then there should exist variants with hits for both samples (both datasets)
    hit_dset1 = {".".join(["datasetIds", public_dataset["_id"]]): {"$exists": True}}
    hit_dset2 = {".".join(["datasetIds", registered_dataset["_id"]]): {"$exists": True}}
    test_variant = database["variant"].find_one({"$and": [hit_dset1, hit_dset2]})

    # Variant should countain callCount for each sample
    callCount1 = test_variant["datasetIds"][public_dataset["_id"]]["samples"][samples[0]][
        "allele_count"
    ]
    callCount2 = test_variant["datasetIds"][registered_dataset["_id"]]["samples"][samples[1]][
        "allele_count"
    ]

    # And a cumulative call count as well
    assert test_variant["call_count"] == callCount1 + callCount2

    # Both dataset objects should be updated with the right number of samples, variants and calls:
    for ds in datasets:
        updated_dataset = database["dataset"].find_one({"_id": ds["_id"]})
        assert len(updated_dataset["samples"]) == 1
        assert updated_dataset["variant_count"] > 0
        assert updated_dataset["allele_count"] > 0


def test_add_sv_variants(mock_app, public_dataset, database):
    """Test adding SV variants for one sample"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants from a SV VCF file
    runner.invoke(
        cli,
        [
            "add",
            "variants",
            "--ds",
            dataset["_id"],
            "--vcf",
            test_sv_vcf_path,
            "--sample",
            sample,
        ],
    )

    # Then a number of variants should have been saved to database
    saved_vars = list(database["variant"].find())
    assert len(saved_vars) > 0

    valid_types = ["INS", "DUP", "DEL", "INV"]
    # AND all of them should have a valid SV variant type
    for var in saved_vars:
        assert var["variantType"] in valid_types


def test_add_bnd_sv_variants(mock_app, public_dataset, database):
    """Test that BND structural variants are correcly parsed and saved to database"""

    runner = mock_app.test_cli_runner()

    # GIVEN a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants from a SV VCF file containing BNDs
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "--ds",
            dataset["_id"],
            "--vcf",
            test_bnd_vcf_path,
            "--sample",
            sample,
        ],
    )

    # Then a number of variants should have been saved to database
    saved_vars = list(database["variant"].find())
    assert len(saved_vars) > 0

    for var in saved_vars:
        # ALL of them should have a valid SV variant type
        assert var["variantType"] == "BND"
        # AND a mateName (end chromosome)
        assert var["mateName"] != var["referenceName"]  # just for the variants in the demo file


def test_add_snv_sv_variants(mock_app, public_dataset, database):
    """Test adding snv + sv variants for one sample"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a dataset
    dataset = public_dataset
    database["dataset"].insert_one(dataset)

    sample = "ADM1059A1"

    # When invoking the add variants from a VCF file for the first time
    # filtering using 2 gene panels
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "--ds",
            dataset["_id"],
            "-vcf",
            test_snv_vcf_path,
            "--sample",
            sample,
            "--panel",
            panel1_path,
            "--panel",
            panel2_path,
        ],
    )

    # Then a number of SNV variants should have been saved to database
    saved_snvs = sum(1 for i in database["variant"].find())

    # WHEN variants from a another VCF file containing SVs are added
    result = runner.invoke(
        cli,
        [
            "add",
            "variants",
            "--ds",
            dataset["_id"],
            "--vcf",
            test_sv_vcf_path,
            "--sample",
            sample,
        ],
    )

    # THEN more variants should have been added to the database
    new_saved_vars = sum(1 for i in database["variant"].find())
    assert new_saved_vars > saved_snvs
