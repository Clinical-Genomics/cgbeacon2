#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import datetime
from flask.cli import with_appcontext, current_app

from cgbeacon2.constants import CONSENT_CODES
from cgbeacon2.models.user import User
from cgbeacon2.utils.add import add_dataset, add_variants, add_user
from cgbeacon2.utils.parse import (
    extract_variants,
    count_variants,
    merge_intervals,
    get_vcf_samples,
)
from cgbeacon2.utils.update import update_dataset, update_event


@click.group()
def add():
    """Add items to database using the CLI"""
    pass


@add.command()
@click.option("-id", type=click.STRING, nargs=1, required=True, help="User ID")
@click.option("-name", type=click.STRING, nargs=1, required=True, help="User name")
@click.option("-desc", type=click.STRING, nargs=1, required=False, help="User description")
@click.option("-url", type=click.STRING, nargs=1, required=False, help="User url")
@with_appcontext
def user(id, name, desc, url):
    """Creates a new user for adding/removing variants using the REST API"""

    if " " in id:
        click.echo("User ID should not contain any space")
        return
    user_info = dict(_id=id, name=name, description=desc, url=url, created=datetime.datetime.now())
    user = User(user_info)
    add_user(current_app.db, user)


@add.command()
@with_appcontext
@click.pass_context
def demo(ctx):
    """Loads demo data into the database:
    A test dataset with public access (genome assembly GRCh37)
    Demo SNV variants filtered using a demo gene panel
    Demo SV variants
    """

    # Dropping any existing database collection from demo database
    collections = current_app.db.collection_names()
    click.echo(f"\n\nDropping the following collections:{ ','.join(collections) }")
    for collection in collections:
        current_app.db.drop_collection(collection)

    # Creating public dataset
    ds_id = "test_public"
    ds_name = "Test public dataset"
    authlevel = "public"
    sample = "ADM1059A1"

    # Invoke add dataset command
    ctx.invoke(dataset, id=ds_id, name=ds_name, authlevel=authlevel)

    # Invoke add variants command to import all SNV variants from demo sample
    ctx.invoke(
        variants, ds=ds_id, vcf="cgbeacon2/resources/demo/test_trio.vcf.gz", sample=[sample],
    )

    # Invoke add variants command to import all SV variants from demo sample
    ctx.invoke(
        variants, ds=ds_id, vcf="cgbeacon2/resources/demo/test_trio.SV.vcf.gz", sample=[sample],
    )

    # Invoke add variants command to import also BND variants from separate VCF file
    ctx.invoke(
        variants, ds=ds_id, vcf="cgbeacon2/resources/demo/BND.SV.vcf", sample=[sample],
    )


@add.command()
@click.option("-id", type=click.STRING, nargs=1, required=True, help="dataset ID")
@click.option("-name", type=click.STRING, nargs=1, required=True, help="dataset name")
@click.option(
    "-build",
    type=click.Choice(["GRCh37", "GRCh38"]),
    nargs=1,
    help="Genome assembly (default:GRCh37)",
    default="GRCh37",
)
@click.option(
    "-authlevel",
    type=click.Choice(["public", "registered", "controlled"], case_sensitive=False),
    help="the access level of this dataset",
    required=True,
)
@click.option("-desc", type=click.STRING, nargs=1, required=False, help="dataset description")
@click.option(
    "-version", type=click.FLOAT, nargs=1, required=False, help="dataset version, i.e. 1.0",
)
@click.option("-url", type=click.STRING, nargs=1, required=False, help="external url")
@click.option("-cc", type=click.STRING, nargs=1, required=False, help="consent code key. i.e. HMB")
@click.option("--update", is_flag=True)
@with_appcontext
def dataset(id, name, build, authlevel, desc, version, url, cc, update):
    """Creates a dataset object in the database or updates a pre-existing one"""

    dataset_obj = {"_id": id, "name": name, "assembly_id": build}

    if update is True:
        dataset_obj["updated"] = datetime.datetime.now()
    else:
        dataset_obj["created"] = datetime.datetime.now()

    dataset_obj["authlevel"] = authlevel

    if desc is not None:
        dataset_obj["description"] = desc

    if version is not None:
        dataset_obj["version"] = version
    else:
        dataset_obj["version"] = 1.0

    if url is not None:
        dataset_obj["external_url"] = url

    if cc is not None:
        # This can be improved, doesn't consider Codes with XX yet
        # Make sure consent code is among is an official consent code
        if cc not in CONSENT_CODES:
            click.echo(
                "Consent code seem to have a non-standard value. Accepted consent code values:"
            )
            count = 1
            for code, item in CONSENT_CODES.items():
                click.echo(f'{count})\t{item["abbr"]}\t{item["name"]}\t{item["description"]}')
                count += 1
            raise click.Abort()

        dataset_obj["consent_code"] = cc

    inserted_id = add_dataset(database=current_app.db, dataset_dict=dataset_obj, update=update)

    if inserted_id:
        click.echo(f"Dataset collection was successfully updated with dataset '{inserted_id}'")
        # register the event in the event collection
        update_event(current_app.db, id, "dataset", True)
    else:
        click.echo("An error occurred while updating dataset collection")


@add.command()
@click.option("-ds", type=click.STRING, nargs=1, required=True, help="dataset ID")
@click.option("-vcf", type=click.Path(exists=True), required=True)
@click.option(
    "-sample",
    type=click.STRING,
    multiple=True,
    required=True,
    help="one or more samples to save variants for",
)
@click.option(
    "-panel",
    type=click.Path(exists=True),
    multiple=True,
    required=False,
    help="one or more bed files containing genomic intervals",
)
@with_appcontext
def variants(ds, vcf, sample, panel):
    """Add variants from a VCF file to a dataset"""
    # make sure dataset id corresponds to a dataset in the database

    dataset = current_app.db["dataset"].find_one({"_id": ds})
    if dataset is None:
        click.echo(f"Couldn't find any dataset with id '{ds}' in the database")
        raise click.Abort()

    # Check if required sample(s) are contained in the VCF
    vcf_samples = get_vcf_samples(vcf)

    if not all(samplen in vcf_samples for samplen in sample):
        click.echo(
            f"One or more provided sample was not found in the VCF file. Valida samples are: { ','.join(vcf_samples)}"
        )
        raise click.Abort()
    custom_samples = set(sample)  # set of samples provided by users

    filter_intervals = None
    if len(panel) > 0:
        # create BedTool panel with genomic intervals to filter VCF with
        filter_intervals = merge_intervals(list(panel))

    vcf_obj = extract_variants(vcf_file=vcf, samples=custom_samples, filter=filter_intervals)

    if vcf_obj is None:
        raise click.Abort()

    nr_variants = count_variants(vcf_obj)
    if nr_variants == 0:
        click.echo("Provided VCF file doesn't contain any variant")
        raise click.Abort()

    vcf_obj = extract_variants(vcf_file=vcf, samples=custom_samples, filter=filter_intervals)

    # ADD variants
    added = add_variants(
        database=current_app.db,
        vcf_obj=vcf_obj,
        samples=custom_samples,
        assembly=dataset["assembly_id"],
        dataset_id=ds,
        nr_variants=nr_variants,
    )
    click.echo(f"{added} variants loaded into the database")

    if added > 0:
        # Update dataset object accordingly
        update_dataset(database=current_app.db, dataset_id=ds, samples=custom_samples, add=True)
