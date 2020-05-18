# Turns on debugging features in Flask
DEBUG = True

# secret key:
SECRET_KEY = "MySuperSecretKey"

# Database connection parameters
DB_USERNAME = "testuser"
DB_PASSWORD = "testpassw"
DB_HOST = "127.0.0.1"
DB_PORT = 27017
DB_NAME = "cgbeacon2"
DB_URI = f"mongodb://{DB_HOST}:{DB_PORT}/{DB_NAME}"


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

############## OAUTH2 permissions layer ##############
### https://elixir-europe.org/services/compute/aai ###
ELIXIR_OAUTH2 = dict(
    server="https://login.elixir-czech.org/oidc/jwk",  # OAuth2 server that returns JWK public key
    issuers=[
        "https://login.elixir-czech.org/oidc/"
    ],  # Authenticated Bearer token issuers
    userinfo="https://login.elixir-czech.org/oidc/userinfo",  # Where to send access token to view user data (permissions, statuses, ...)
    audience=[],  # List of strings. Sservice(s) the token is intended for. (key provided by the Beacon Network administrator)
    verify_aud=False,  # if True, force verify audience for provided token
    bona_fide_requirements="https://doi.org/10.1038/s41431-018-0219-y",
)
