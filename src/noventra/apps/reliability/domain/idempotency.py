"""Idempotency domain — key record.

Per ADR-0043 / DEC-0048: idempotency_key table with (key, tenant_id, endpoint) PK.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class IdempotencyRecord:
    """An idempotency key record.

    Per ADR-0043: 24-hour TTL; conflict handling (same key + same body =
    cached response; same key + different body = 409).
    """

    key: str  # UUIDv4 from client
    tenant_id: uuid.UUID
    endpoint: str
    request_hash: str  # SHA-256 of request body
    response_status: int
    response_body: str
    created_at: datetime
    expires_at: datetime
