# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `ipaddress` so the module can use that dependency.
import ipaddress

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Collection


# Defines the `trusted_client_ip` callable and its typed interface.
def trusted_client_ip(
    # Declares the typed `peer` data field.
    peer: str | None,
    # Declares the typed `forwarded_for` data field.
    forwarded_for: str | None,
    # Declares the typed `trusted_proxy_ips` data field.
    trusted_proxy_ips: Collection[str],
    # Completes the signature and declares the callable return type.
) -> str:
    # Documents the purpose or contract of this module, class, or function.
    """Resolve a client address without trusting caller-controlled forwarding headers."""

    # Computes and stores `direct_peer` for subsequent operations.
    direct_peer = peer or "unknown"
    # Checks this condition before executing the nested branch.
    if direct_peer not in trusted_proxy_ips:
        # Returns this result to the caller and ends the current function.
        return direct_peer
    # Computes and stores `forwarded` for subsequent operations.
    forwarded = (forwarded_for or "").split(",", 1)[0].strip()
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Returns this result to the caller and ends the current function.
        return str(ipaddress.ip_address(forwarded))
    # Handles the listed exception so failure remains controlled.
    except ValueError:
        # Returns this result to the caller and ends the current function.
        return direct_peer
