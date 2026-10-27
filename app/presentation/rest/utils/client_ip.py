"""The address of the person behind a request, through the proxies in front of us.

Browser traffic reaches the API through nginx and the frontend's `/backend`
proxy, so the TCP peer is always one of our own machines. Counting per peer
made every per-IP limit (logins, the demo, the kinship tool) one limit shared
by all visitors. The visitor's address is in ``X-Forwarded-For``, but that
header is only believable when a proxy we run put it there.
"""

from functools import lru_cache
from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network

from starlette.requests import Request

from app.core.config import settings


@lru_cache(maxsize=4)
def _trusted_networks(spec: str) -> tuple[IPv4Network | IPv6Network, ...]:
    return tuple(
        ip_network(part.strip(), strict=False)
        for part in spec.split(",")
        if part.strip()
    )


def _is_trusted(address: str) -> bool:
    try:
        parsed = ip_address(address)
    except ValueError:
        return False
    return any(
        parsed in network for network in _trusted_networks(settings.TRUSTED_PROXY_CIDRS)
    )


def client_ip(request: Request) -> str | None:
    """
    The client's address, read through trusted proxies.

    When the direct peer is not a trusted proxy, its own address is the answer
    and ``X-Forwarded-For`` is ignored — anyone can write that header. When it
    is trusted, the header is read from the right (each proxy appends the
    address it saw) and the first address that is not itself a trusted proxy
    is the client.

    Args:
        request: The incoming request.

    Returns:
        str | None: The client's address, or ``None`` when the server knows no
        peer at all.
    """
    peer = request.client.host if request.client else None
    if peer is None or not _is_trusted(peer):
        return peer

    forwarded = request.headers.get("x-forwarded-for", "")
    hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
    for hop in reversed(hops):
        if not _is_trusted(hop):
            return hop
    # Every hop was one of ours: the request started inside the network.
    return hops[0] if hops else peer
