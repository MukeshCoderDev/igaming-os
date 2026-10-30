"""JWT utilities — issuance + verification.

Per ADR-0031 / DEC-0036: JWT (JWS, HS256 for Phase 6) for access tokens
(15min) + rotating refresh tokens (30d). Service JWTs carry typ=service.

Phase 6 stub: HS256 with SECRET_KEY. Phase 7 switches to RS256 with
key rotation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from typing import Optional

from django.conf import settings


ACCESS_TOKEN_LIFETIME = 900  # 15 minutes.
REFRESH_TOKEN_LIFETIME = 2592000  # 30 days.
SERVICE_TOKEN_LIFETIME = 3600  # 1 hour.


@dataclass(frozen=True)
class TokenClaims:
    """Parsed JWT claims."""

    sub: str  # user_uuid (human) or service_uuid (service)
    tenant_id: str
    typ: str  # "bearer" (human) or "service"
    role: Optional[str]  # role name
    jti: str  # JWT ID (for refresh rotation blacklisting)
    exp: int  # expiry (unix timestamp)
    iat: int  # issued at


def _b64encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return urlsafe_b64decode(data + padding)


def _sign(data: bytes) -> str:
    """HMAC-SHA256 sign with SECRET_KEY."""
    key = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def issue_access_token(
    *,
    subject: str,
    tenant_id: str,
    role: Optional[str] = None,
    typ: str = "bearer",
    lifetime: int = ACCESS_TOKEN_LIFETIME,
) -> str:
    """Issue a JWT access token.

    Args:
        subject: user_uuid (human) or service_uuid (service).
        tenant_id: the tenant context for this token.
        role: role name (for human tokens).
        typ: "bearer" (human) or "service".
        lifetime: token lifetime in seconds.
    """
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "typ": typ,
        "role": role,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + lifetime,
    }
    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = _sign(signing_input)
    return f"{header_b64}.{payload_b64}.{signature}"


def issue_refresh_token(*, subject: str, tenant_id: str, role: Optional[str] = None) -> str:
    """Issue a refresh token (longer lifetime)."""
    return issue_access_token(
        subject=subject,
        tenant_id=tenant_id,
        role=role,
        typ="refresh",
        lifetime=REFRESH_TOKEN_LIFETIME,
    )


def verify_token(token: str) -> Optional[TokenClaims]:
    """Verify a JWT and return claims. Returns None if invalid/expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature = parts
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = _sign(signing_input)
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(_b64decode(payload_b64))
        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None
        return TokenClaims(
            sub=payload["sub"],
            tenant_id=payload["tenant_id"],
            typ=payload.get("typ", "bearer"),
            role=payload.get("role"),
            jti=payload.get("jti", ""),
            exp=payload["exp"],
            iat=payload.get("iat", 0),
        )
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def hash_token_for_logging(token: str) -> str:
    """Hash a token for safe logging (never log raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]
