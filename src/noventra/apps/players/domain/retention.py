"""Retention domain — schedule + data classes.

Per ADR-0051 / DEC-0056.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class DataClass(str, enum.Enum):
    """Data classes for retention scheduling.

    Per ADR-0051: default schedule per data class.
    """

    PLAYER_PROFILE = "player_profile"
    CONSENT_RECORDS = "consent_records"
    LOGIN_HISTORY = "login_history"
    AUDIT_LOG = "audit_log"  # Per Phase 7 ADR-0036 (separate schedule)
    TRANSACTIONS = "transactions"  # Phase 11+


# Default retention periods (days). Per ADR-0051.
# Phase 9 uses defaults per DEC-0157.
DEFAULT_RETENTION_DAYS: dict[DataClass, int] = {
    DataClass.PLAYER_PROFILE: 2555,  # 7 years after closure
    DataClass.CONSENT_RECORDS: 2555,  # 7 years after revocation
    DataClass.LOGIN_HISTORY: 730,  # 2 years
    DataClass.AUDIT_LOG: 2555,  # 7 years (per Phase 7)
    DataClass.TRANSACTIONS: 2555,  # 7 years
}


@dataclass(frozen=True)
class RetentionSchedule:
    """Retention schedule for a data class.

    Per ADR-0051: single default schedule (DEC-0157 Global Mode).
    """

    data_class: DataClass
    retention_days: int

    @classmethod
    def default_for(cls, data_class: DataClass) -> "RetentionSchedule":
        return cls(data_class=data_class, retention_days=DEFAULT_RETENTION_DAYS[data_class])
