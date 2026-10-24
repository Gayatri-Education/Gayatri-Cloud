"""SSRF Protection and Path Traversal Defense.
Protects against Server-Side Request Forgery on user-supplied endpoints (custom AI providers, webhooks).
Blocks cloud metadata services (e.g. AWS 169.254.169.254), private RFC-1918 subnets, and loopback.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Disallowed IP ranges
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("10.0.0.0/8"),  # RFC-1918 Private
    ipaddress.ip_network("172.16.0.0/12"),  # RFC-1918 Private
    ipaddress.ip_network("192.168.0.0/16"),  # RFC-1918 Private
    ipaddress.ip_network("169.254.0.0/16"),  # Link-Local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("0.0.0.0/8"),  # Current network
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
    ipaddress.ip_network("::1/128"),  # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),  # IPv6 Link-Local
]


def validate_outbound_url(
    url_str: str,
    allow_localhost_for_dev: bool = False,
) -> str:
    """Validate user-supplied URL against SSRF attack vectors.

    Raises HTTPException(400) if URL targets internal, private, loopback, or cloud-metadata IPs.
    """
    if not url_str or not isinstance(url_str, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL provided.",
        )

    url_str = url_str.strip()
    try:
        parsed = urlparse(url_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed URL: {e}",
        ) from e

    if parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are allowed.",
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL missing valid hostname.",
        )

    # Check for direct IP address literal
    try:
        ip = ipaddress.ip_address(hostname)
        if allow_localhost_for_dev and ip.is_loopback:
            return url_str
        for net in BLOCKED_NETWORKS:
            if ip in net:
                logger.warning("SSRF blocked attempt to access private IP: %s", ip)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SSRF protection: access to restricted network address ({ip}) is prohibited.",
                )
        return url_str
    except ValueError:
        # Not a raw IP literal, it is a DNS hostname
        pass

    # Block well-known metadata hostnames
    lowered = hostname.lower()
    if lowered in (
        "localhost",
        "metadata.google.internal",
        "169.254.169.254",
        "instance-data",
    ):
        if not (allow_localhost_for_dev and lowered == "localhost"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSRF protection: hostname '{hostname}' is restricted.",
            )

    # In production/live environments, DNS resolution can be checked
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in addr_info:
            resolved_ip_str = sockaddr[0]
            resolved_ip = ipaddress.ip_address(resolved_ip_str)
            if allow_localhost_for_dev and resolved_ip.is_loopback:
                continue
            for net in BLOCKED_NETWORKS:
                if resolved_ip in net:
                    logger.warning(
                        "SSRF blocked: hostname '%s' resolved to private IP %s",
                        hostname,
                        resolved_ip,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"SSRF protection: hostname resolved to restricted address ({resolved_ip}).",
                    )
    except socket.gaierror:
        # DNS resolution failure in tests or offline is permitted if hostname is not a prohibited literal
        pass

    return url_str


def sanitize_storage_key(path_or_key: str) -> str:
    """Sanitizes file paths and storage keys, preventing directory traversal attacks.

    Rejects '..' segments, absolute root overrides, and null bytes.
    """
    if "\x00" in path_or_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Null byte detected in file path.",
        )

    normalized = path_or_key.replace("\\", "/").strip()
    parts = normalized.split("/")

    for part in parts:
        if part in ("..", "."):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path traversal detected: directory navigation not allowed.",
            )

    # Strip leading slashes to prevent absolute breakout
    clean_key = "/".join(p for p in parts if p)
    if not clean_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty or invalid storage key.",
        )

    return clean_key
