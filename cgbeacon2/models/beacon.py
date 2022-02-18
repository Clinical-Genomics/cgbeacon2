# -*- coding: utf-8 -*-
import datetime

import pymongo
from cgbeacon2 import __version__


class Beacon:
    """Represents a general beacon object"""

    def __init__(self, conf_obj, api_version="1.0.0", database=None) -> None:
        self.alternativeUrl = conf_obj.get("alternative_url")
        self.apiVersion = f"v{api_version}"
        self.createDateTime = self._date_event(database, True)
        self.updateDateTime = self._date_event(database, False)
        self.description = conf_obj.get("description")
        self.id = conf_obj.get("id")
        self.name = conf_obj.get("name")
        self.organisation = conf_obj.get("organisation")
        self.sampleAlleleRequests = self._sample_allele_requests()
        self.version = f"v{__version__}"
        self.welcomeUrl = conf_obj.get("welcome_url")
        self.datasets = self._datasets(database)
        self.datasets_by_auth_level = self._datasets_by_access_level(database)

    def _date_event(self, database, order_asc) -> datetime.datetime:
        """Return the date of the first event event created for this beacon

        Accepts:
            database(pymongo.database.Database)
            order_asc(bool): if True get first event else get last event

        Returns
            event.created(datetime.datetime): date of creation of the event
        """
        if database:
            if order_asc is True:
                order = pymongo.ASCENDING
            else:
                order = pymongo.DESCENDING

            events = database["event"].find().sort([("created", order)]).limit(1)
            for event in events:
                return event.get("created")

    def introduce(self) -> dict:
        """Returns a the description of this beacon, with the fields required by the / endpoint"""
        beacon_obj = self.__dict__
        beacon_obj.pop("datasets_by_auth_level")
        return beacon_obj

    def _datasets(self, database) -> list:
        """Retrieve all datasets associated to this Beacon

        Accepts:
            database(pymongo.database.Database)
        Returns:
            datasets(list)
        """
        if database is None:
            return []
        datasets = list(database["dataset"].find())
        for ds in datasets:
            if ds.get("samples") is not None:
                # return number of samples for each dataset, not sample names
                ds["sampleCount"] = len(ds.get("samples"))
                # return number of variants present for this dataset
                ds["variantCount"] = ds.get("variant_count")
                # return number of alleles present for this dataset
                ds["callCount"] = ds.get("allele_count")

            ds.pop("samples", None)
            ds.pop("variant_count", None)
            ds.pop("allele_count", None)

            ds["info"] = {"accessType": ds["authlevel"].upper()}
            ds.pop("authlevel")
            ds["id"] = ds["_id"]
            ds.pop("_id")

        return datasets

    def _datasets_by_access_level(self, database) -> dict:
        """Retrieve all datasets associated to this Beacon, by access level

        Accepts:
            database(pymongo.database.Database)
        Returns:
            datasets_by_level(dict): the keys are "public", "registered", "controlled"
        """
        datasets_by_level = dict(public={}, registered={}, controlled={})

        if database is None:
            return datasets_by_level

        datasets = database["dataset"].find()
        for ds in list(datasets):
            # add dataset as id=dataset_id, value=dataset to the dataset category
            datasets_by_level[ds["authlevel"]][ds["_id"]] = ds

        return datasets_by_level

    def _sample_allele_requests(self) -> list:
        """Returns a list of example allele requests"""

        examples = [
            {
                "alternateBases": "A",
                "referenceBases": "C",
                "referenceName": "1",
                "start": 156146085,
                "assemblyId": "GRCh37",
                "datasetIds": ["test_public"],
                "includeDatasetResponses": "HIT",
            },
            {
                "variantType": "DUP",
                "referenceBases": "C",
                "referenceName": "20",
                "start": 54963148,
                "assemblyId": "GRCh37",
                "includeDatasetResponses": "ALL",
            },
        ]
        return examples
