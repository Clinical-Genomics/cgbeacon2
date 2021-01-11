from cgbeacon2.resources import test_snv_vcf_path
import json


def test_delete_no_auth_token(mock_app, api_req_headers):
    """Test receiving a variant delete request with no X-Auth-Token header key"""
    api_req_headers.pop("X-Auth-Token")
    # When a POST delete request is missing the auth token
    data = dict(samples=["sample1", "sample2"])
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=api_req_headers)
    # then it should return not authorized
    assert response.status_code == 403
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Invalid auth token error"


def test_delete_wrong_auth_token(mock_app, database, api_req_headers):
    """Test receiving a variant delete request with wrong X-Auth-Token"""

    # Given that no authorized API user is present in the database
    assert database["user"].find_one() is None

    # When a POST delete request with token is sent
    data = dict(samples=["sample1", "sample2"])
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=api_req_headers)
    # then it should return not authorized
    assert response.status_code == 403
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Invalid auth token error"


def test_delete_no_dataset(mock_app, database, api_user, api_req_headers):
    """Test receiving a variant delete request missing dataset id param"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    # When a POST delete request is missing dataset id param:
    data = dict(samples=["sample1", "sample2"])
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=api_req_headers)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Invalid request. Please specify a valid dataset ID"


def test_delete_invalid_dataset(mock_app, database, api_user, api_req_headers):
    """Test receiving a variant delete request for a dataset not found on the server"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    # When a POST delete request specifies a dataset not found in the database
    data = dict(dataset_id="FOO", samples=["sample1", "sample2"])
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=api_req_headers)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Invalid request. Please specify a valid dataset ID"


def test_delete_invalid_sample_format(
    mock_app, public_dataset, database, api_user, api_req_headers
):
    """Test receiving a variant delete request with invalid samples param format"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    # When a POST delete request contains an invalid samples parameter
    data = dict(dataset_id=public_dataset["_id"], samples="a_string")
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=api_req_headers)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Please provide a valid list of samples"


def test_delete_samples_not_found(mock_app, public_dataset, database, api_user, api_req_headers):
    """Test receiving a variant delete request with samples not found in that dataset"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    # When a POST delete request contains a list of samples that is not found in the dataset
    data = dict(dataset_id=public_dataset["_id"], samples=["FOO", "BAR"])
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=api_req_headers)

    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    # With a proper error message
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "One or more provided samples was not found in the dataset"


def test_delete_variants_wrong_sample(
    mock_app, public_dataset, database, test_gene, api_user, api_req_headers
):
    """Test the API that deletes variants when a wrong sample is provided for a given dataset"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)
    # And a test gene
    database["gene"].insert_one(test_gene)

    right_sample = "ADM1059A2"

    # And some variants for a sample
    data = {
        "dataset_id": public_dataset["_id"],
        "vcf_path": test_snv_vcf_path,
        "assemblyId": "GRCh37",
        "samples": [right_sample],
        "genes": {"ids": [17284], "id_type": "HGNC"},
    }
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=api_req_headers)
    n_inserted = len(list(database["variant"].find()))
    assert n_inserted > 0
    updated_ds = database["dataset"].find_one()
    assert updated_ds["samples"] == [right_sample]

    # WHEN the delete variants API is used to remove variants for a sample that is not among dataset samples
    data = {"dataset_id": public_dataset["_id"], "samples": ["WRONG_SAMPLE"]}
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=api_req_headers)

    # It should return an error
    assert response.status_code == 422
    resp_data = json.loads(response.data)
    # With a pertinent message
    assert "One or more provided samples was not found in the dataset" in resp_data["message"]


def test_delete_variants_api(
    mock_app, public_dataset, database, test_gene, api_user, api_req_headers
):
    """Test the API that deletes variants according to params specified in user's request"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)
    # And a test gene
    database["gene"].insert_one(test_gene)

    # And some variants for a couple of samples
    data = {
        "dataset_id": public_dataset["_id"],
        "vcf_path": test_snv_vcf_path,
        "assemblyId": "GRCh37",
        "samples": ["ADM1059A1", "ADM1059A2"],
        "genes": {"ids": [17284], "id_type": "HGNC"},
    }
    response = mock_app.test_client().post("/apiv1.0/add", json=data, headers=api_req_headers)
    n_inserted = len(list(database["variant"].find()))
    assert n_inserted > 0

    updated_ds = database["dataset"].find_one()
    assert len(updated_ds["samples"]) == len(data["samples"])  # 2

    # When the delete variants API is used to remove variants for one sample
    data = {"dataset_id": public_dataset["_id"], "samples": ["ADM1059A2"]}
    response = mock_app.test_client().post("/apiv1.0/delete", json=data, headers=api_req_headers)
    # Then the response should return success
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    # Should contain the number of variants updates/removed
    assert resp_data["message"] == "Deleting variants from Beacon"

    # Number of variants on server should change
    n_variants = len(list(database["variant"].find()))
    assert n_variants < n_inserted

    # And dataset object should have been updated
    updated_ds = database["dataset"].find_one()
    assert "ADM1059A2" not in updated_ds["samples"]
