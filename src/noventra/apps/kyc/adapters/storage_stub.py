"""Stub storage adapter — dev only. Per ADR-0054: backend Q5-blocked."""

from __future__ import annotations

import logging
from typing import Any

from noventra.apps.kyc.domain.storage_port import StoragePort, StorageResult

log = logging.getLogger("noventra.kyc.storage_stub")


class StubStorageAdapter(StoragePort):
    """In-memory storage stub. Dev only. Real adapter (Q5) in Phase 11."""

    def __init__(self):
        self._store: dict[str, bytes] = {}
        self._meta: dict[str, dict] = {}

    def put(self, *, key: str, data: bytes, metadata: dict[str, Any]) -> StorageResult:
        self._store[key] = data
        self._meta[key] = metadata
        log.info("storage_stub_put", extra={"key": key, "size": len(data)})
        return StorageResult(success=True, key=key, metadata=metadata)

    def get(self, *, key: str) -> StorageResult:
        if key not in self._store:
            return StorageResult(success=False, error="not_found")
        return StorageResult(success=True, key=key, metadata={"data": self._store[key], **self._meta.get(key, {})})

    def delete(self, *, key: str) -> StorageResult:
        if key not in self._store:
            return StorageResult(success=False, error="not_found")
        del self._store[key]
        self._meta.pop(key, None)
        return StorageResult(success=True, key=key)

    def head(self, *, key: str) -> StorageResult:
        if key not in self._store:
            return StorageResult(success=False, error="not_found")
        return StorageResult(success=True, key=key, metadata=self._meta.get(key, {}))
