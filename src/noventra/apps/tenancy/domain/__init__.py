"""Player domain — entity, lifecycle FSM, consents, retention.

Per ADR-0047..0051 / DEC-0052..0056.
"""

from .player import Player, PlayerState  # noqa: F401
from .consent import Consent, ConsentStatus, ConsentPurpose  # noqa: F401
from .retention import RetentionSchedule, DataClass  # noqa: F401
