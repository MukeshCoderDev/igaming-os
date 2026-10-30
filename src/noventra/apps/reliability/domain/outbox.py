"""Outbox domain — event schema + status.

Per ADR-0040 / DEC-0045: outbox table schema; relay via polling;
multi-instance via SELECT FOR UPDATE SKIP LOCKED; at-least-once.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    RELAYED = "relayed"
    FAILED = "failed"


@dataclass(frozen=True)
class OutboxEvent:
    """An outbox event to be relayed.

    Per ADR-0040 / event schema doc (Phase 8 spec output #9):
    event_id, event_type, event_version, aggregate_id, aggregate_type,
    tenant_id, actor_id, correlation_id, occurred_at, payload.
    """

    event_id: uuid.UUID
    event_type: str
    event_version: int
    aggregate_id: str
    aggregate_type: str
    tenant_id: Optional[uuid.UUID]
    actor_id: uuid.UUID
    correlation_id: Optional[str]
    occurred_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    status: OutboxStatus = OutboxStatus.PENDING
    relayed_at: Optional[datetime] = None
    retry_count: int = 0
