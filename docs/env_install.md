
## Beacon setup

1. [ Prerequisites ](#prerequisites)
1. [ Installation - on a virtual environment using pip](#installation-pip)
1. [ Server settings ](#settings)
1. [ Running the server](#running)


<a name="installation-pip"></a>

### Prerequisites
- A virtual environment containing Python 3.6+
- A working instance of **MongoDB**. From the mongo shell you can create a database using this syntax:
```
use <name_of_database>
```

Database name can be customized. If you don't have any preferences`cgbeacon2` will work just fine.

## Installation

Once activated the virtual environment, clone this repository from github using this command:
```
git clone https://github.com/Clinical-Genomics/cgbeacon2.git
```

Change directory to the cloned folder and from there, install the software using the following command:
```
pip install -e .
```

To make sure the software is installed, from the terminal, you can run the following command: `cgbeacon2 --version`


<a name="settings"></a>
## Server settings

Default server settings are specified in the `config.py` file under cgbeacon2/instance

Secret key and database connection parameters depend on your server implementation, and for the purpose of testing the software they might be left unchanged.

```
# secret key:
SECRET_KEY = "MySuperSecretKey"

# Database connection parameters
DB_HOST = "127.0.0.1"
DB_PORT = 27017
DB_NAME = "cgbeacon2-test"
DB_URI = f"mongodb://{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

`ORGANISATION` and `BEACON_OBJ` dictionaries contain values that are returned by the server when users or other beacons send a request to the info endpoint(/), so they should be filled in properly in a production environment:

```
ORGANISATION = dict(
    id="scilifelab",  # mandatory
    name="Clinical Genomics, SciLifeLab",  # mandatory
    description="A science lab",
    address="",
    contactUrl="",
    info=[],
    logoUrl="",
    welcomeUrl="",
)

BEACON_OBJ = dict(
    id="SciLifeLab-beacon",  # mandatory
    name="SciLifeLab Stockholm Beacon",  # mandatory
    organisation=ORGANISATION,  # mandatory
    alternativeUrl="http//scilifelab.beacon_alt.se",
    createDateTime="2015-06-15T00:00.000Z",
    description="Beacon description",
    info=[],
    welcomeUrl="http//scilifelab.beacon.se",
)
```
The `info` field of both object can contain a series of custom key/values that better describe your organisation and its beacon server.


**OAUTH2 permissions layer** parameters are responsible for the authentication of incoming requests bearing a auth token, and should be left unchanged:
```
ELIXIR_OAUTH2 = dict(
    server="https://login.elixir-czech.org/oidc/jwk",  # OAuth2 server that returns JWK public key
    issuers=[
        "https://login.elixir-czech.org/oidc/"
    ],  # Authenticated Bearer token issuers
    userinfo="https://login.elixir-czech.org/oidc/userinfo",  # Where to send access token to view user data (permissions, statuses, ...)
    audience=[],  # List of strings. Service(s) the token is intended for. (key provided by the Beacon Network administrator)
    verify_aud=False,  # if True, force verify audience for provided token
    bona_fide_requirements="https://doi.org/10.1038/s41431-018-0219-y",
)
```

<a name="running"></a>
## Running the server
To run the server, from the command line, you can use the following command:
```
cgbeacon2 run
```
