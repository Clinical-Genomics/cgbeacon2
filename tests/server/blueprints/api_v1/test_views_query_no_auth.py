# -*- coding: utf-8 -*-
import json

from cgbeacon2.cli.commands import cli
from cgbeacon2.resources import test_bnd_vcf_path
from cgbeacon2.resources import test_snv_vcf_path

HEADERS = {"Content-type": "application/json", "Accept": "application/json"}

BASE_ARGS = "query?assemblyId=GRCh37&referenceName=1&referenceBases=TA"
COORDS_ARGS = "start=235826381&end=235826383"
ALT_ARG = "alternateBases=T"


def test_post_range_coords_BND_SV_found(mock_app, public_dataset, database, test_bnd_sv):
    """Test a POST request to search for an existing BND structural variant

    curl -X POST \
    localhost:5000/apiv1.0/query \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json' \
    -d '{"referenceName": "17",
    "mateName": "2",
    "variantType" : "BND",
    "startMin": 198000,
    "startMax": 200000,
    "referenceBases": "A",
    "assemblyId": "GRCh37",
    "includeDatasetResponses": "HIT"}'

    """

    # GIVEN a database containing a public dataset
    database["dataset"].insert_one(public_dataset)

    sample = "ADM1059A1"

    # AND a number of BND variants
    runner = mock_app.test_cli_runner()
    runner.invoke(
        cli,
        [
            "add",
            "variants",
            "-ds",
            public_dataset["_id"],
            "-vcf",
            test_bnd_vcf_path,
            "-sample",
            sample,
        ],
    )

    data = json.dumps(
        {
            "referenceName": test_bnd_sv["referenceName"],
            "referenceBases": test_bnd_sv["referenceBases"],
            "mateName": test_bnd_sv["mateName"],
            "variantType": test_bnd_sv["variantType"],  # BND
            "assemblyId": test_bnd_sv["assemblyId"],
            "startMin": test_bnd_sv["start"] - 1000,
            "startMax": test_bnd_sv["start"] + 1000,
            "includeDatasetResponses": "ALL",
        }
    )

    # When calling the endpoing with the POST method
    response = mock_app.test_client().post("/apiv1.0/query", data=data, headers=HEADERS)

    # Should not return error
    assert response.status_code == 200
    resp_data = json.loads(response.data)

    # And the variant should be found
    assert resp_data["datasetAlleleResponses"][0]["exists"]


def test_beacon_entrypoint(mock_app, registered_dataset):
    """Test the endpoint that returns the beacon info, when there is one dataset in database"""

    runner = mock_app.test_cli_runner()

    # Having a database containing a registered_dataset dataset
    database = mock_app.db

    runner.invoke(
        cli,
        [
            "add",
            "dataset",
            "-id",
            registered_dataset["_id"],
            "-name",
            registered_dataset["name"],
            "-authlevel",
            registered_dataset["authlevel"],
        ],
    )
    assert database["dataset"].find_one()

    with mock_app.test_client() as client:

        # When calling the endpoing with the GET method
        response = client.get("/apiv1.0/", headers=HEADERS)
        assert response.status_code == 200

        # The returned data should contain all the expected fields
        data = json.loads(response.data)
        fields = [
            "id",
            "name",
            "apiVersion",
            "organisation",
            "datasets",
            "createDateTime",
            "updateDateTime",
        ]
        for field in fields:
            assert data[field] is not None

        # including the dataset info
        assert data["datasets"][0]["id"]
        assert data["datasets"][0]["info"]["accessType"] == "REGISTERED"
        assert len(data["sampleAlleleRequests"]) == 2  # 2 query examples provided


################## TESTS FOR HANDLING GET REQUESTS ################


def test_get_request_exact_position_snv_return_ALL(
    mock_app, test_snv, public_dataset, public_dataset_no_variants
):
    """Test the query endpoint by sending a GET request. Search for SNVs, exact position, return responses from ALL datasets"""

    # Having a dataset with a variant:
    database = mock_app.db
    database["variant"].insert_one(test_snv)

    # And 2 datasets
    public_dataset["samples"] = ["ADM1059A1"]
    for ds in [public_dataset, public_dataset_no_variants]:
        database["dataset"].insert_one(ds)

    # when providing the required parameters in a SNV query for exact positions
    ds_reponse_type = "includeDatasetResponses=ALL"
    query_string = "&".join([BASE_ARGS, COORDS_ARGS, ALT_ARG, ds_reponse_type])

    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)
    data = json.loads(response.data)

    # No error should be returned
    assert response.status_code == 200

    # AllelRequest field should reflect the original query
    assert data["allelRequest"]["referenceName"] == "1"
    assert data["allelRequest"]["start"]
    assert data["allelRequest"]["end"]
    assert data["allelRequest"]["referenceBases"] == "TA"
    assert data["allelRequest"]["alternateBases"] == "T"
    assert data["allelRequest"]["includeDatasetResponses"] == "ALL"

    assert data.get("message") is None

    # Beacon info should be returned
    assert data["beaconId"]
    assert data["apiVersion"] == "1.0.0"

    # Response should provide dataset-level detailed info
    assert len(data["datasetAlleleResponses"]) == 2
    for ds_level_result in data["datasetAlleleResponses"]:
        # Response could be positive or negative
        assert ds_level_result["exists"] in [True, False]

        # And should include allele count
        assert ds_level_result["callCount"] is not None

        # Allele count should be a positive number when there is positive match
        if ds_level_result["exists"] is True:
            assert ds_level_result["callCount"] > 0

        # Variant count should also be a positive number if there is positive match
        if ds_level_result["exists"] is True:
            assert ds_level_result["variantCount"] > 0

        # Dataset info should be available and containing the expected info
        assert ds_level_result["info"] == {"accessType": "PUBLIC"}


def test_get_request_exact_position_snv_return_HIT(
    mock_app, test_snv, public_dataset, public_dataset_no_variants
):
    """Test the query endpoint by sending a GET request. Search for SNVs, exact position, return only responses from dataset with variant (HIT)"""

    # Having a dataset with a variant:
    database = mock_app.db
    database["variant"].insert_one(test_snv)

    # And 2 datasets
    public_dataset["samples"] = ["ADM1059A1"]
    for ds in [public_dataset, public_dataset_no_variants]:
        database["dataset"].insert_one(ds)

    # when providing the required parameters in a SNV query for exact positions
    ds_reponse_type = "includeDatasetResponses=HIT"
    query_string = "&".join([BASE_ARGS, COORDS_ARGS, ALT_ARG, ds_reponse_type])

    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)
    data = json.loads(response.data)

    # No error should be returned
    assert response.status_code == 200
    assert data.get("message") is None

    # And only the dataset with hits should be returned
    assert len(data["datasetAlleleResponses"]) == 1
    assert data["datasetAlleleResponses"][0]["datasetId"] == public_dataset["_id"]
    assert data["datasetAlleleResponses"][0]["exists"]


def test_get_request_exact_position_snv_return_MISS(
    mock_app, test_snv, public_dataset, public_dataset_no_variants
):
    """Test the query endpoint by sending a GET request. Search for SNVs, exact position, return only responses from dataset with no hits (MISS)"""

    # Having a dataset with a variant:
    database = mock_app.db
    database["variant"].insert_one(test_snv)

    # And 2 datasets
    public_dataset["samples"] = ["ADM1059A1"]
    for ds in [public_dataset, public_dataset_no_variants]:
        database["dataset"].insert_one(ds)

    # when providing the required parameters in a SNV query for exact positions
    ds_reponse_type = "includeDatasetResponses=MISS"
    query_string = "&".join([BASE_ARGS, COORDS_ARGS, ALT_ARG, ds_reponse_type])

    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)
    data = json.loads(response.data)

    # No error should be returned
    assert response.status_code == 200
    assert data.get("message") is None

    # And only the dataset with NO hits should be returned
    assert len(data["datasetAlleleResponses"]) == 1
    assert data["datasetAlleleResponses"][0]["datasetId"] == public_dataset_no_variants["_id"]
    assert data["datasetAlleleResponses"][0]["exists"] is False


def test_get_request_snv_return_NONE(mock_app, test_snv, public_dataset):
    """Test the query endpoint by sending a GET request. Search for SNVs, includeDatasetResponses=None"""

    # Having a database with a variant:
    database = mock_app.db
    database["variant"].insert_one(test_snv)

    # And a dataset
    database["dataset"].insert_one(public_dataset)

    # when providing the required parameters in a SNV query with includeDatasetResponses=NONE (or omitting the param)
    query_string = "&".join([BASE_ARGS, "start=235826381", ALT_ARG])
    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)
    data = json.loads(response.data)

    # No error should be returned
    assert response.status_code == 200
    assert data["allelRequest"]["includeDatasetResponses"] == "NONE"
    # No specific dataset response should be prensent
    assert data["datasetAlleleResponses"] == []
    # But since variant is found, beacon responds: True
    assert data["exists"] is True


def test_get_snv_query_variant_not_found(mock_app, public_dataset):
    """Test a query that should return variant not found (exists=False)"""

    # Having a database with a dataset but no variant:
    database = mock_app.db
    database["dataset"].insert_one(public_dataset)

    # when querying for a variant
    query_string = "&".join([BASE_ARGS, "start=235826381", ALT_ARG])
    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)
    data = json.loads(response.data)

    # No error should be returned
    assert response.status_code == 200

    # AllelRequest field should reflect the original query
    assert data["allelRequest"]["referenceName"] is not None
    assert data["allelRequest"]["start"] is not None
    assert data["allelRequest"]["referenceBases"] is not None
    assert data["allelRequest"]["alternateBases"] is not None
    assert data["allelRequest"]["includeDatasetResponses"] == "NONE"

    # and response should be negative (exists=False)
    assert data["exists"] is False
    assert data["error"] is None


################## TESTS FOR HANDLING SV GET REQUESTS ################


def test_get_request_svs_range_coordinates(mock_app, test_sv, public_dataset):
    """test get request providing coordinate range for querying structural variants"""

    # Having a database with a variant:
    database = mock_app.db
    database["variant"].insert_one(test_sv)

    # And a dataset
    database["dataset"].insert_one(public_dataset)

    build = test_sv["assemblyId"]
    chrom = test_sv["referenceName"]
    ref = test_sv["referenceBases"]
    base_sv_coords = f"query?assemblyId={build}&referenceName={chrom}&referenceBases={ref}"

    vtype = f"variantType={test_sv['variantType']}"

    # When providing range coordinates
    start_min = test_sv["start"] - 5
    start_max = test_sv["start"] + 5
    end_min = test_sv["end"] - 5
    end_max = test_sv["end"] + 5
    range_coords = f"startMin={start_min}&startMax={start_max}&endMin={end_min}&endMax={end_max}"

    query_string = "&".join([base_sv_coords, range_coords, vtype])

    response = mock_app.test_client().get("".join(["/apiv1.0/", query_string]), headers=HEADERS)

    data = json.loads(response.data)
    # No error should be returned
    assert response.status_code == 200
    # And the beacon should answer exists=True (variant found)
    assert data["exists"] is True


def test_query_form_get(mock_app):
    """Test the interactive query interface page"""

    # When calling the endpoing with the GET method
    response = mock_app.test_client().get("/apiv1.0/query_form")

    # Should not return error
    assert response.status_code == 200


################## TESTS FOR HANDLING JSON POST REQUESTS ################


def test_post_query(mock_app, test_snv, public_dataset):
    """Test receiving classical POST json request and returning a response
        curl -X POST \
        localhost:5000/apiv1.0/query \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json' \
        -d '{"referenceName": "1",
        "start": 156146085,
        "referenceBases": "C",
        "alternateBases": "A",
        "assemblyId": "GRCh37",
        "includeDatasetResponses": "HIT"}'
    """

    # Having a database with a variant:
    database = mock_app.db
    database["variant"].insert_one(test_snv)

    # And a dataset
    database["dataset"].insert_one(public_dataset)

    data = json.dumps(
        {
            "referenceName": test_snv["referenceName"],
            "start": test_snv["start"],
            "referenceBases": test_snv["referenceBases"],
            "alternateBases": test_snv["alternateBases"],
            "assemblyId": test_snv["assemblyId"],
            "datasetIds": [public_dataset["_id"]],
            "includeDatasetResponses": "HIT",
        }
    )

    # When calling the endpoing with the POST method
    response = mock_app.test_client().post("/apiv1.0/query", data=data, headers=HEADERS)

    # Should not return error
    assert response.status_code == 200
    resp_data = json.loads(response.data)

    # And all the expected fields should be present in the response
    assert resp_data["allelRequest"]["referenceName"] == test_snv["referenceName"]
    assert resp_data["allelRequest"]["start"] == test_snv["start"]
    assert resp_data["allelRequest"]["referenceBases"] == test_snv["referenceBases"]
    assert resp_data["allelRequest"]["alternateBases"] == test_snv["alternateBases"]
    assert resp_data["allelRequest"]["assemblyId"] == test_snv["assemblyId"]
    assert resp_data["allelRequest"]["includeDatasetResponses"] == "HIT"

    # Including the hit result
    assert resp_data["datasetAlleleResponses"][0]["datasetId"] == public_dataset["_id"]
    assert resp_data["datasetAlleleResponses"][0]["exists"] is True


################### TESTS FOR HANDLING POST REQUESTS FROM THE WEB INTERFACE ################


def test_query_form_post_snv_exact_coords_found(mock_app, test_snv, public_dataset):
    """Test the interactive query interface, snv, exact coordinates"""

    # Having a database with a variant:
    database = mock_app.db
    database["variant"].insert_one(test_snv)

    # And a dataset
    database["dataset"].insert_one(public_dataset)

    form_data = dict(
        assemblyId=test_snv["assemblyId"],
        referenceName=test_snv["referenceName"],
        start=test_snv["start"],
        referenceBases=test_snv["referenceBases"],
        alternateBases=test_snv["alternateBases"],
        includeDatasetResponses="ALL",
    )

    # When calling the endpoing with the POST method
    response = mock_app.test_client().post("/apiv1.0/query_form", data=form_data)

    # Endpoint should NOT return error
    assert response.status_code == 200

    # And should display exists = true, af the dataset level
    assert "alert alert-success" in str(response.data)
    assert "exists&#39;: True" in str(response.data)


def test_query_form_post_snv_exact_coords_not_found(mock_app, test_snv, public_dataset):
    """Test the interactive query interface, snv, exact coordinates, allele not found"""

    # Having a database with a dataset but no variants
    database = mock_app.db
    database["dataset"].insert_one(public_dataset)

    form_data = dict(
        assemblyId=test_snv["assemblyId"],
        referenceName=test_snv["referenceName"],
        start=test_snv["start"],
        referenceBases=test_snv["referenceBases"],
        alternateBases=test_snv["alternateBases"],
        includeDatasetResponses="NONE",
    )

    # When calling the endpoing with the POST method
    response = mock_app.test_client().post("/apiv1.0/query_form", data=form_data)

    # Endpoint should NOT return error
    assert response.status_code == 200

    # And should display allele NOT found message
    assert "Allele could not be found" in str(response.data)


def test_query_form_post_SV_exact_coords_found(mock_app, test_sv, public_dataset):
    """Test the interactive query interface, sv, exact coordinates"""

    # Having a database with a structural variant:
    database = mock_app.db
    database["variant"].insert_one(test_sv)

    # And a dataset
    database["dataset"].insert_one(public_dataset)

    form_data = dict(
        assemblyId=test_sv["assemblyId"],
        referenceName=test_sv["referenceName"],
        start=test_sv["start"],
        end=test_sv["end"],
        referenceBases=test_sv["referenceBases"],
        variantType=test_sv["variantType"],
        includeDatasetResponses="NONE",
    )

    # When calling the endpoing with the POST method,
    response = mock_app.test_client().post("/apiv1.0/query_form", data=form_data)

    # Endpoint should NOT return error
    assert response.status_code == 200

    # And Allele found message should be displayed on the page
    assert "Allele was found in this beacon" in str(response.data)


def test_query_post_range_coords_SV_found(mock_app, test_sv, public_dataset):
    """Test the interactive query interface, sv, range coordinates"""

    # Having a database with a structural variant:
    database = mock_app.db
    database["variant"].insert_one(test_sv)

    # And a dataset
    database["dataset"].insert_one(public_dataset)

    start_min = test_sv["start"] - 5
    start_max = test_sv["start"] + 5
    end_min = test_sv["end"] - 5
    end_max = test_sv["end"] + 5

    # providing range coordinates in the form data
    form_data = dict(
        assemblyId=test_sv["assemblyId"],
        referenceName=test_sv["referenceName"],
        startMin=start_min,
        startMax=start_max,
        endMin=end_min,
        endMax=end_max,
        referenceBases=test_sv["referenceBases"],
        variantType=test_sv["variantType"],
        includeDatasetResponses="NONE",
    )

    # When calling the endpoing with the POST method,
    response = mock_app.test_client().post("/apiv1.0/query_form", data=form_data)

    # Endpoint should NOT return error
    assert response.status_code == 200

    # And Allele found message should be displayed on the page
    assert "Allele was found in this beacon" in str(response.data)


def test_post_query_error(mock_app, test_snv, public_dataset):
    """Test posting a query with errors, the servers should restuen error"""

    # Example, form data is missing wither alt base or variant type (one of them is mandatory)
    form_data = dict(
        assemblyId=test_snv["assemblyId"],
        referenceName=test_snv["referenceName"],
        start=test_snv["start"],
        end=test_snv["end"],
    )

    # When calling the endpoing with the POST method,
    response = mock_app.test_client().post("/apiv1.0/query_form", data=form_data)

    # Endpoint should retun a page
    assert response.status_code == 200

    # that displays the error
    assert "alert alert-danger" in str(response.data)
    assert "errorCode&#39;: 400" in str(response.data)
