import json
import time

from cgbeacon2.resources import test_snv_vcf_path

API_ADD_DATASET = "/apiv1.0/add_dataset"
API_ADD = "/apiv1.0/add"
INVALID_TOKEN = "Invalid auth token error"
PATH_TO_VCF = "path/to/vcf"


def test_add_dataset_wrong_auth_token(mock_app, api_req_headers):
    """Test receiving an add_dataset request with an X-Auth-Token header key not registered in database"""

    # WHEN an add request with the wrong token is sent
    api_req_headers["X-Auth-Token"] = "FOO"
    # GIVEN a POST request with data sent to the add_dataset endpoint
    response = mock_app.test_client().post(API_ADD_DATASET, json={}, headers=api_req_headers)
    # then it should return not authorized
    assert response.status_code == 403
    resp_data = json.loads(response.data)
    assert resp_data["message"] == INVALID_TOKEN


def test_add_dataset_missing_data(mock_app, api_req_headers, database, api_user):
    """Test receiving an add_dataset request with one of the mandatory params that is missing (genome build)"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    # GIVEN a request missing one mandatory parameter (build)
    data = {"id": "test_id", "name": "A new dataset"}

    # GIVEN a POST request with data sent to the add_dataset endpoint
    response = mock_app.test_client().post(API_ADD_DATASET, json=data, headers=api_req_headers)
    # then it should return not authorized
    assert response.status_code == 422
    resp_data = json.loads(response.data)
    assert "Dataset genome build 'None' is not valid" in resp_data["message"]


def test_add_dataset(mock_app, api_req_headers, public_dataset, api_user, database):
    """Test receiving an add_dataset request for adding a new dataset"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    # GIVEN a database with no dataset
    assert database["dataset"].find_one() is None
    # AND with no events
    assert database["event"].find_one() is None

    # GIVEN a request containing all the required params
    data = {
        "id": public_dataset["_id"],
        "name": public_dataset["name"],
        "build": public_dataset["assembly_id"],
        "authlevel": public_dataset["authlevel"],
        "description": public_dataset["description"],
        "version": public_dataset["version"],
        "url": public_dataset["url"],
    }

    # GIVEN a POST request with data sent to the add_dataset endpoint
    response = mock_app.test_client().post(API_ADD_DATASET, json=data, headers=api_req_headers)
    # THEN it should return a successful response
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Dataset collection was successfully updated"

    # the dataset should be created:
    assert database["dataset"].find_one({"_id": public_dataset["_id"]})

    # and one event should be registered in events collection
    assert database["event"].find_one(
        {"updated_collection": "dataset", "dataset": public_dataset["_id"]}
    )


def test_add_dataset_existing(mock_app, api_req_headers, public_dataset, api_user, database):
    """Tested adding a dataset to the database when the new dataset ID already exists"""

    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    # GIVEN a database with a dataset
    assert database["dataset"].insert_one(public_dataset)

    # GIVEN a request containing all the required params
    data = {
        "id": public_dataset["_id"],
        "name": public_dataset["name"],
        "build": public_dataset["assembly_id"],
        "authlevel": public_dataset["authlevel"],
        "description": public_dataset["description"],
        "version": public_dataset["version"],
        "url": public_dataset["url"],
    }

    # GIVEN a POST request with data sent to the add_dataset endpoint
    response = mock_app.test_client().post(API_ADD_DATASET, json=data, headers=api_req_headers)

    # THEN it should return an error response
    assert response.status_code == 422
    # CONTAINING the expected error message
    resp_data = json.loads(response.data)
    assert "Duplicate Key Error" in resp_data["message"]


def test_add_variants_no_auth_token(mock_app, api_req_headers):
    """Test receiving an add request with no X-Auth-Token header key"""
    api_req_headers.pop("X-Auth-Token")
    data = dict(vcf_path=PATH_TO_VCF, assemblyId="GRCh37")
    # When a POST add request is missing the token in the header
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # then it should return not authorized
    assert response.status_code == 403
    resp_data = json.loads(response.data)
    assert resp_data["message"] == INVALID_TOKEN


def test_add_variants_wrong_auth_token(mock_app, database, api_user, api_req_headers):
    """Test receiving an add request with an X-Auth-Token header key not registered in database"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
    # WHEN an add request with the wrong token is sent
    api_req_headers["X-Auth-Token"] = "FOO"
    data = dict(vcf_path=PATH_TO_VCF, assemblyId="GRCh37")
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # then it should return not authorized
    assert response.status_code == 403
    resp_data = json.loads(response.data)
    assert resp_data["message"] == INVALID_TOKEN


def test_variants_add_no_dataset(mock_app, api_user, database, api_req_headers):
    """Test receiving a variant add request missing one of the required params"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    data = dict(vcf_path=PATH_TO_VCF, assemblyId="GRCh37")
    # When a POST add request is missing dataset id param:
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "'dataset_id' is a required property"


def test_variants_add_no_vcf_path(mock_app, api_user, database, api_req_headers):
    """Test receiving a variant add request missing one of the required params"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    data = dict(dataset_id="test_id", assemblyId="GRCh37")
    # When a POST add request is missing dataset path to vcf file
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "'vcf_path' is a required property"


def test_variants_add_wrong_assembly(mock_app, api_user, database, api_req_headers):
    """Test receiving a variant add request with non-valid genome assembly"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    data = dict(dataset_id="test_id", vcf_path=PATH_TO_VCF, assemblyId="FOO")
    # When a POST add request is sent with a non valid assembly id
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return error 422 (Unprocessable Entity)
    assert response.status_code == 422
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "'FOO' is not one of ['GRCh37', 'GRCh38']"


def test_variants_add_wrong_dataset(mock_app, api_user, database, api_req_headers):
    """Test receiving a variant add request with non-valid dataset id"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)

    data = dict(dataset_id="FOO", vcf_path=PATH_TO_VCF, assemblyId="GRCh37")
    # When a POST add request is sent with a non valid assembly id
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return error
    assert response.status_code == 422
    # With message that dataset could not be found
    data = json.loads(response.data)
    assert data["message"] == "Invalid request. Please specify a valid dataset ID"


def test_variants_add_invalid_vcf_path(
    mock_app, public_dataset, database, api_user, api_req_headers
):
    """Test receiving a variant add request with non-valid vcf path"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    data = dict(dataset_id=public_dataset["_id"], vcf_path=PATH_TO_VCF, assemblyId="GRCh37")
    # When a POST add request is sent with a non valid assembly id
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return error
    assert response.status_code == 422
    # With message that VCF path is not valid
    data = json.loads(response.data)
    assert "VCF file was not found at the provided path" in data["message"]


def test_variants_add_invalid_samples(
    mock_app, public_dataset, database, api_user, api_req_headers
):
    """Test receiving a variant add request with non-valid samples (samples not in provided VCF file)"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    data = dict(
        dataset_id=public_dataset["_id"],
        vcf_path=test_snv_vcf_path,
        assemblyId="GRCh37",
        samples=["FOO", "BAR"],
    )
    # When a POST add request is sent with non-valid samples
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return error
    assert response.status_code == 422
    # With message that VCF files doesn't contain those samples
    data = json.loads(response.data)
    assert "One or more provided samples were not found in VCF" in data["message"]


def test_variants_add_invalid_gene_list(
    mock_app, public_dataset, database, api_user, api_req_headers
):
    """Test receiving a variant add request with non-valid genes object"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
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
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return error
    assert response.status_code == 422
    # With message that missing info should be provided
    data = json.loads(response.data)
    assert "Please provide id_type (HGNC or Ensembl) for the given list of genes" in data["message"]


def test_variants_add_hgnc_genes(
    mock_app, public_dataset, database, test_gene, api_user, api_req_headers
):
    """Test receiving a request to add variants with valid parameters, hgnc genes"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
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
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return a 202 (accepted) response
    assert response.status_code == 202
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Saving variants to Beacon"
    # And given some time to load variants
    time.sleep(3)
    # Variants should be added
    assert database["variant"].find_one()
    updated_dataset = database["dataset"].find_one()
    # And dataset should be updated with sample
    assert updated_dataset["samples"] == samples


def test_variants_add_ensembl_genes(
    mock_app, public_dataset, database, test_gene, api_user, api_req_headers
):
    """Test receiving a request to add variants with valid parameters, hgnc genes"""
    # GIVEN an authorized API user
    database["user"].insert_one(api_user)
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
    response = mock_app.test_client().post(API_ADD, json=data, headers=api_req_headers)
    # Then it should return a 202 (accepted) response
    assert response.status_code == 202
    resp_data = json.loads(response.data)
    assert resp_data["message"] == "Saving variants to Beacon"
    # And given some time to load variants
    time.sleep(3)
    # Variants should be added
    assert database["variant"].find_one()
    updated_dataset = database["dataset"].find_one()
    # And dataset should be updated with sample
    assert updated_dataset["samples"] == samples
