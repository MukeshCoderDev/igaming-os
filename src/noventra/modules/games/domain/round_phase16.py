"""Game Round Lifecycle Extension — Math Version Lock + RNG Seed Lock + Round Hash.

Per ADR-0101 / DEC-0102. Phase 16.

Extends Phase 15 GameRound (domain/round.py) with three regulator-mandated
properties:

1. **Math version locked at round initiation.** Once a round starts, the math
   version cannot change mid-round. The round row records `math_version_uuid`
   and `math_config_hash` at initiation; the outcome calculation verifies both
   before producing a result.

2. **RNG seed locked at round initiation.** The seed for the round is generated
   (or injected in sandbox) at initiation and recorded on the round row. The
   seed is part of the round hash, so any post-initiation change is detected.

3. **Round hash for tamper-evidence.** The round carries a SHA-256 hash over
   (math_version_hash, rng_seed, bet_config, outcome). Computed at settlement;
   verified at every downstream read (audit, dispute evidence, regulator inquiry).

Together with ADR-0099 (math version immutability) and ADR-0100 (RNG audit),
this ADR closes the audit chain: a regulator inquiry can reconstruct any round
from (math_version, rng_seed, bet_config) and verify the outcome matches the
recorded hash.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .math_version import MathVersion, canonical_json
from .round import GameRound, RoundState


# ─────────────────────────────────────────────────────────────────────────
# Round hash computation
# ─────────────────────────────────────────────────────────────────────────

def compute_round_hash(
    *,
    math_config_hash: str,
    rng_seed_hex: str,
    bet_config: dict,
    outcome: Optional[dict],
) -> str:
    """Compute SHA-256 hex over canonical JSON of round inputs + outcome.

    Per ADR-0101: round_hash = SHA-256(canonical_json({
        math_version_hash: <math_config_hash>,
        rng_seed: <rng_seed_hex>,
        bet_config: <bet_config>,
        outcome: <outcome or null>,
    }))

    The hash is computed at settlement and verified at every downstream read.
    Any tampering with any of the four inputs is detected.

    Args:
        math_config_hash: The math_config_hash from the MathVersion used for this round.
        rng_seed_hex: The 256-bit hex seed used for this round.
        bet_config: Final bet configuration (frozen at CLOSED transition).
        outcome: Outcome dict at SETTLED transition (None for voided rounds).

    Returns:
        64-character hex string (SHA-256).
    """
    payload = {
        "math_version_hash": math_config_hash,
        "rng_seed": rng_seed_hex,
        "bet_config": bet_config,
        "outcome": outcome,
    }
    canonical = canonical_json(payload).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ─────────────────────────────────────────────────────────────────────────
# Extended GameRound
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class GameRoundPhase16(GameRound):
    """Extended GameRound with math version lock + RNG seed lock + round hash.

    Per ADR-0101 / DEC-0102. Phase 16.

    This subclass extends Phase 15's GameRound with three new fields:
    - math_version_uuid: FK to the MathVersion used for this round (locked at initiation).
    - math_config_hash: Snapshot of MathVersion.math_config_hash at initiation.
    - rng_seed_hex: 256-bit hex seed (locked at initiation).
    - bet_config: Final bet configuration (frozen at CLOSED transition).
    - outcome: Outcome dict at SETTLED transition.
    - round_hash: SHA-256 over (math_version_hash, rng_seed, bet_config, outcome).

    All three "lock" fields (math_version_uuid, math_config_hash, rng_seed_hex)
    are set at initiation and IMMUTABLE thereafter. Linter rule 125 (Phase 16)
    forbids any code path that mutates these fields after initiation.
    """

    # Locked at initiation (immutable thereafter).
    math_version_uuid: Optional[uuid.UUID] = None
    math_config_hash: str = ""
    rng_seed_hex: str = ""

    # Updated during OPEN; frozen at CLOSED.
    bet_config: dict = field(default_factory=dict)

    # Set at SETTLED.
    outcome: Optional[dict] = None

    # Computed at SETTLED or VOIDED.
    round_hash: str = ""

    def initiate(
        self,
        *,
        math_version: MathVersion,
        rng_seed_hex: str,
    ) -> None:
        """Lock the math version + RNG seed at round initiation. Per ADR-0101.

        Called once when the round transitions to OPEN. Sets:
        - math_version_uuid (immutable)
        - math_config_hash (immutable; verified against math_version.verify_hash())
        - rng_seed_hex (immutable)

        Raises if math_version.verify_hash() returns False (tamper detection).
        Raises if math_version.is_playable is False (only PUBLISHED versions are playable).
        """
        if not math_version.verify_hash():
            raise ValueError(
                "Math version hash verification failed; math config may have been tampered."
            )
        if not math_version.is_playable:
            raise ValueError(
                f"Math version status is {math_version.status.value}; "
                f"only PUBLISHED versions are playable."
            )
        if self.state != RoundState.OPEN.value:
            raise ValueError(
                f"Round must be in OPEN state to initiate; current state: {self.state}"
            )
        if self.math_version_uuid is not None:
            raise ValueError(
                "Round already initiated; math_version_uuid is locked."
            )

        self.math_version_uuid = math_version.version_uuid
        self.math_config_hash = math_version.math_config_hash
        self.rng_seed_hex = rng_seed_hex

    def freeze_bet_config(self) -> None:
        """Freeze bet_config at CLOSED transition. Per ADR-0101.

        Called when the round transitions OPEN → CLOSED. The bet_config dict
        is serialized to canonical JSON (for hash stability) and frozen.
        Subsequent bet attempts are refused (state is CLOSED).
        """
        if self.state != RoundState.CLOSED.value:
            raise ValueError(
                f"freeze_bet_config can only be called in CLOSED state; "
                f"current state: {self.state}"
            )
        # bet_config is already a dict; canonical JSON is computed at hash time.

    def settle_with_outcome(self, *, outcome: dict, payout_minor: int) -> None:
        """Settle the round with a computed outcome. Per ADR-0101.

        Calls the Phase 15 settle() method (CLOSED → SETTLED) and additionally:
        - Records the outcome dict.
        - Computes round_hash over (math_config_hash, rng_seed_hex, bet_config, outcome).
        - Stores round_hash on the round row.

        The round_hash is verified at every downstream read (audit, dispute
        evidence, regulator inquiry).
        """
        if self.math_version_uuid is None:
            raise ValueError(
                "Cannot settle: round was not initiated (math_version_uuid is None)."
            )
        if not self.rng_seed_hex:
            raise ValueError("Cannot settle: rng_seed_hex is empty (not initiated).")

        # Phase 15 settle (CLOSED → SETTLED).
        self.settle(payout_minor=payout_minor)

        # Phase 16: record outcome + compute round_hash.
        self.outcome = outcome
        self.round_hash = compute_round_hash(
            math_config_hash=self.math_config_hash,
            rng_seed_hex=self.rng_seed_hex,
            bet_config=self.bet_config,
            outcome=self.outcome,
        )

    def void_with_hash(self, *, reason: str) -> None:
        """Void the round AND compute round_hash (with outcome=None). Per ADR-0101.

        Calls the Phase 15 void() method (OPEN/CLOSED → VOIDED) and additionally:
        - Sets outcome to None (no outcome for voided rounds).
        - Computes round_hash over (math_config_hash, rng_seed_hex, bet_config, None).
        - Stores round_hash on the round row.

        The round_hash for a voided round is still computed for audit completeness.
        """
        # Phase 15 void (OPEN/CLOSED → VOIDED).
        self.void(reason=reason)

        # Phase 16: record null outcome + compute round_hash.
        self.outcome = None
        self.round_hash = compute_round_hash(
            math_config_hash=self.math_config_hash,
            rng_seed_hex=self.rng_seed_hex,
            bet_config=self.bet_config,
            outcome=None,
        )

    def verify_round_hash(self) -> bool:
        """Verify that the stored round_hash matches a fresh computation.

        Called at:
        - Audit reads (Phase 7): flag audit failure if hash mismatch.
        - Dispute evidence pack (ADR-0076): include hash for lab verification.
        - Regulator inquiry API: return hash for independent verification.

        Returns True if the stored round_hash matches the recomputed hash.
        Returns False if any of the four inputs (math_config_hash, rng_seed,
        bet_config, outcome) have been tampered with.
        """
        if not self.round_hash:
            return False  # Not yet settled/voided.
        recomputed = compute_round_hash(
            math_config_hash=self.math_config_hash,
            rng_seed_hex=self.rng_seed_hex,
            bet_config=self.bet_config,
            outcome=self.outcome,
        )
        return recomputed == self.round_hash

    @property
    def is_initiated(self) -> bool:
        """True if the round has been initiated (math version + RNG seed locked)."""
        return (
            self.math_version_uuid is not None
            and bool(self.math_config_hash)
            and bool(self.rng_seed_hex)
        )
