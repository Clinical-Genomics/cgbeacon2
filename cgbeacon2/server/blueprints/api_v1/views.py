# -*- coding: utf-8 -*-
import logging
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    render_template,
    flash,
    redirect,
)
from flask_negotiate import consumes
from cgbeacon2.constants import CHROMOSOMES
from cgbeacon2.models import Beacon
from cgbeacon2.utils.auth import authlevel
from cgbeacon2.utils.parse import validate_add_request
from .controllers import create_allele_query, dispatch_query

API_VERSION = "1.0.0"
LOG = logging.getLogger(__name__)
api1_bp = Blueprint(
    "api_v1",
    __name__,
    static_folder="static",
    template_folder="templates",
    static_url_path="/api_v1/static",
)


@api1_bp.route("/apiv1.0/", methods=["GET"])
def info():
    """Returns Beacon info data as a json object

    Example:
        curl -X GET 'http://localhost:5000/apiv1.0/'

    """

    beacon_config = current_app.config.get("BEACON_OBJ")
    beacon = Beacon(beacon_config, API_VERSION, current_app.db)

    resp = jsonify(beacon.introduce())
    resp.status_code = 200
    return resp


@api1_bp.route("/apiv1.0/query_form", methods=["GET", "POST"])
def query_form():
    """The endpoint to a super simple query form to interrogate this beacon
    Query is performed only on public access datasets contained in this beacon

    query_form page is accessible from a browser at this address:
    http://127.0.0.1:5000/apiv1.0/query_form
    """

    all_dsets = current_app.db["dataset"].find()
    all_dsets = [ds["_id"] for ds in all_dsets]
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

            if resp_obj["exists"] == False:
                flash_color = "secondary"

            if len(resp_obj.get("datasetAlleleResponses", [])) > 0:
                # flash response from single datasets:
                for resp in resp_obj["datasetAlleleResponses"]:
                    if resp["exists"] is True:
                        flash(resp, "success")
                    else:
                        flash(resp, "secondary")
            elif resp_obj["exists"] is True:
                flash("Allele was found in this beacon", "success")
            else:
                flash("Allele could not be found", "secondary")

    return render_template(
        "queryform.html",
        chromosomes=CHROMOSOMES,
        dsets=all_dsets,
        form=dict(request.form),
    )


@consumes("application/json")
@api1_bp.route("/apiv1.0/", methods=["POST"])
def add():
    """Endpoint accepting json data from POST requests. Save variants from a VCF file according to params specified in the request."""
    # validate request content:
    validate_request = validate_add_request(request)
    return str(validate_request)


@api1_bp.route("/apiv1.0/query", methods=["GET", "POST"])
def query():
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
