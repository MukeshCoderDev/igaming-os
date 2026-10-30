"""AML/CFT domain — screening, risk, SAR.

Per ADR-0056 / DEC-0061.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class ScreeningType(str, enum.Enum):
    PEP = "pep"
    SANCTIONS = "sanctions"
    ADVERSE_MEDIA = "adverse_media"


class ScreeningResultStatus(str, enum.Enum):
    CLEAR = "clear"
    MATCH = "match"
    POSSIBLE_MATCH = "possible_match"
    ERROR = "error"


class SarStatus(str, enum.Enum):
    """SAR (Suspicious Activity Report) status."""
    DRAFT = "draft"
    FILED = "filed"  # Filed by MLRO to FIU
    WITHDRAWN = "withdrawn"  # Withdrawn before filing


@dataclass(frozen=True)
class ScreeningResult:
    """Result of a PEP/sanctions screening.

    Per ADR-0056: vendor Q5-blocked (stub for dev).
    """

    screening_uuid: uuid.UUID
    case_uuid: uuid.UUID
    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    screening_type: ScreeningType
    status: ScreeningResultStatus
    match_details: Optional[str] = None  # Redacted in non-MLRO views
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class AmlResult:
    """AML/CFT risk assessment result.

    Per ADR-0056: RBA (rule-based); risk score computed from screening + player profile.
    """

    case_uuid: uuid.UUID
    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    risk_score: int  # 0-100
    risk_level: str  # low, medium, high
    triggers_edd: bool  # True if risk > threshold
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class SarRecord:
    """A SAR record. Per ADR-0056.

    MLRO-only visibility (restricted audit per ADR-0058).
    Tipping-off prohibition: the player is NOT notified when a SAR is filed.
    """

    sar_uuid: uuid.UUID
    case_uuid: uuid.UUID
    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    status: SarStatus = SarStatus.DRAFT
    mlro_uuid: Optional[uuid.UUID] = None
    filed_at: Optional[datetime] = None
    reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # MLRO-only: this record is not visible to non-MLRO roles per ADR-0058.
    mlro_restricted: bool = True
