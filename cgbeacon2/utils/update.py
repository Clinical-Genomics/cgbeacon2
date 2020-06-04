# -*- coding: utf-8 -*-
import datetime
import logging

LOG = logging.getLogger(__name__)


def update_dataset(database, dataset_id, samples, add):
    """Update dataset object in dataset collection after adding or removing variants

    Accepts:
        database(pymongo.database.Database)
        dataset_id(str): id of dataset to be updated
        samples(list): list of samples to be added to/removed from dataset
        add(bool): whether the samples should be added or removed from dataset
    """
    dataset_obj = database["dataset"].find_one({"_id": dataset_id})

    # update list of samples for this dataset
    updated_samples = update_dataset_samples(dataset_obj, samples, add)

    # update variants count for this dataset
    n_variants = update_dataset_variant_count(database, dataset_id)

    # Update number of allele calls for this dataset
    n_alleles = update_dataset_allele_count(database, dataset_obj)

    result = database["dataset"].find_one_and_update(
        {"_id": dataset_id},
        {
            "$set": {
                "samples": list(updated_samples),
                "variant_count": n_variants,
                "allele_count": n_alleles,
                "updated": datetime.datetime.now(),
            }
        },
    )
    return result


def update_dataset_samples(dataset_obj, samples, add=True):
    """Update the list of samples for a dataset

    Accepts:
        dataset_obj(dict): a dataset object
        samples(list): list of samples to be added to/removed from dataset
        add(bool): whether the samples should be added or removed from dataset

    Returns:
        datasets_samples(list): the updated list of samples
    """
    datasets_samples = set(dataset_obj.get("samples", []))

    for sample in samples:  # add new samples to dataset
        if add is True:
            datasets_samples.add(sample)
        else:
            datasets_samples.remove(sample)

    LOG.info(f"Updated dataset contains {len(datasets_samples)} samples")
    return datasets_samples


def update_dataset_variant_count(database, dataset_id):
    """Count how many variants there are for a dataset and update dataset object with this number

    Accepts:
        database(pymongo.database.Database)
        dataset_id(str): id of dataset to be updated

    Returns:
        n_variants(int): the number of variants with calls for this dataset
    """

    variant_collection = database["variant"]
    # Get all variants present with calls for this dataset
    query = {".".join(["datasetIds", dataset_id]): {"$exists": True}}
    n_variants = sum(1 for i in variant_collection.find(query))

    LOG.info(f"Updated dataset contains {n_variants} variants")
    return n_variants


def update_dataset_allele_count(database, dataset_obj):
    """Count how many allele calls are present for a dataset and update dataset object with this number

    Accepts:
        database(pymongo.database.Database)
        dataset_obj(dict): a dataset object

    Returns:
        updated_dataset(obj): the updated dataset
    """
    allele_count = 0
    variant_collection = database["variant"]

    n_beacon_datasets = sum(1 for i in database["dataset"].find())

    # If beacon contains only one dataset, then allele count is the sum of allele count for each variant
    if n_beacon_datasets == 1:
        pipe = [{"$group": {"_id": None, "alleles": {"$sum": "$call_count"}}}]
        aggregate_res = variant_collection.aggregate(pipeline=pipe)
        for res in aggregate_res:
            allele_count += res.get("alleles")

        # Else count calls for each sample of this dataset in variant collection and sum them up
        else:
            allele_count = _samples_calls(variant_collection, dataset_obj)

    return allele_count


def _samples_calls(variant_collection, dataset_obj):
    """Count all allele calls for a dataset in variants collection

    Accepts:
        variant_collection(pymongo.database.Database.Collection)
        dataset_obj(dict): a dataset object
    Returns:

    """
    allele_count = 0
    samples = dataset_obj.get("samples", [])

    for sample in samples:
        pipe = [
            {
                "$group": {
                    "_id": None,
                    "alleles": {
                        "$sum": f"$datasetIds.test_public.samples.{sample}.allele_count"
                    },
                }
            }
        ]
        aggregate_res = variant_collection.aggregate(pipeline=pipe)
        for res in aggregate_res:
            allele_count += res.get("alleles")

    return allele_count
