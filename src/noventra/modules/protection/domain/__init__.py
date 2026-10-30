"""Protection domain — limits, self-exclusion, reality checks, kill switch.

Per ADR-0084..0091 / DEC-0084..0091. Phase 14.
Most safety-critical phase. Kill Switch <200ms SLO is regulator-mandated.
Implements REAL RGPort (replacing Phase 13 stubs).
"""

from .limits import PlayerLimit, LimitType, LimitPeriod  # noqa: F401
from .self_exclusion import SelfExclusion, ExclusionPeriod  # noqa: F401
from .reality_check import RealityCheck  # noqa: F401
from .kill_switch import KillSwitch, KillSwitchScope  # noqa: F401
from .ports import RoundVoidingPort, GeoPort  # noqa: F401
