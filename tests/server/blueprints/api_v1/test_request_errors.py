# -*- coding: utf-8 -*-
import json

from cgbeacon2.constants import (
    BUILD_MISMATCH,
    INVALID_COORDINATES,
    NO_MANDATORY_PARAMS,
    NO_POSITION_PARAMS,
    NO_SECONDARY_PARAMS,
    UNKNOWN_DATASETS,
)

HEADERS = {"Content-type": "application/json", "Accept": "application/json"}
BASE_ARGS = "query?assemblyId=GRCh37&referenceName=1&referenceBases=TA"
API_V1 = "/apiv1.0/"

################## TESTS FOR HANDLING WRONG REQUESTS ################


def test_post_empty_query(mock_app):
    """Test receiving an empty POST query"""

    # When a POST request is missing data
    response = mock_app.test_client().post("".join([API_V1, "query?"]), headers=HEADERS)

    # Then it should return error
    assert response.status_code == 400


def test_query_get_request_missing_mandatory_params(mock_app):
    """Test the query endpoint by sending a request without mandatory params:
    referenceName, referenceBases, assemblyId
    """

    # When a request missing one or more required params is sent to the server
    response = mock_app.test_client().get("".join([API_V1, "query?"]), headers=HEADERS)

    # Then it should return error
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] == NO_MANDATORY_PARAMS
    assert data["exists"] is None
    assert data["beaconId"]
    assert data["apiVersion"] == "v1.0.1"


def test_query_get_request_unknown_datasets(mock_app):
    """Test the query endpoint with a qquery containing unknown datasets"""

    # GIVEN a database with no datasets
    database = mock_app.db
    assert database["dataset"].find_one() is None

    # WHEN a request contain a specific dataset ID
    ds_param = "datasetIds=foo"
    query_string = "&".join([BASE_ARGS, ds_param])
    response = mock_app.test_client().get("".join([API_V1, query_string]), headers=HEADERS)

    # THEN it should return the expected type of error
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] == UNKNOWN_DATASETS


def test_query_get_request_build_mismatch(mock_app, public_dataset):
    """Test the query endpoint by sending a request with build mismatch between queried datasets and genome build"""

    # Having a dataset with genome build GRCh38 in the database:
    database = mock_app.db
    public_dataset["assembly_id"] = "GRCh38"
    database["dataset"].insert_one(public_dataset)

    # When a request with genome build GRCh37 and detasetIds with genome build GRCh38 is sent to the server:
    query_string = "&".join([BASE_ARGS, f"datasetIds={public_dataset['_id']}"])
    response = mock_app.test_client().get("".join([API_V1, query_string]), headers=HEADERS)

    # Then it should return error
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] == BUILD_MISMATCH


def test_query_get_request_missing_secondary_params(mock_app):
    """Test the query endpoint by sending a request without secondary params:
    alternateBases, variantType
    """
    # When a request missing alternateBases or variantType params is sent to the server
    query_string = BASE_ARGS
    response = mock_app.test_client().get("".join([API_V1, query_string]), headers=HEADERS)

    # Then it should return error
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] == NO_SECONDARY_PARAMS


def test_query_get_request_non_numerical_sv_coordinates(mock_app):
    """Test the query endpoint by sending a request with non-numerical start position"""

    query_string = "&".join([BASE_ARGS, "start=FOO&end=70600&variantType=DUP"])
    # When a request has a non-numerical start or stop position
    response = mock_app.test_client().get("".join([API_V1, query_string]), headers=HEADERS)
    data = json.loads(response.data)
    # Then it should return error
    assert response.status_code == 400
    assert data["error"] == INVALID_COORDINATES


def test_query_get_request_missing_positions_params(mock_app):
    """Test the query endpoint by sending a request missing coordinate params:
    Either start or any range coordinate

    """
    # When a request missing start position and all the 4 range position coordinates (startMin, startMax, endMin, endMax)
    query_string = "&".join([BASE_ARGS, "alternateBases=T"])
    response = mock_app.test_client().get("".join([API_V1, query_string]), headers=HEADERS)
    data = json.loads(response.data)
    # Then it should return error
    assert response.status_code == 400
    assert data["error"] == NO_POSITION_PARAMS


def test_query_get_request_non_numerical_range_coordinates(mock_app):
    """Test the query endpoint by sending a request with non-numerical range coordinates"""

    range_coords = "&variantType=DUP&startMin=2&startMax=3&endMin=6&endMax=FOO"
    query_string = "&".join([BASE_ARGS, range_coords])

    # When a request for range coordinates doesn't contain integers
    response = mock_app.test_client().get("".join([API_V1, query_string]), headers=HEADERS)
    data = json.loads(response.data)
    # Then it should return error
    assert response.status_code == 400
    assert data["error"] == INVALID_COORDINATES
