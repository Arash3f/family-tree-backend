import base64
import hashlib

from app.application.services.mcp_oauth_service import _b64url_sha256


def test_pkce_s256_matches_rfc7636_example_shape():
    verifier = "abcdefghijklmnop"
    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    assert _b64url_sha256(verifier) == expected
