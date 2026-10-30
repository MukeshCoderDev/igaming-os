"""Storage port interface.

Per ADR-0054 / DEC-0059. Backend Q5-blocked (stub for dev).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class StorageResult:
    """Result of a storage operation."""
    success: bool
    key: Optional[str] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class StoragePort(abc.ABC):
    """Port: document storage interface.

    Per ADR-0054: put/get/delete/head. Backend Q5-blocked.
    Per-document encryption key (DEK) for cryptographic shredding (ADR-0055).
    Access control via application-level proxy (no direct backend access).
    """

    @abc.abstractmethod
    def put(self, *, key: str, data: bytes, metadata: dict[str, Any]) -> StorageResult:
        """Store data under key. Returns StorageResult."""

    @abc.abstractmethod
    def get(self, *, key: str) -> StorageResult:
        """Retrieve data by key. Returns StorageResult (data in metadata)."""

    @abc.abstractmethod
    def delete(self, *, key: str) -> StorageResult:
        """Delete data by key. Returns StorageResult."""

    @abc.abstractmethod
    def head(self, *, key: str) -> StorageResult:
        """Check if key exists + get metadata (no data). Returns StorageResult."""
