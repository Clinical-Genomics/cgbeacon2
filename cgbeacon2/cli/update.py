#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import click
import types
from flask.cli import with_appcontext
from cgbeacon2.utils.ensembl_biomart import EnsemblBiomartClient
from cgbeacon2.utils.update import update_genes


@click.group()
def update():
    """Update items in the database using the cli"""
    pass


@update.command()
@with_appcontext
@click.option(
    "-build",
    type=click.Choice(["GRCh37", "GRCh38"]),
    nargs=1,
    help="Genome assembly (default:GRCh37)",
    default="GRCh37",
)
def genes(build):
    """Update genes and gene coordinates in database"""

    click.echo(f"Collecting gene names from EBI, genome build -> {build}")
    client = EnsemblBiomartClient(build)
    gene_lines = client.query_service()
    # If gene query was not successful, exit command
    if isinstance(gene_lines, types.GeneratorType) is False:
        click.echo(f"An error occurred while retrieving genes from Ensembl:{gene_lines}")
        return

    n_inserted = update_genes(gene_lines, build)
    click.echo(f"Number of inserted genes for build {build}: {len(n_inserted)}")