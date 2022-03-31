## [] -
### Added
- Load genes when initializing demo application
- Instructions on how to load/update genes in database to filter uploaded VCFs by genes
- Added an add_dataset endpoint to create or update datasets via the API
### Fixed
- Fixed code to remove all deprecation warnings

## [4.0] - 2022.03.21
### Added
- Redirect to query form page when user lands on / endpoint
- Software version on query form page
- Database name and general stats on landing page
- Tooltips on query form explaining that coordinates are 0-based
- Clicking on number of datasets in query form expands dataset description window
- Codecov config file
- Push gunicorn server image to Docker Hub on new release event
### Changed
- / endpoint redirects to info endpoint returning json beacon info
- Refactored HTML query form to be more user friendly
- Refactored query form page to better display dataset-specific results
- Refactored cli options and params to be compliant with the GNU coding standards
- Moved code checking parameters used to create a new dataset in a dedicated function under utils/add.py
- Removed optional consent codes when creating a new dataset, as they are not required and complicate code
### Fixed
- Return dataset-specific info even if allele is not found
- Instructions on how to deploy the beacon with podman as a systemd service
- Updated Black version used in GitHub action's to 22.3.0, to fix linting error in CI due to new Click release
- Dataset version is saved as a string

## [3.3.1] - 2022.03.11
### Fixed
- Long description error in setup.py file causing an error on twine before PyPI push
- Switch to codecov action v.2, since v.1 is deprecated

## [3.3] - 2022.03.11
### Added
- Push to PyPI when a new release is created
- Dockerfile-server to serve the prod app via gunicorn
- Notify admins via email when app crashes
- Queries using fuzzy string searching (allow Ns in search pattern)
- Return type annotation to all python functions
### Changed
- Install required libs from requirements.txt directly in setup.py
- Dockerfile-server image pushed to Docker Hub (cgbeacon2-server-stage) when a PR is opened or updated
- Refactored code in server/blueprints/api_v1/controllers.py
### Fixed
- Error returned when query contains non-existent dataset IDs
- Serve images as static files otherwise nginx doesn't show them

## [3.2] - 2022.02.01
### Added
- Vulture GitHub action to find unused code with 80% confidence
### Fixed
- Freeze PyMongo lib to version<4.0 to keep supporting previous MongoDB versions
### Changed
- Scan only changed .py files with Vulture
- Multi-stage Dockerfile for smaller and faster-built image


## [3.1] - 2021.10.18
### Added
- Option to provide a custom token when creating a database user
- Example of URI for connecting to a MongoDB replica set
### Fixed
- Fixed the command that runs the web app service on docker-compose
### Changed
- Replaced the alpine-based MongoDB image used in docker-compose with the official MongodDB image (db version 4.4.9)
- Launch the demo app on port 6000 when it's started via docker-compose
- Build Docker image from local repo when using docker-compose
- Use database port 27013 in docker-compose

## [3.0] - 2021.06.30
### Added
- Instructions to run the Beacon cli and web server connected to mongo as a service via Podman
- Inclusive-language check using [woke](https://github.com/get-woke/woke) github action
- Use official Docker github actions to push Docker images to Docker Hub -> Master branch (on release event) and PR branch (on push event)
- Create a demo user with a token for using the API when creating a demo instance
- Github action to deploy docs after a new release is published
### Fixed
- Links in docs pages
- Added instructions on how to install bedtools in documentation and readme file
- Build badge link in README page
- Fixed test no longer working after the release of Flask 2.0
- Replaced old docs link www.clinicalgenomics.se/cgbeacon2 with new https://clinical-genomics.github.io/cgbeacon2
- Improved code according to codefactor and Flake8 suggestions
- Indented code in a github action
- Link to docs in the README page
### Changed
- Switch to codecov in gihub actions
- Switched coveralls badge with codecov badge
- id param name in create user and create database cli command
- Use list_collection_names() instead of collection_names() that was deprecated in pymongo 3.7
- Use DELETE requests for deleting items from the database


## [2.0] - 2021.01.11
### Added
- Create users with randomly generated tokens to use the REST API
- Auth token validation in `add` and `delete` requests
- Updated documentation to add and delete variants using the APIs
### Fixed
- Docker action that didn't push 2 tags for a new release, just the "latest"
- Dockerfile faster to build and cleaner code
- Modified jwt.decode params to be compliant to PyJWT v2.0
- Bug when trying to delete variants for samples not in dataset
- Bug when variant samples do not correspond to dataset samples
### Changed
- `add` and `delete` API are returning async responses
- Renamed entry point command `cgbeacon2` to `beacon`


## [1.4] - 2020.11.05
### Added
- Github action to build and publish Docker image
### Changed
- Docker reference to image point to clinicalgenomics Docker Hub
### Fixed
- Broken link in the docs and in README


## [1.3] - 2020.10.27

### Fixed
- Broken github actions test
### Changed
- Removed Codecov and master workflow github action
### Added
- Codecov and CodeFactor github actions
- Created deployment WSGI file
- Dockerfile and docker-compose files
- Flake8, Coveralls and Black github actions


## [1.2] - 2020.10.19

### Fixed
- Added an init file inside the demo resources folder
- Accept variants annotated with build GRCh37 and GRCh38 (`chrN`) instead of just `N` (as in hg19)
- Improved calculation of structural variants end coordinates

### Changed
- Renamed SNV and SV demo VCF files
- Coordinate Range queries allowing fuzzy positions

### Added
- Demo VCF file containing BND SV variants
- Save BND variants to database (introduced additional mateName key/values)
- Query BND variants using mateName
- Documentation using `MkDocs`.
- Populate database with genes downloaded from Ensembl Biomart
- Function to create a VCF Bedtool filter from a list of genes HGNC ids or Ensembl ids
- API endpoint to add variants using a POST request
- API endpoint to remove variants using POST request


## [1.1] - 2020.06.17

### Fixed
- Revert to previous code, since cyvcf2 returns 0-based coordinates
- Updated README
- Added missing `requests` lib in requests
- Freezes pysam in requirements file
- Sets pytest requirement to >4.6 because of lack of backward compatibility of new version of pytest-cov
- Remove redundant text from cli docstrings
- Modified colors of 2 big checkboxes in the query form html page

### Added
- Check that all requested samples are in VCF samples before uploading any variant
- Registering events whenever datasets and/or variants are added or removed
- Beacon info endpoint now returns beacon createDateTime and updateDateTime


## [1] - 2020.06.05

### Added
- Info endpoint (/) for API v1
- Add new datasets using the command line
- Update existing datasets using the command line
- Delete a dataset using the command line
- Code to parse VCF files (SNVs) and create Variant objects
- Save SNV variants from parsed VCF files
- Update SNV variants for one or more VCF samples
- Remove variants by providing dataset id and sample name(s)
- Filter VCF files using bed files with genomic intervals
- Query endpoint returns basic response
- Created error messages to handle wrong server requests
- Return responses for SNV queries with datasetAlleleResponses == ALL, HIT, MISS
- Added repository codeowners
- Added tests for queries with datasetAlleleResponses == HIT and MISS
- No conflicts between queried assembly and the assembly or queried datasets
- Parse SVs and save them to database
- Fixed code for range queries and without end position, with tests
- Added test for negative response and introduce error=None if response status code is 200 (success)
- Added simple query interface
- Run queries and display results on the web interface
- Add 3 level of authentication when creating datasets and fix tests accordingly
- Important request/response syntax fixes
- Included OAuth2 JWT validation layer
- Included tests for non-valid auth JWTs
- Stratify returned results by user auth level
- Fixed code that handles POST request content
- Added a function to load demo data into demo database
- Added a short description of the Beacon command and functionalities in the readme file
- Return query examples in the info endpoint
- Do not enforce check of end position in structural variants query
- Zero-based coordinates
- Save variant allele count and return it in datasetAlleleResponses result objects
- Return variantCount in datasetAlleleResponses
- Return dataset access level info in datasetAlleleResponses
- Return datasets callCount and variantCount in info endpoint response
