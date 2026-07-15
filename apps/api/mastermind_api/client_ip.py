from __future__ import annotations

import ipaddress
from collections.abc import Collection


def trusted_client_ip(
    peer: str | None,
    forwarded_for: str | None,
    trusted_proxy_ips: Collection[str],
) -> str:
    """Resolve a client address without trusting caller-controlled forwarding headers."""

    direct_peer = peer or "unknown"
    if direct_peer not in trusted_proxy_ips:
        return direct_peer
    forwarded = (forwarded_for or "").split(",", 1)[0].strip()
    try:
        return str(ipaddress.ip_address(forwarded))
    except ValueError:
        return direct_peer
