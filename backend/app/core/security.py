from __future__ import annotations

import hashlib
import hmac
import secrets


def hash_secret(secret: str, salt: str | None = None) -> str:
    """Hash a password, OTP, or device credential using PBKDF2-HMAC-SHA256."""
    actual_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        actual_salt.encode("utf-8"),
        210_000,
    )
    return f"pbkdf2_sha256${actual_salt}${digest.hex()}"


def verify_secret(secret: str, encoded: str) -> bool:
    """Verify a secret against a stored PBKDF2 hash."""
    try:
        algorithm, salt, expected = encoded.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hash_secret(secret, salt).split("$", 2)[2]
    return hmac.compare_digest(candidate, expected)


def generate_token() -> str:
    """Create a high-entropy bearer credential."""
    return secrets.token_urlsafe(48)


def token_fingerprint(token: str) -> str:
    """Create the lookup fingerprint stored for bearer credentials."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
