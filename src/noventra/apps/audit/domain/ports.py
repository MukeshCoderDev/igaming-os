"""Audit domain ports (interfaces)."""

from __future__ import annotations

import abc
import uuid
from typing import Optional

from .aggregates import AuditChainHead, AuditEvent


class AuditEventRepository(abc.ABC):
    """Port: repository for AuditEvent (insert-only per ADR-0038)."""

    @abc.abstractmethod
    def append(self, event: AuditEvent) -> AuditEvent:
        """Append an event. The DB trigger computes the hash. Returns the
        stored event (with hash + created_at populated)."""

    @abc.abstractmethod
    def read(
        self,
        *,
        tenant_id: Optional[uuid.UUID],
        event_type: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        target_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
    ) -> tuple[list[AuditEvent], Optional[str]]:
        """Read events with filtering + cursor pagination. Returns (events, next_cursor)."""


class AuditChainRepository(abc.ABC):
    """Port: repository for AuditChainHead."""

    @abc.abstractmethod
    def get_head(self, scope: str) -> Optional[AuditChainHead]: ...

    @abc.abstractmethod
    def update_head(self, head: AuditChainHead) -> None: ...
