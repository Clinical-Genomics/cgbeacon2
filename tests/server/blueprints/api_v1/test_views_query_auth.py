# -*- coding: utf-8 -*-
import copy
import json

import pytest
from authlib.jose import jwt
from authlib.jose.errors import ExpiredTokenError
from cgbeacon2.constants import (
    EXPIRED_TOKEN_SIGNATURE,
    INVALID_TOKEN_CLAIMS,
    MISSING_PUBLIC_KEY,
    MISSING_TOKEN,
    MISSING_TOKEN_CLAIMS,
    NO_GA4GH_USERDATA,
    PASSPORTS_ERROR,
    WRONG_SCHEME,
)
from cgbeacon2.utils import auth

HEADERS = {"Content-type": "application/json", "Accept": "application/json"}

API_QUERY = "/apiv1.0/query?"
BEARER = "Bearer "


def test_post_request_wrong_token_no_token(mock_app):
    """test receiving a post request with Auth headers but not token"""

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = ""

    # When a POST request Authorization="" is sent
    response = mock_app.test_client().post(API_QUERY, headers=headers)

    # Then it should return unauthorized error 401
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data["errorMessage"] == MISSING_TOKEN["errorMessage"]


def test_post_request_wrong_token_null_token(mock_app):
    """test receiving a post request with Auth headers and wrong scheme"""

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER

    # When a POST request Authorization="" is sent
    response = mock_app.test_client().post(API_QUERY, headers=headers)

    # Then it should return unauthorized error 401
    assert response.status_code == 401
    data = json.loads(response.data)

    assert data["errorMessage"] == MISSING_TOKEN["errorMessage"]


def test_post_request_wrong_token_wrong_scheme(mock_app, test_token):
    """test receiving a post request with Auth headers and wrong scheme"""

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = "Basic " + test_token

    # When a POST request Authorization="" is sent
    response = mock_app.test_client().post(API_QUERY, headers=headers)

    # Then it should return unauthorized error 401
    assert response.status_code == 401
    data = json.loads(response.data)

    assert data["errorMessage"] == WRONG_SCHEME["errorMessage"]


def test_validate_test_token(test_token, pem):
    """Test validate demo token"""

    # Having a test token
    assert test_token

    # Decoding it
    claims = jwt.decode(test_token, pem)
    claims.validate()


def test_validate_expired_token(expired_token, pem):
    """Perform validation on an expired token"""

    # When a token is expired
    assert expired_token
    claims = jwt.decode(expired_token, pem)

    # Validate token should raise specific
    with pytest.raises(ExpiredTokenError) as excinfo:
        claims.validate()
    assert excinfo.match(r"The token is expired")


def test_post_request_expired_token(mock_app, expired_token, pem, monkeypatch):
    """test receiving a POST request containing an expired token"""

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + expired_token

    # When the beacon receives a request with this token
    response = mock_app.test_client().post(API_QUERY, headers=headers)
    data = json.loads(response.data)

    # Should return expired token error
    assert response.status_code == 403
    assert data == EXPIRED_TOKEN_SIGNATURE


def test_post_request_wrong_issuers_token(mock_app, wrong_issuers_token, pem, monkeypatch):
    """test receiving a POST request containing a token with wrong issuers"""

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + wrong_issuers_token

    # When a POST request with a token with wrong issuers is sent
    response = mock_app.test_client().post(API_QUERY, headers=headers)
    data = json.loads(response.data)
    # it should return invalid token claims error
    assert response.status_code == 403
    assert data == INVALID_TOKEN_CLAIMS


def test_post_request_missing_claims_token(mock_app, no_claims_token, pem, monkeypatch):
    """test receiving a POST request containing a token with no claims"""

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + no_claims_token

    # When a POST request with a token with missing claims
    response = mock_app.test_client().post(API_QUERY, headers=headers)
    data = json.loads(response.data)

    # it should return missing claims error
    assert response.status_code == 403
    assert data == MISSING_TOKEN_CLAIMS


def test_post_request_missing_public_key(mock_app, test_token, monkeypatch, mock_oauth2):
    """test receiving a post request with a token when the public key to decode it is available"""

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + test_token

    mock_app.config["ELIXIR_OAUTH2"] = mock_oauth2

    # When a POST request with token is sent, but public key is not available
    response = mock_app.test_client().post(API_QUERY, headers=headers)
    data = json.loads(response.data)

    # it should return missing public key error
    assert response.status_code == 403
    assert data == MISSING_PUBLIC_KEY


def test_post_request_invalid_token_signature(mock_app, pem, monkeypatch, basic_query):
    """test receiving a POST request containing a token that triggers the InvalidTokenError"""

    # generate a random token not using the test public key
    wrong_token = jwt.encode({"alg": "HS256"}, {"aud": ["foo", "bar"]}, "k").decode("utf-8")
    assert wrong_token

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + wrong_token

    # When a POST request with the wrong token is sent
    response = mock_app.test_client().post(API_QUERY, headers=headers, data=json.dumps(basic_query))
    data = json.loads(response.data)

    # it should return bad signature error
    assert response.status_code == 403
    assert "bad_signature" in data["errorMessage"]


def test_post_request_token_no_oidc(
    mock_app, test_token, pem, monkeypatch, basic_query, mock_oauth2
):
    """Test receiving a POST request with valid token, but a non-valid OIDC is set"""

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + test_token

    mock_app.config["ELIXIR_OAUTH2"]["userinfo"] = mock_oauth2["userinfo"]

    # When a POST request with a valid token, but in absence of OIDC provider is sent
    response = mock_app.test_client().post(API_QUERY, headers=headers, data=json.dumps(basic_query))
    data = json.loads(response.data)

    # it should return a 403 error
    assert response.status_code == 403
    # With OIDC unreachable error
    assert data == NO_GA4GH_USERDATA


def test_post_request_token_passports_error(mock_app, test_token, pem, monkeypatch, mock_oauth2):
    """Test receiving POST request with valid token but in the absence of a valid server returning valid passport JWTs"""

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    def mock_ga4gh_userdata(*args, **kwargs):
        # OIDC provider returning non-canonical response
        return {"foo": "bar"}

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)

    # And OIDC provider is mocked
    monkeypatch.setattr(auth, "ga4gh_userdata", mock_ga4gh_userdata)

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + test_token

    mock_app.config["ELIXIR_OAUTH2"]["userinfo"] = mock_oauth2["userinfo"]

    # When a POST request with a valid token is sent
    response = mock_app.test_client().post(API_QUERY, headers=headers)
    data = json.loads(response.data)

    # it should return the specific 403 passports error
    assert response.status_code == 403
    assert data == PASSPORTS_ERROR


def test_post_request_token_ok_oidc(
    mock_app, test_token, pem, monkeypatch, basic_query, mock_oauth2
):
    """Test receiving a POST request with valid token, valid userdata passports"""

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    def mock_ga4gh_userdata(*args, **kwargs):
        pass

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)
    # And OIDC provider is mocked
    monkeypatch.setattr(auth, "ga4gh_userdata", mock_ga4gh_userdata)

    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + test_token

    mock_app.config["ELIXIR_OAUTH2"]["userinfo"] = mock_oauth2["userinfo"]

    # When a POST request with a valid token is sent
    response = mock_app.test_client().post(API_QUERY, headers=headers, data=json.dumps(basic_query))

    # it should return a valid response
    assert response.status_code == 200


def test_post_query_registered_dataset_no_token(
    mock_app, registered_dataset, test_snv, basic_query
):
    """Test the case when the variant is from a registered dataset and the query has no token"""

    # Having a database containing a dataset with registered access protection
    database = mock_app.db
    registered_dataset["samples"] = ["ADM1059A1"]
    database["dataset"].insert_one(registered_dataset)

    # And a variant from the same dataset
    test_snv["datasetIds"] = {registered_dataset["_id"]: {"samples": registered_dataset["samples"]}}
    database["variant"].insert_one(test_snv)

    # When a POST request is sent without auth token
    response = mock_app.test_client().post(API_QUERY, headers=HEADERS, data=json.dumps(basic_query))
    data = json.loads(response.data)
    # it should return a valid response
    assert response.status_code == 200
    # But the variant should NOT be found
    assert data["exists"] is False


def test_post_query_registered_dataset_registered_token(
    mock_app,
    registered_dataset,
    test_snv,
    basic_query,
    test_token,
    mock_oauth2,
    monkeypatch,
    pem,
    registered_access_passport_info,
):
    """Test post query from a user that has access to a registered dataset on this beacon"""

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    def mock_ga4gh_userdata(*args, **kwargs):
        return registered_access_passport_info

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)
    # And OIDC provider is mocked
    monkeypatch.setattr(auth, "ga4gh_userdata", mock_ga4gh_userdata)

    # Having a database containing a dataset with registered access protection
    database = mock_app.db
    registered_dataset["samples"] = ["ADM1059A1"]
    database["dataset"].insert_one(registered_dataset)

    # And a variant from the same dataset
    test_snv["datasetIds"] = {registered_dataset["_id"]: {"samples": registered_dataset["samples"]}}
    database["variant"].insert_one(test_snv)

    # When a POST request with a valid token is sent
    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + test_token
    mock_app.config["ELIXIR_OAUTH2"]["userinfo"] = mock_oauth2["userinfo"]

    response = mock_app.test_client().post(API_QUERY, headers=headers, data=json.dumps(basic_query))

    # it should return a valid response
    assert response.status_code == 200
    data = json.loads(response.data)
    # And the beacon response would be Found=Yes
    assert data["exists"] is True


def test_post_query_controlled_dataset_no_token(
    mock_app, controlled_dataset, test_snv, basic_query
):
    """Test the case when the variant is from a controlled dataset and the query has no token"""

    # Having a database containing a dataset with registered access protection
    database = mock_app.db
    controlled_dataset["samples"] = ["ADM1059A1"]
    database["dataset"].insert_one(controlled_dataset)

    # And a variant from the same dataset
    test_snv["datasetIds"] = {controlled_dataset["_id"]: {"samples": controlled_dataset["samples"]}}
    database["variant"].insert_one(test_snv)

    # When a POST request is sent without auth token
    response = mock_app.test_client().post(API_QUERY, headers=HEADERS, data=json.dumps(basic_query))
    data = json.loads(response.data)
    # it should return a valid response
    assert response.status_code == 200
    # But the variant should NOT be found
    assert data["exists"] is False


def test_post_query_controlled_dataset_bona_fide_token(
    mock_app,
    controlled_dataset,
    test_snv,
    basic_query,
    test_token,
    mock_oauth2,
    monkeypatch,
    pem,
    bona_fide_passport_info,
):
    """Test post query from a bona fide user that has access to a controlled dataset on this beacon"""

    # Monkeypatch Elixir JWT server public key
    def mock_public_server(*args, **kwargs):
        return pem

    def mock_ga4gh_userdata(*args, **kwargs):
        return bona_fide_passport_info

    # Elixir key is not collected from elixir server, but mocked
    monkeypatch.setattr(auth, "elixir_key", mock_public_server)
    # And OIDC provider is mocked
    monkeypatch.setattr(auth, "ga4gh_userdata", mock_ga4gh_userdata)

    # Having a database containing a dataset with controlled access protection
    database = mock_app.db
    controlled_dataset["samples"] = ["ADM1059A1"]
    database["dataset"].insert_one(controlled_dataset)

    # And a variant from the same dataset
    test_snv["datasetIds"] = {controlled_dataset["_id"]: {"samples": controlled_dataset["samples"]}}
    database["variant"].insert_one(test_snv)

    # When a POST request with a valid token is sent
    headers = copy.deepcopy(HEADERS)
    headers["Authorization"] = BEARER + test_token
    mock_app.config["ELIXIR_OAUTH2"]["userinfo"] = mock_oauth2["userinfo"]
    mock_app.config["ELIXIR_OAUTH2"][
        "bona_fide_requirements"
    ] = "https://doi.org/10.1038/s41431-018-0219-y"

    response = mock_app.test_client().post(API_QUERY, headers=headers, data=json.dumps(basic_query))

    # it should return a valid response
    assert response.status_code == 200
    data = json.loads(response.data)
    # And the beacon response would be Found=Yes
    assert data["exists"] is True
