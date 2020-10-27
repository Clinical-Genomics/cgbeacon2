# -*- coding: utf-8 -*-

from cgbeacon2.models import Beacon


def test_beacon_model_no_db_connection(mock_app, public_dataset):
    """Test creating a beacon using the Beacon class with no database connection"""

    config_options = mock_app.config.get("BEACON_OBJ")
    beacon = Beacon(config_options)

    assert beacon.apiVersion == "v1.0.0"
    assert beacon.description == config_options["description"]
    assert beacon.id == config_options["id"]
    assert beacon.name == config_options["name"]
    assert beacon.datasets == []
    assert beacon.datasets_by_auth_level == dict(public={}, registered={}, controlled={})
