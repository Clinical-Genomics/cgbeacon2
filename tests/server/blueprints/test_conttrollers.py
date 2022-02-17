# -*- coding: utf-8 -*-
from cgbeacon2.server.blueprints.api_v1.controllers import add_coords_query, overlapping_samples


def test_add_coords_query_fuzzy_search():
    """test the function adding coordinates search to the allele database query"""
    mongo_query = {}

    # GIVEN an alt allele with Ns
    alt = "TTANGN"
    add_coords_query(mongo_query, "alternateBases", alt)
    assert mongo_query["alternateBases"] == {"$regex": alt.replace("N", ".")}


def test_overlapping_samples_overlap():
    """Test the functions that returns True if 2 lists of samples contain overlaps"""

    ds_samples = ["sample1", "sample2", "sample3"]
    req_samples = ["sample3"]
    assert overlapping_samples(ds_samples, req_samples) is True


def test_overlapping_samples_no_overlap():
    """Test the functions that returns True if 2 lists of samples contain overlaps. Should return false is lists don't overlap"""
    ds_samples = ["sample1", "sample2", "sample3"]
    req_samples = ["sample4"]
    assert overlapping_samples(ds_samples, req_samples) is False
