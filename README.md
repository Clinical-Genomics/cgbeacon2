# cgbeacon2

[![Build Status](https://travis-ci.org/Clinical-Genomics/MIP.svg?branch=master)](https://travis-ci.org/Clinical-Genomics/MIP)
[![Coverage Status](https://coveralls.io/repos/github/Clinical-Genomics/cgbeacon2/badge.svg?branch=master)](https://coveralls.io/github/Clinical-Genomics/cgbeacon2?branch=master)

An updated beacon supporting [ GA4GH API 1.0 ][ga4gh_api1]

This README only gives a brief overview of the tool, for a more complete reference, please check out our docs: www.clinicalgenomics.se/cgbeacon2

Table of Contents:
1. [ Running the app using Docker ](#docker)
2. [ Installation using pip in a virtual environment](#installation)
3. [ Loading demo data into the database ](#Loading)
4. [ Server endpoints ](#endpoints)
    - [ Obtaining beacon info ](#info)
    - [ Running queries ](#query)
    - [ Adding variants ](#add)
    - [ Removing variants ](#delete)
5. [ Web interface ](#webform)


<a name="docker"></a>
## Installing and running the app using Docker

A demo instance of the app containing test data can be started from the docker-compose file using this command:
```
docker-compose up -d
```
The command will create 3 containers:
- mongodb: starting a mongodb server
- beacon-cli: the a command-line app, which will connect to the server and populates it with demo data
- beacon-web: a web server running on localhost and port 27017.

The server will be running and accepting requests sent from outside the containers (another terminal or a web browser). Read further down to find out about request types and queries.

To stop the containers (and the server), run:
```
docker-compose down
```

To instantiate a server without demo data just remove the line:
`command: bash -c 'beacon add demo'`
from the docker-compose.yml file.

More info on how to set up a server containing app backend and frontend is available in the [docs](http://www.clinicalgenomics.se/cgbeacon2)

<a name="installation"></a>
## Installation

### Prerequisites
- It is recommended to install the app inside a virtual environment containing python >3.6
- Bedtools should be installed in the virtual environment. To install it using the bioconda channel type:
```
conda install -n your_beacon_environment -c bioconda bedtools
```
Python 3.6+
- A working instance of **MongoDB**. From the mongo shell you can create a database using this syntax:
```
use cgbeacon2-test
```

Activate the virtual environment and clone this repository from github using this command:
```
git clone https://github.com/Clinical-Genomics/cgbeacon2.git
```

Change directory to the cloned folder and from there, install the software using the following command:
```
pip install -r requirements.txt
pip install -e .
```

To customize the server configuration you'll need to edit the **config.py** file under the /instance folder. &nbsp;
For testing purposes you can keep the default configuration values as they are, but keep in mind that you should adjust these parameters when in production.

To start the server run this command:
```
beacon run -h custom_host -p custom_port
```
Omitting custom_host and custom_port parameters will make the server run on default host=localhost (127.0.0.1) and default port 5000.

Please note that this code is NOT guaranteed to be bug-free and it must be adapted to be used in production.

<a name="loading"></a>
## Loading demo data into the database
In order to test how the software works and run test queries, a demo dataset and variants can be loaded into the database by running the following command:
```
beacon add demo
```
This command will create 2 collections: "dataset" and "variant". Dataset collection will contain a public dataset named "test_public". "variant" collection will be populated with several hundreds variants, both single nucleotide variants, indels and structural variants.

<a name="endpoints"></a>
## Server endpoints

<a name="info"></a>
- **/**.
General info regarding this Beacon, including a description of its datasets, API version, sample count etc, can be obtained by sending a GET request using the following shell command:
```
curl -X GET 'http://localhost:5000/apiv1.0/'
```

Demo beacon will reply to this request with a JSON object like this:
```
{"alternativeUrl":null,"apiVersion":"v1.0.0","createDateTime":"Tue, 23 Jun 2020 14:33:52 GMT","datasets":[{"assembly_id":"GRCh37","callCount":483,"created":"Tue, 23 Jun 2020 14:33:52 GMT","id":"test_public","info":{"accessType":"PUBLIC"},"name":"Test public dataset","sampleCount":1,"updated":"Tue, 23 Jun 2020 14:33:53 GMT","variantCount":408,"version":1.0}],"description":"Beacon description","id":"SciLifeLab-beacon","name":"SciLifeLab Stockholm Beacon","organisation":{"address":"","contactUrl":"","description":"A science lab","id":"scilifelab","info":[],"logoUrl":"","name":"Clinical Genomics, SciLifeLab","welcomeUrl":""},"sampleAlleleRequests":[{"alternateBases":"A","assemblyId":"GRCh37","datasetIds":["test_public"],"includeDatasetResponses":"HIT","referenceBases":"C","referenceName":"1","start":156146085},{"assemblyId":"GRCh37","includeDatasetResponses":"ALL","referenceBases":"C","referenceName":"20","start":54963148,"variantType":"DUP"}],"updateDateTime":"Tue, 23 Jun 2020 14:33:53 GMT","version":"v1.1","welcomeUrl":null}
```

<a name="query"></a>
- **/query**.
Query endpoint supports both GET and POST requests.
Example of a GET request:
```
curl -X GET \
  'http://localhost:5000/apiv1.0/query?referenceName=1&referenceBases=C&start=156146085&assemblyId=GRCh37&alternateBases=A'
```

Example of a POST request:
```
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"referenceName": "1",
  "start": 156146085,
  "referenceBases": "C",
  "alternateBases": "A",
  "assemblyId": "GRCh37",
  "includeDatasetResponses": "HIT"}' http://localhost:5000/apiv1.0/query
```

The Beacon reply to a query of this type would be a json object where the "exist" key will be true if the allele is found, otherwise it will be false.
```
{"allelRequest":{"alternateBases":"A","assemblyId":"GRCh37","datasetIds":[],"includeDatasetResponses":"NONE","referenceBases":"C","referenceName":"1","start":"156146085"},"apiVersion":"1.0.0","beaconId":"SciLifeLab-beacon","datasetAlleleResponses":[],"error":null,"exists":true}
```

<a name="add"></a>
- **/add**.
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
Note that only authenticated users will be able to use this endpoint by including the user's auth_token in the request headers. [Additional info](http://www.clinicalgenomics.se/cgbeacon2/loading/) on how to use this endpoint.

<a name="delete"></a>
- **/delete**.
Endpoint that can be used by authenticated users to remove variants by sending a POST request like this:
```
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Auth-Token: auth_token' \
  -d '{"dataset_id": "test_public",
  "samples" : ["ADM1059A1", "ADM1059A2"]}' http://localhost:5000/apiv1.0/delete
```
Additional info available [here](http://www.clinicalgenomics.se/cgbeacon2/removing/).


<a name="webform"></a>
## Web interface
A simple web interface to perform interactive queries can be used by typing the following address in any browser window: `http://127.0.0.1:5000/apiv1.0/query_form`

![Interface picture](docs/pics/beacon2_interface.jpg)

At the moment this interface is disconnected with Elixir AAI so all queries will be limited to the available public datasets in the Beacon.

[ga4gh_api1]: https://github.com/ga4gh-beacon/specification/blob/develop/beacon.md
