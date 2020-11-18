# -*- coding: utf-8 -*-
import json
from cgbeacon2.constants import (
    NO_MANDATORY_PARAMS,
    NO_SECONDARY_PARAMS,
    NO_POSITION_PARAMS,
    INVALID_COORDINATES,
    BUILD_MISMATCH,
)
from cgbeacon2.resources import test_snv_vcf_path

HEADERS = {"Content-type": "application/json", "Accept": "application/json"}

BASE_ARGS = "query?assemblyId=GRCh37&referenceName=1&referenceBases=TA"
################## TESTS FOR HANDLING WRONG REQUESTS ################


def test_delete_no_dataset(mock_app):
    """Test receiving a variant delete request missing dataset id param"""
    # When a POST delete request is missing dataset id param:
    data = dict(samples=["sample1", "sample2"])
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=HEADERS)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Invalid request. Please specify a valid dataset ID"


def test_delete_invalid_dataset(mock_app):
    """Test receiving a variant delete request for a dataset not found on the server"""
    # When a POST delete request specifies a dataset not found in the database
    data = dict(dataset_id="FOO", samples=["sample1", "sample2"])
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=HEADERS)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Provided dataset 'FOO' was not found on the server"


def test_delete_invalid_sample_format(mock_app, public_dataset, database):
    """Test receiving a variant delete request with invalid samples param format"""

    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    # When a POST delete request contains an invalid samples parameter
    data = dict(dataset_id=public_dataset["_id"], samples="a_string")
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=HEADERS)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Please provide a valid list of samples"


def test_delete_samples_not_found(mock_app, public_dataset, database):
    """Test receiving a variant delete request with samples not found in that dataset"""

    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    # When a POST delete request contains a list of samples that is not found in the dataset
    data = dict(dataset_id=public_dataset["_id"], samples=["FOO", "BAR"])
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=HEADERS)

    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "None of the provided samples was found in the dataset"


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
    assert data["message"] == "Provided dataset 'FOO' was not found on the server"


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


def test_add_invalid_gene_list(mock_app, public_dataset, database):
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


def test_post_empty_query(mock_app):
    """Test receiving an empty POST query"""

    # When a POST request is missing data
    response = mock_app.test_client().post("/apiv1.0/query?", headers=HEADERS)

    # Then it should return error
    assert response.status_code == 400


def test_query_get_request_missing_mandatory_params(mock_app):
    """Test the query endpoint by sending a request without mandatory params:
    referenceName, referenceBases, assemblyId
    """

    # When a request missing one or more required params is sent to the server
    response = mock_app.test_client().get("/apiv1.0/query?", headers=HEADERS)

    # Then it should return error
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["message"]["error"] == NO_MANDATORY_PARAMS
    assert data["message"]["exists"] is None
    assert data["message"]["datasetAlleleResponses"] == []
    assert data["message"]["beaconId"]
    assert data["message"]["apiVersion"] == "1.0.0"


def test_query_get_request_build_mismatch(mock_app, public_dataset):
    """Test the query endpoint by sending a request with build mismatch between queried datasets and genome build"""

    # Having a dataset with genome build GRCh38 in the database:
    database = mock_app.db
    public_dataset["assembly_id"] = "GRCh38"
    database["dataset"].insert_one(public_dataset)

    # When a request with genome build GRCh37 and detasetIds with genome build GRCh38 is sent to the server:
    query_string = "&".join([BASE_ARGS, f"datasetIds={public_dataset['_id']}"])
    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)

    # Then it should return error
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["message"]["error"] == BUILD_MISMATCH


def test_query_get_request_missing_secondary_params(mock_app):
    """Test the query endpoint by sending a request without secondary params:
    alternateBases, variantType
    """
    # When a request missing alternateBases or variantType params is sent to the server
    query_string = BASE_ARGS
    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)

    # Then it should return error
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["message"]["error"] == NO_SECONDARY_PARAMS


def test_query_get_request_non_numerical_sv_coordinates(mock_app):
    """Test the query endpoint by sending a request with non-numerical start position"""

    query_string = "&".join([BASE_ARGS, "start=FOO&end=70600&variantType=DUP"])
    # When a request has a non-numerical start or stop position
    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)
    data = json.loads(response.data)
    # Then it should return error
    assert response.status_code == 400
    assert data["message"]["error"] == INVALID_COORDINATES


def test_query_get_request_missing_positions_params(mock_app):
    """Test the query endpoint by sending a request missing coordinate params:
    Either start or any range coordinate

    """
    # When a request missing start position and all the 4 range position coordinates (startMin, startMax, endMin, endMax)
    query_string = "&".join([BASE_ARGS, "alternateBases=T"])
    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)
    data = json.loads(response.data)
    # Then it should return error
    assert response.status_code == 400
    assert data["message"]["error"] == NO_POSITION_PARAMS


def test_query_get_request_non_numerical_range_coordinates(mock_app):
    """Test the query endpoint by sending a request with non-numerical range coordinates"""

    range_coords = "&variantType=DUP&startMin=2&startMax=3&endMin=6&endMax=FOO"
    query_string = "&".join([BASE_ARGS, range_coords])

    # When a request for range coordinates doesn't contain integers
    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)
    data = json.loads(response.data)
    # Then it should return error
    assert response.status_code == 400
    assert data["message"]["error"] == INVALID_COORDINATES
