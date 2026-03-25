"""MD5 signature algorithm for ZPay API.

Algorithm (per official docs):
1. Exclude: sign, sign_type, and any null/empty value fields.
2. Sort remaining keys by ASCII order (a→z).
3. Join as URL key-value pairs: a=b&c=d
4. Append the merchant KEY directly (no separator).
5. MD5 hash the full string → lowercase hex.
"""

import hashlib
from typing import Any


def _build_query(params: dict[str, Any]) -> str:
    """Filter, sort and join params into a query string (no URL encoding)."""
    excluded = {"sign", "sign_type"}
    filtered = {
        k: str(v)
        for k, v in params.items()
        if k not in excluded and v is not None and str(v) != ""
    }
    sorted_keys = sorted(filtered.keys())
    return "&".join(f"{k}={filtered[k]}" for k in sorted_keys)


def generate_sign(params: dict[str, Any], key: str) -> str:
    """Generate an MD5 signature for the given parameters.

    Args:
        params: Request parameters (sign/sign_type/null values are excluded).
        key: Merchant secret key.

    Returns:
        Lowercase MD5 hex digest.
    """
    query = _build_query(params)
    raw = query + key
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def verify_sign(params: dict[str, Any], key: str) -> bool:
    """Verify that the ``sign`` field in *params* matches the expected value.

    Args:
        params: Parameters received from ZPay (must include ``sign`` field).
        key: Merchant secret key.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    received_sign = params.get("sign", "")
    expected_sign = generate_sign(params, key)
    return received_sign == expected_sign
