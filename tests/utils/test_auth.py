from cgbeacon2.constants import MISSING_PUBLIC_KEY
from cgbeacon2.utils.auth import elixir_key, claims, decode_passport


def test_elixir_key_wrong_key():
    """Test function that returns Elixir AAI public key with wrong server"""

    public_key = elixir_key("nonsense")
    assert public_key == MISSING_PUBLIC_KEY


def test_elixir_key(mock_app):
    """Test the function that returns the public key of Elixir AAI"""

    # When calling the Elixir OAuth2 server
    oauth_config = mock_app.config.get("ELIXIR_OAUTH2")
    assert "server" in oauth_config

    # It should return the expected keys
    public_key = elixir_key(oauth_config["server"])
    assert public_key["keys"][0]["alg"]  # algorithm
    assert public_key["keys"][0]["kid"]
    assert public_key["keys"][0]["n"]
    assert public_key["keys"][0]["kty"]


def test_decode_passport(test_token, header, payload):
    """Test the function that extracts header and payload from a Base64url encoded token"""

    decode_header, decoded_payload = decode_passport(test_token)
    assert decode_header == header
    assert decoded_payload == payload


def test_claims_no_aud(mock_app):
    """Test function that creates token claims when aud is empty and verify aud is False"""

    # When creating the web tokens claim
    claims_options = claims(mock_app.config.get("ELIXIR_OAUTH2"))
    # The function should contain the mandatory keys

    assert claims_options["iss"]["values"] == mock_app.config["ELIXIR_OAUTH2"]["issuers"][0]
    assert claims_options["iss"]["essential"]
    assert claims_options["aud"]["values"] == ""
    assert claims_options["aud"]["essential"] is False
    assert claims_options["exp"]["essential"]


def test_claims_with_aud_and_issuers():
    """test function that creates token claims when aud, verify_aud and issuers are present"""

    # When creating the web tokens claim
    mock_oauth2_settings = dict(
        issuers=["issuer1", "issuer2"], audience=["aud1", "aud2", "aud3"], verify_aud=True,
    )

    # The function should contain the mandatory keys, with values
    claims_options = claims(mock_oauth2_settings)

    assert claims_options["iss"]["values"] == ",".join(mock_oauth2_settings["issuers"])
    assert claims_options["iss"]["essential"]
    assert claims_options["aud"]["values"] == ",".join(mock_oauth2_settings["audience"])
    assert claims_options["aud"]["essential"]
    assert claims_options["exp"]["essential"]
