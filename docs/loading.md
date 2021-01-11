
## Adding data to the database

Dataset and variant data can be loaded into the database using specific the specific command line. To visualize command line options, from the terminal you can user the following command: `beacon --help`.

The default procedure to add variants to the beacon is always the following:

- Create a dataset to link your variants to.
- Load variants from a VCF file for one or more samples, specifying which dataset these variants belong to.

## How to add:
1. [ Demo data ](#demodata)
1. [ A new dataset (custom data)](#dataset)
1. [ Variants (custom data)](#variants)


<a name="demodata"></a>
## Demo data
Demo data consisting in a test dataset with public access and a set of variants (SNVs and structural variants of different type) is available under the cgbeacon2/resources/demo folder. You don't need to load this data manually since the following command will take care of everything:
```
beacon add demo
```

<a name="dataset"></a>
## Adding a new dataset
A new dataset can be created with the following command:
```
beacon add dataset -id <dataset_id> -name <"A dataset name"> -build <GRCh37|GRCh38> -authlevel <public|registered|controlled>
```
The above parameters (id, name, build, authlevel) are mandatory. If user doesn't specify any genome build then the default build used is GRCh37. One dataset can be associated to variants called using only one genome build.
`authlevel` parameter will be used in queries to return results according to the request authentication level.

- **Public datasets** can be interrogated by any beacon and any user in general and should not be used to store sensitive data such as individual phenotypes.
- **Bona fide researchers** logged in via the Elixir AAI will be able to access data store in **registered datasets**.
- **Controlled access datasets** might be used to store sensitive information and will be accessed only by users that have a signed agreement and their access approved by a Data Access Committee (DAC).


More info about the ELixir AAI authentication is available [here](https://elixir-europe.org/services/compute/aai)

Other optional parameters that can be provided to improve the dataset description are the following.
```
  -desc TEXT                      dataset description
  -version FLOAT                  dataset version, i.e. 1.0
  -url TEXT                       external url
  -cc TEXT                        consent code key. i.e. HMB
  --update
```
The `--update` flag will allow to modify the information for a dataset that is already existing in the database.


<a name="variants"></a>
## Adding variant data
Variant data can be loaded to the database using the following command:

```
beacon add variants

Options:
  -ds TEXT      dataset ID  [required]
  -vcf PATH     [required]
  -sample TEXT  one or more samples to save variants for  [required]
  -panel PATH   one or more bed files containing genomic intervals
```
ds (dataset id) and vcf (path to the VCF file containing the variants) are mandatory parameters. One or more samples included in the VCF file must also be specified. To specify multiple samples use the -sample parameter multiple times (example -sample sampleA -sample sampleB ..).

VCF files might as well be filtered by genomic intervals prior to variant uploading. To upload variants filtered by multiple panels use the options -panel panelA -panel panelB, providing the path to a [bed file](http://genome.ucsc.edu/FAQ/FAQformat#format1) containing the genomic intervals of interest.

Additional variants for the same sample(s) and the same dataset might be added any time by running the same `beacon add variants` specifying another VCF file. Whenever the variant is already found for the same sample and the same dataset it will not be saved twice.
