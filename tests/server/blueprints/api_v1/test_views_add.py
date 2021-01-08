# -*- coding: utf-8 -*-
from cgbeacon2.resources import test_snv_vcf_path
import json

HEADERS = {"Content-type": "application/json", "Accept": "application/json"}


def test_add_no_dataset(mock_app):
    """Test receiving a variant add request missing one of the required params"""
    data = dict(vcf_path="path/to/vcf", assemblyId="GRCh37")
    # When a POST add request is missing dataset id param:
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=HEADERS)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "'dataset_id' is a required property"


def test_add_no_vcf_path(mock_app):
    """Test receiving a variant add request missing one of the required params"""
    data = dict(dataset_id="test_id", assemblyId="GRCh37")
    # When a POST add request is missing dataset path to vcf file
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=HEADERS)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "'vcf_path' is a required property"


def test_add_wrong_assembly(mock_app):
    """Test receiving a variant add request with non-valid genome assembly"""
    data = dict(dataset_id="test_id", vcf_path="path/to/vcf", assemblyId="FOO")
    # When a POST add request is sent with a non valid assembly id
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=HEADERS)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "'FOO' is not one of ['GRCh37', 'GRCh38']"


def test_add_wrong_dataset(mock_app):
    """Test receiving a variant add request with non-valid dataset id"""
    data = dict(dataset_id="FOO", vcf_path="path/to/vcf", assemblyId="GRCh37")
    # When a POST add request is sent with a non valid assembly id
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=HEADERS)
    # Then it should return error
    assert response.status_code == 422
    # With message that dataset could not be found
    data = json.loads(response.data)
    assert data["message"] == "Invalid request. Please specify a valid dataset ID"


def test_add_invalid_vcf_path(mock_app, public_dataset, database):
    """Test receiving a variant add request with non-valid vcf path"""

    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    data = dict(dataset_id=public_dataset["_id"], vcf_path="path/to/vcf", assemblyId="GRCh37")
    # When a POST add request is sent with a non valid assembly id
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=HEADERS)
    # Then it should return error
    assert response.status_code == 422
    # With message that VCF path is not valid
    data = json.loads(response.data)
    assert data["message"] == "Error extracting info from VCF file, please check path to VCF"


def test_add_invalid_samples(mock_app, public_dataset, database):
    """Test receiving a variant add request with non-valid samples (samples not in provided VCF file)"""

    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    data = dict(
        dataset_id=public_dataset["_id"],
        vcf_path=test_snv_vcf_path,
        assemblyId="GRCh37",
        samples=["FOO", "BAR"],
    )
    # When a POST add request is sent with non-valid samples
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=HEADERS)
    # Then it should return error
    assert response.status_code == 422
    # With message that VCF files doesn't contain those samples
    data = json.loads(response.data)
    assert "One or more provided samples were not found in VCF" in data["message"]


def test_add_add_variants_api_invalid_gene_list(mock_app, public_dataset, database):
    """Test receiving a variant add request with non-valid genes object"""

    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    data = dict(
        dataset_id=public_dataset["_id"],
        vcf_path=test_snv_vcf_path,
        assemblyId="GRCh37",
        samples=["ADM1059A1"],
        genes={"ids": [17284]},
    )
    # When a POST add request is sent with non-valid genes object (missing id_type for instance)
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=HEADERS)
    # Then it should return error
    assert response.status_code == 422
    # With message that missing info should be provided
    data = json.loads(response.data)
    assert "Please provide id_type (HGNC or Ensembl) for the given list of genes" in data["message"]


def test_add_variants_api_hgnc_genes(mock_app, public_dataset, database, test_gene):
    """Test receiving a request to add variants with valid parameters, hgnc genes"""

    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    # And a test gene:
    database["gene"].insert_one(test_gene)

    # AND no variants
    assert database["variant"].find_one() is None

    samples = ["ADM1059A1"]
    # WHEN the add endpoint receives a POST request with valid data, including a list of HGNC genes
    data = {
        "dataset_id": public_dataset["_id"],
        "vcf_path": test_snv_vcf_path,
        "assemblyId": "GRCh37",
        "samples": samples,
        "genes": {"ids": [17284], "id_type": "HGNC"},
    }
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=HEADERS)
    # Then it should return a success response
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Saving variants to Beacon"
    # And given some time to load variants
    # Variants should be added
    assert database["variant"].find_one()
    updated_dataset = database["dataset"].find_one()
    # And dataset should be updated with sample
    assert updated_dataset["samples"] == samples


def test_add_variants_api_ensembl_genes(mock_app, public_dataset, database, test_gene):
    """Test receiving a request to add variants with valid parameters, hgnc genes"""

    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    # And a test gene:
    database["gene"].insert_one(test_gene)

    # WHEN the add endpoint receives a POST request with valid data, including a list of Ensembl genes
    samples = ["ADM1059A1"]
    data = {
        "dataset_id": public_dataset["_id"],
        "vcf_path": test_snv_vcf_path,
        "assemblyId": "GRCh37",
        "samples": samples,
        "genes": {"ids": ["ENSG00000128513"], "id_type": "Ensembl"},
    }
    response = mock_app.test_client().post("/apiv1.0/add?", json=data, headers=HEADERS)
    # Then it should return a success response
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Saving variants to Beacon"
    # And given some time to load variants
    # Variants should be added
    assert database["variant"].find_one()
    updated_dataset = database["dataset"].find_one()
    # And dataset should be updated with sample
    assert updated_dataset["samples"] == samples
