"""Inbox domain — dedup entry.

Per ADR-0041 / DEC-0046: inbox table with (message_id, consumer_id) PK.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class InboxEntry:
    """An inbox entry recording that a message was processed.

    Per ADR-0041: (message_id, consumer_id) composite PK.
    ON CONFLICT DO NOTHING on insert.
    """

    message_id: uuid.UUID
    consumer_id: str
    processed_at: datetime
    payload_hash: Optional[str] = None
