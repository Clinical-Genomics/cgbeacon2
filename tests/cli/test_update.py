# -*- coding: utf-8 -*-
import responses  # for the sake of mocking it
from cgbeacon2.cli.commands import cli
from cgbeacon2.utils.ensembl_biomart import BIOMART_38

# Example of query runned on the EnsemblBiomartClient
XML_QUERY = """%3C?xml%20version=%221.0%22%20encoding=%22UTF-8%22?%3E%0A%3C!DOCTYPE%20Query%3E%0A%3CQuery%20%20virtualSchemaName%20=%20%22default%22%20formatter%20=%20%22TSV%22%20header%20=%20%220%22%20uniqueRows%20=%20%220%22%20count%20=%20%22%22%20datasetConfigVersion%20=%20%220.6%22%20completionStamp%20=%20%221%22%3E%0A%0A%09%3CDataset%20name%20=%20%22hsapiens_gene_ensembl%22%20interface%20=%20%22default%22%20%3E%0A%09%09%3CFilter%20name%20=%20%22chromosome_name%22%20value%20=%20%221,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,X,Y,MT%22/%3E%0A%09%09%3CAttribute%20name%20=%20%22ensembl_gene_id%22%20/%3E%0A%09%09%3CAttribute%20name%20=%20%22hgnc_id%22%20/%3E%0A%09%09%3CAttribute%20name%20=%20%22hgnc_symbol%22%20/%3E%0A%09%09%3CAttribute%20name%20=%20%22chromosome_name%22%20/%3E%0A%09%09%3CAttribute%20name%20=%20%22start_position%22%20/%3E%0A%09%09%3CAttribute%20name%20=%20%22end_position%22%20/%3E%0A%09%3C/Dataset%3E%0A%3C/Query%3E"""


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
    responses.add(responses.GET, url, body=response, status=200)

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
