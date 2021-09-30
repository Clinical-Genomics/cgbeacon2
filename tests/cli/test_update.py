# -*- coding: utf-8 -*-
import responses  # for the sake of mocking it
from cgbeacon2.cli.commands import cli
from cgbeacon2.utils.ensembl_biomart import BIOMART_38, requests

XML_QUERY = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "TSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.6" completionStamp = "1">

	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Filter name = "chromosome_name" value = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,X,Y,MT"/>
		<Attribute name = "ensembl_gene_id" />
		<Attribute name = "hgnc_id" />
		<Attribute name = "hgnc_symbol" />
		<Attribute name = "chromosome_name" />
		<Attribute name = "start_position" />
		<Attribute name = "end_position" />
	</Dataset>
</Query>"""


@responses.activate
def test_update_genes_build_38(mock_app, database):
    """Test the cli command that downloads all genes for a genome build from Ensembl using Biomart"""

    # GIVEN client with a xml query for a gene
    build = "GRCh38"
    url = "".join([BIOMART_38, XML_QUERY])

    # GIVEN a mocked response from Ensembl Biomart
    response = (
        b"ENSG00000171314\tHGNC:8888\tPGAM1\t10\t97426191\t97433444\n"
        b"ENSG00000121236\tHGNC:16277\tTRIM6\t11\t5596109\t5612958\n"
        b"ENSG00000016391\tHGNC:24288\tCHDH\t3\t53812335\t53846419\n"
        b"ENSG00000232218\t\t\t22\t32386668\t32386868\n"
        b"[success]"
    )
    responses.add(responses.GET, url, body=response, status=200, stream=True, match_querystring=False)

    # test add a dataset_obj using the app cli
    runner = mock_app.test_cli_runner()

    # When invoking the update genes command
    result = runner.invoke(cli, ["update", "genes", "-build", build])

    # Then the command shouldn't return error
    assert result.exit_code == 0

    # And 3 genes should be found on database
    assert f"Number of inserted genes for build {build}: 3" in result.output
    genes = list(database["gene"].find())
    assert len(genes) == 3
