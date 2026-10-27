import pytest
from starlette.requests import Request

from app.presentation.rest.utils.client_ip import client_ip


def _request(peer: str | None, forwarded: str | None = None) -> Request:
    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded else []
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "client": (peer, 1234) if peer else None,
    }
    return Request(scope)


def test_a_direct_visitor_is_counted_by_their_own_address():
    assert client_ip(_request("203.0.113.7")) == "203.0.113.7"


def test_a_direct_visitor_cannot_spoof_the_header():
    # An untrusted peer writing X-Forwarded-For gains nothing.
    assert client_ip(_request("203.0.113.7", "198.51.100.1")) == "203.0.113.7"


def test_behind_our_proxy_the_forwarded_client_is_used():
    assert client_ip(_request("172.18.0.5", "198.51.100.1")) == "198.51.100.1"


def test_a_chain_of_our_proxies_is_skipped_from_the_right():
    # nginx saw the visitor, then the frontend container appended itself.
    forwarded = "198.51.100.1, 172.18.0.3"
    assert client_ip(_request("127.0.0.1", forwarded)) == "198.51.100.1"


def test_a_value_the_visitor_prepended_is_not_believed():
    # The visitor sent "1.2.3.4"; nginx appended the real address after it.
    forwarded = "1.2.3.4, 198.51.100.1"
    assert client_ip(_request("172.18.0.5", forwarded)) == "198.51.100.1"


def test_a_request_from_inside_the_network_keeps_the_first_hop():
    assert client_ip(_request("127.0.0.1", "10.0.0.2, 172.18.0.3")) == "10.0.0.2"


def test_without_a_header_the_peer_is_used():
    assert client_ip(_request("172.18.0.5")) == "172.18.0.5"


def test_no_peer_at_all():
    assert client_ip(_request(None)) is None


@pytest.mark.parametrize("peer", ["172.18.0.5", "::1"])
def test_trusted_network_list_comes_from_settings(monkeypatch, peer):
    from app.core.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_CIDRS", "192.0.2.0/24")
    # With the default networks gone, the peer itself is the client.
    assert client_ip(_request(peer, "198.51.100.1")) == peer
