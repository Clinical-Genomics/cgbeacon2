
## Adding data to the database

Dataset and variant data can be loaded into the database using specific the specific command line. To visualize command line options, from the terminal you can user the following command: `beacon --help`.

The default procedure to add variants to the beacon is always the following:

- Create a dataset to link your variants to.
- Load variants from a VCF file for one or more samples, specifying which dataset these variants belong to.

## How to add:
1. [ Demo data ](#demodata)
1. [ Gene data ](#genes)
1. [ Creating an authorized user for using the APIs](#user)
1. [ A new dataset (custom data)](#dataset)
1. [ Variants (custom data) using the command line](#variants_cli)
1. [ Variants (custom data) using the REST API](#variants_api)


<a name="demodata"></a>
## Demo data
Demo data consisting in a test dataset with public access and a set of variants (SNVs and structural variants of different type) is available under the cgbeacon2/resources/demo folder. You don't need to load this data manually since the following command will take care of everything:
```
beacon add demo
```

<a name="genes"></a>
## Adding/updating gene data
In order to accept add variants requests containing the `genes` option, the database should be pre-populated with gene data. VCF files can in fact be filtered by genes only if gene information containing chromosome, start and stop coordinates are already available when the variants load command is executed.

To load genes into database or to update the database gene collection, run the following command:
```
beacon update genes

Options:
  -build [GRCh37|GRCh38]  Genome assembly (default:GRCh37)
```

<a name="user"></a>
### Creating an authorized user for using the APIs
An API user is required whenever variants are by sending a request to the Beacon API.
One or more API users can be created using the command:
```
beacon add user


Options:
  --uid TEXT    User ID  [required]
  --name TEXT  User name  [required]
  --desc TEXT  User description
  --url TEXT   User url
  --help      Show this message and exit.
```
Once a user is created, a random user token will be created in the database for this user.


<a name="dataset"></a>
## Adding a new dataset
A new dataset can be created with the following command:
```
beacon add dataset --did <dataset_id> --name <"A dataset name"> --build <GRCh37|GRCh38> --authlevel <public|registered|controlled>
```
The above parameters (ds-id, name, build, authlevel) are mandatory. If user doesn't specify any genome build then the default build used is GRCh37. One dataset can be associated to variants called using only one genome build.
`authlevel` parameter will be used in queries to return results according to the request authentication level.

- **Public datasets** can be interrogated by any beacon and any user in general and should not be used to store sensitive data such as individual phenotypes.
- **Bona fide researchers** logged in via the Elixir AAI will be able to access data store in **registered datasets**.
- **Controlled access datasets** might be used to store sensitive information and will be accessed only by users that have a signed agreement and their access approved by a Data Access Committee (DAC).


More info about the Elixir AAI authentication is available [here](https://elixir-europe.org/services/compute/aai)

Other optional parameters that can be provided to improve the dataset description are the following.
```
  --desc TEXT                      dataset description
  --version FLOAT                  dataset version, i.e. 1.0
  --url TEXT                       external url
  --cc TEXT                        consent code key. i.e. HMB
  --update
```
The `--update` flag will allow to modify the information for a dataset that is already existing in the database.



<a name="variants_cli"></a>
## Adding variant data using the command line
Variant data can be loaded to the database using the following command:

```
beacon add variants

Options:
  --ds TEXT      dataset ID  [required]
  --vcf PATH     [required]
  --sample TEXT  one or more samples to save variants for  [required]
  --panel PATH   one or more bed files containing genomic intervals
```
ds (dataset id) and vcf (path to the VCF file containing the variants) are mandatory parameters. One or more samples included in the VCF file must also be specified. To specify multiple samples use the -sample parameter multiple times (example -sample sampleA -sample sampleB ..).

VCF files might as well be filtered by genomic intervals prior to variant uploading. To upload variants filtered by multiple panels use the options -panel panelA -panel panelB, providing the path to a [bed file](http://genome.ucsc.edu/FAQ/FAQformat#format1) containing the genomic intervals of interest.

Additional variants for the same sample(s) and the same dataset might be added any time by running the same `beacon add variants` specifying another VCF file. Whenever the variant is already found for the same sample and the same dataset it will not be saved twice.

<a name="variants_api"></a>
## Adding variant data using the REST API
Variant data can be alternatively loaded to the Beacon by sending a request to the /apiv1.0/add endpoint.
This Endpoint is accepting json data from POST requests. If the request parameters are correct it will return a response with code 200 (success) and message "Saving variants to Beacon", whole it will start the actual thread that will save variants to database.


### Sending an add request to the API
Apart from the header, an add request should contain the following parameters:
 - **dataset_id** (mandatory): string dentifier for a dataset
 - **vcf_path** (mandatory): path to variants VCF file
 - **assemblyId** (mandatory) : Genome build used in variant calling ("GRCh37", "GRCh38")
 - **samples** (mandatory): list of samples to extract variants from in VCF file
 - **genes**<sup>*</sup> (optional): an object containing two keys:
  - **ids**: list of genes ids to be used to filter VCF file (only variants included in these genes will be saved to database).
  - **id_type**: either "HGNC" or "Ensembl", to specify which type of ID format `ids` refers to. All genes in the list must be of the same type (for example all Ensembl IDs).

HTML Requests to add variants should contain an `auth_token` header which corresponds to the token of a **pre-existing API user**. API users are created exclusively using the command line. Follow these [instructions](#user) to create a new API user.

Once the user is created in the database, make sure the request to the add API contains the following header parameters:
 - **Content-Type**: application/json
 - **X-Auth-Token**: auth_token


Example of a valid POST request to the add endpoint:
```
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Auth-Token: auth_token' \
  -d '{"dataset_id": "test_public",
  "vcf_path": "path/to/cgbeacon2/cgbeacon2/resources/demo/test_trio.vcf.gz",
  "samples" : ["ADM1059A1", "ADM1059A2"],
  "genes" : {"ids": [17284, 29669, 11592], "id_type":"HGNC"},
  "assemblyId": "GRCh37"}' http://localhost:5000/apiv1.0/add
```

<sup>*</sup> **In order for the genes option to work, it is necessary to load genes data into the database via the command line**. Instructions on how to load genes info into the database are available [here](#genes)
