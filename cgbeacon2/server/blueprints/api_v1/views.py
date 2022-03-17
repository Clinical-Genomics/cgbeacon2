# -*- coding: utf-8 -*-
import logging
import os
from threading import Thread

from cgbeacon2.__version__ import __version__
from cgbeacon2.constants import CHROMOSOMES, INVALID_TOKEN_AUTH
from cgbeacon2.models import Beacon
from cgbeacon2.utils.auth import authlevel, validate_token
from cgbeacon2.utils.parse import validate_add_params
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    render_template,
    request,
    send_from_directory,
)
from flask_negotiate import consumes

from .controllers import (
    add_variants_task,
    create_allele_query,
    delete_variants_task,
    dispatch_query,
    stats,
    validate_add_data,
    validate_delete_data,
)

API_VERSION = "1.0.0"
LOG = logging.getLogger(__name__)
api1_bp = Blueprint(
    "api_v1",
    __name__,
    template_folder="templates",
)


@api1_bp.route("/apiv1.0/img/<filename>")
def send_img(filename) -> Response:
    """Serve images to be displayed in web pages"""
    mimetype = "image/png"
    if filename.endswith(".svg"):
        mimetype = "image/svg+xml"
    return send_from_directory(
        os.path.join(current_app.root_path, "static"), filename, mimetype=mimetype
    )


@api1_bp.route("/", methods=["GET"])
@api1_bp.route("/apiv1.0/", methods=["GET"])
def info() -> Response:
    """Returns Beacon info data as a json object

    Example:
        curl -X GET 'http://localhost:5000/apiv1.0/'
        curl -X GET 'http://localhost:5000/'
    """
    beacon_config = current_app.config.get("BEACON_OBJ")
    beacon = Beacon(beacon_config, API_VERSION, current_app.db)

    resp = jsonify(beacon.introduce())
    resp.status_code = 200
    return resp


@api1_bp.route("/", methods=["GET", "POST"])
@api1_bp.route("/apiv1.0/query_form", methods=["GET", "POST"])
def query_form() -> str:
    """The endpoint to a simple query form to interrogate this beacon
    Query is performed only on public access datasets contained in this beacon

    query_form page is accessible from a browser at this address:
    http://127.0.0.1:5000/apiv1.0/query_form
    """

    all_dsets = current_app.db["dataset"].find()
    all_dsets = [ds for ds in all_dsets]
    resp_obj = {}

    if request.method == "POST":
        # Create database query object
        query = create_allele_query(resp_obj, request)

        if resp_obj.get("message") is not None:  # an error must have occurred
            flash(resp_obj["message"]["error"], "danger")

        else:  # query database
            # query database (it should return a datasetAlleleResponses object)
            response_type = resp_obj["allelRequest"].get("includeDatasetResponses", "NONE")
            query_datasets = resp_obj["allelRequest"].get("datasetIds", [])
            exists, ds_allele_responses = dispatch_query(query, response_type, query_datasets)
            resp_obj["exists"] = exists
            resp_obj["error"] = None
            resp_obj["datasetAlleleResponses"] = ds_allele_responses

            flash(resp_obj)

            flash_color = "secondary" if resp_obj["exists"] is False else "success"

            if len(resp_obj.get("datasetAlleleResponses", [])) > 0:
                # flash response from single datasets:
                for resp in resp_obj["datasetAlleleResponses"]:
                    if resp["exists"] is True:
                        flash(resp, flash_color)
                    else:
                        flash(resp, flash_color)
            elif resp_obj["exists"] is True:
                flash("Allele was found in this beacon", flash_color)
            else:
                flash("Allele could not be found", flash_color)

    return render_template(
        "queryform.html",
        chromosomes=CHROMOSOMES,
        dsets=all_dsets,
        software_version=__version__,
        stats=stats(),
        form=dict(request.form),
    )


@consumes("application/json")
@api1_bp.route("/apiv1.0/add", methods=["POST"])
def add() -> Response:
    """
    Endpoint accepting json data from POST requests. If request params are OK returns 200 (success).
    Then start a Thread that will save variants to database.

    Example:
    ########### POST request ###########
    curl -X POST \
    -H 'Content-Type: application/json' \
    -H 'X-Auth-Token: auth_token' \
    -d '{"dataset_id": "test_public",
    "vcf_path": "path/to/cgbeacon2/resources/demo/test_trio.vcf.gz",
    "samples" : ["ADM1059A1", "ADM1059A2"],
    "assemblyId": "GRCh37"}' http://localhost:5000/apiv1.0/add
    """
    resp = None
    # Check request auth token
    valid_token = validate_token(request, current_app.db)
    if valid_token is False:
        resp = jsonify({"message": INVALID_TOKEN_AUTH["errorMessage"]})
        resp.status_code = INVALID_TOKEN_AUTH["errorCode"]
        return resp

    # Check that request contains the required params
    validate_req = validate_add_params(request)
    if isinstance(validate_req, str):  # Validation failed
        resp = jsonify({"message": validate_req})
        resp.status_code = 422
        return resp

    # Check that request params are valid
    validate_req_data = validate_add_data(request)
    if isinstance(validate_req_data, str):  # Validation failed
        resp = jsonify({"message": validate_req_data})
        resp.status_code = 422
        return resp

    # Start loading variants thread
    Thread(target=add_variants_task(request)).start()

    # Return success response
    resp = jsonify({"message": "Saving variants to Beacon"})
    resp.status_code = 200
    return resp


@consumes("application/json")
@api1_bp.route("/apiv1.0/delete", methods=["DELETE"])
def delete() -> Response:
    """
    Endpoint accepting json data from POST requests. If request params are OK returns 200 (success).
    Then start a Thread that will delete variants from database.
    ########### POST request ###########
    curl -X DELETE \
    -H 'Content-Type: application/json' \
    -H 'X-Auth-Token: auth_token' \
    -d '{"dataset_id": "test_public",
    "samples" : ["ADM1059A1", "ADM1059A2"]' http://localhost:5000/apiv1.0/delete
    """
    resp = None
    # Check request auth token
    valid_token = validate_token(request, current_app.db)
    if valid_token is False:
        resp = jsonify({"message": INVALID_TOKEN_AUTH["errorMessage"]})
        resp.status_code = INVALID_TOKEN_AUTH["errorCode"]
        return resp

    # Check that request params are valid
    validate_req_data = validate_delete_data(request)
    if isinstance(validate_req_data, str):  # Validation failed
        resp = jsonify({"message": validate_req_data})
        resp.status_code = 422
        return resp

    # Start deleting variants thread
    Thread(target=delete_variants_task(request)).start()

    # Return success response
    resp = jsonify({"message": "Deleting variants from Beacon"})
    resp.status_code = 200
    return resp


@api1_bp.route("/apiv1.0/query", methods=["GET", "POST"])
def query() -> Response:
    """Create a query from params provided in the request and return a response with eventual results, or errors

    Examples:
    ########### GET request ###########
    curl -X GET \
    'http://localhost:5000/apiv1.0/query?referenceName=1&referenceBases=C&start=156146085&assemblyId=GRCh37&alternateBases=A'

    ########### POST request ###########
    curl -X POST \
    -H 'Content-Type: application/json' \
    -d '{"referenceName": "1",
    "start": 156146085,
    "referenceBases": "C",
    "alternateBases": "A",
    "assemblyId": "GRCh37",
    "includeDatasetResponses": "HIT"}' http://localhost:5000/apiv1.0/query
    """

    beacon_config = current_app.config.get("BEACON_OBJ")
    beacon_obj = Beacon(beacon_config, API_VERSION, current_app.db)

    resp_obj = {}
    resp_status = 200

    # Check request headers to define user access level
    # Public access only has auth_levels = ([], False)
    auth_levels = authlevel(request, current_app.config.get("ELIXIR_OAUTH2"))

    if isinstance(auth_levels, dict):  # an error must have occurred, otherwise it's a tuple
        resp = jsonify(auth_levels)
        resp.status_code = auth_levels.get("errorCode", 403)
        return resp

    # Create database query object
    query = create_allele_query(resp_obj, request)

    if resp_obj.get("message") is not None:
        # an error must have occurred
        resp_status = resp_obj["message"]["error"]["errorCode"]
        resp_obj["message"]["beaconId"] = beacon_obj.id
        resp_obj["message"]["apiVersion"] = API_VERSION

    else:
        resp_obj["beaconId"] = beacon_obj.id
        resp_obj["apiVersion"] = API_VERSION

        # query database (it should return a datasetAlleleResponses object)
        response_type = resp_obj["allelRequest"].get("includeDatasetResponses", "NONE")
        query_datasets = resp_obj["allelRequest"].get("datasetIds", [])
        exists, ds_allele_responses = dispatch_query(
            query, response_type, query_datasets, auth_levels
        )

        resp_obj["exists"] = exists
        resp_obj["error"] = None
        resp_obj["datasetAlleleResponses"] = ds_allele_responses

    resp = jsonify(resp_obj)
    resp.status_code = resp_status
    return resp
