# -*- coding: utf-8 -*-
import logging
from progress.bar import Bar

from cgbeacon2.constants import CHROMOSOMES
from cgbeacon2.models.variant import Variant
from cgbeacon2.utils.parse import variant_called

LOG = logging.getLogger(__name__)


def add_dataset(database, dataset_dict, update=False):
    """Add/modify a dataset

    Accepts:
        database(pymongo.database.Database)
        dataset_dict(dict)

    Returns:
        inserted_id(str): the _id of the added/updated dataset
    """
    collection = "dataset"

    if update is True:  # update an existing dataset
        # LOG.info(f"Updating dataset collection with dataset id: {id}..")
        old_dataset = database[collection].find_one({"_id": dataset_dict["_id"]})

        if old_dataset is None:
            LOG.fatal(
                "Couldn't find any dataset with id '{}' in the database".format(
                    dataset_dict["_id"]
                )
            )
            return
        dataset_dict["created"] = old_dataset["created"]
        result = database[collection].replace_one(
            {"_id": dataset_dict["_id"]}, dataset_dict
        )
        if result.modified_count > 0:
            return dataset_dict["_id"]
        else:
            return
    try:
        result = database[collection].insert_one(dataset_dict)

    except Exception as err:
        LOG.error(err)
        return

    return result.inserted_id


def add_variants(database, vcf_obj, samples, assembly, dataset_id, nr_variants):
    """Build variant objects from a cyvcf2 VCF iterator

    Accepts:
        database(pymongo.database.Database)
        vcf_obj(cyvcf2.VCF): a VCF object
        samples(set): set of samples to add variants for
        assembly(str): chromosome build
        dataset_id(str): dataset id
        nr_variant(int): number of variants contained in VCF file
    Returns:
        inserted_vars, samples(tuple): (int,list)

    """
    LOG.info("Parsing variants..\n")
    new_samples = set()

    # Collect position to check genotypes for (only samples provided by user)
    gt_positions = []
    for i, sample in enumerate(vcf_obj.samples):
        if sample in samples:
            gt_positions.append(i)

    vcf_samples = vcf_obj.samples

    inserted_vars = 0
    with Bar("Processing", max=nr_variants) as bar:
        for vcf_variant in vcf_obj:
            if vcf_variant.CHROM not in CHROMOSOMES:
                LOG.warning(
                    f"chromosome '{vcf_variant.CHROM}' not included in canonical chromosome list, skipping it."
                )
                continue

            # Check if variant was called in provided samples
            sample_calls = variant_called(
                vcf_samples, gt_positions, vcf_variant.gt_types
            )

            if sample_calls == {}:
                continue  # variant was not called in samples of interest

            parsed_variant = dict(
                chromosome=vcf_variant.CHROM,
                start=vcf_variant.start - 1,
                end=vcf_variant.end - 1,
                reference_bases=vcf_variant.REF,
                alternate_bases=vcf_variant.ALT,
            )

            if vcf_variant.var_type == "sv":
                parsed_variant["variant_type"] = vcf_variant.INFO["SVTYPE"]

            dataset_dict = {dataset_id: {"samples": sample_calls}}
            # Create standard variant object with specific _id
            variant = Variant(parsed_variant, dataset_dict, assembly)

            # Load variant into database or update an existing one with new samples and dataset
            result = add_variant(
                database=database, variant=variant, dataset_id=dataset_id
            )
            if result is not None:
                inserted_vars += 1

            bar.next()

    return inserted_vars


def add_variant(database, variant, dataset_id):
    """Check if a variant is already in database and update it, otherwise add a new one

    Accepts:
        database(pymongo.database.Database)
        variant(cgbeacon2.models.Variant)
        dataset_id(str): current dataset in use

    Returns:
        result.inserted_id or updated variant allele_count

    """
    # check if variant already exists
    old_variant = database["variant"].find_one({"_id": variant._id})
    current_samples = variant.datasetIds[dataset_id][
        "samples"
    ]  # {sample1: allele_count, sample2:allele_count}
    if old_variant is None:  # if it doesn't exist
        # insert variant into database
        variant.call_count = sum(current_samples.values())
        result = database["variant"].insert_one(variant.__dict__)
        return result.inserted_id

    else:  # update pre-existing variant
        updated_datasets = old_variant.get(
            "datasetIds", {}
        )  # dictionary where dataset ids are keys
        allele_count = 0
        if dataset_id in updated_datasets:  # variant was already found in this dataset
            updated_samples = updated_datasets[dataset_id]["samples"]
            for sample, value in current_samples.items():
                if sample not in updated_samples:
                    updated_samples[sample] = value
                    allele_count += value
            updated_datasets[dataset_id] = updated_samples
        else:
            updated_datasets[dataset_id] = current_samples
            allele_count = sum(current_samples.values())

        if allele_count > 0:  # changes in sample, allele count dictionary must be saved
            result = database["variant"].find_one_and_update(
                {"_id": old_variant["_id"]},
                {
                    "$set": {
                        "datasetIds": updated_datasets,  # this is actually updated now
                        "call_count": old_variant["call_count"] + allele_count,
                    }
                },
            )
            return allele_count
