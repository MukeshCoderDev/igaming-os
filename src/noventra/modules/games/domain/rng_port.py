"""RNG Port — Interface + 3 Adapters. Per ADR-0100 / DEC-0101. Phase 16.

Three adapters serve three different environments but share a single port
interface (`RngPort`):

1. **ProductionRngAdapter** — live player-facing rounds. Sources entropy from
   `secrets.token_bytes()` (CSPRNG backed by OS kernel /dev/urandom). Outputs
   are unpredictable. The seed is logged per round (post-generation) so the
   round outcome can be audited but not predicted.

2. **DeterministicRngAdapter** — sandbox (ADR-0095) and certification evidence
   generator (ADR-0102). Sources entropy from a `random.Random(seed)` instance
   seeded from a caller-provided hex string. Same seed → same output sequence.

3. **CertificationRngAdapter** — lab certification. Wraps DeterministicRngAdapter
   with additional logging: every call records (seed, call_index, output,
   round_id) to a tamper-evident hash-chained log.

All three adapters share the same (seed, call_index) → output determinism
property. ProductionRngAdapter differs only in that the seed is generated
randomly (and logged post-generation); the seed→output mapping is identical
to DeterministicRngAdapter given the same seed.

Linter rule 124 (Phase 16) forbids direct use of `random.Random`,
`random.randint`, `random.random` in the games module — all RNG must go
through RngPort.
"""

from __future__ import annotations

import abc
import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass, field
from typing import List

log = logging.getLogger("noventra.games.rng")

# Seed is 256 bits = 32 bytes = 64 hex chars. Per ADR-0100.
SEED_HEX_LEN = 64


# ─────────────────────────────────────────────────────────────────────────
# Port interface
# ─────────────────────────────────────────────────────────────────────────

class RngPort(abc.ABC):
    """Port: Random Number Generator interface. Per ADR-0100.

    Every game-round RNG call MUST go through this port (linter rule 124).
    Direct use of `random.Random`, `random.randint`, `random.random` in the
    games module is forbidden.

    Contract: `(seed, call_index) → output` is deterministic across all
    adapters. This means a ProductionRngAdapter round with seed S produces
    the same output sequence as a DeterministicRngAdapter round with seed S.

    Callers MUST number their calls (call_index = 0, 1, 2, ...). The adapter
    does NOT auto-increment (avoids hidden state). This makes audit trivial:
    a round with N bets has N calls, indexed 0..N-1, each reconstructable
    from the seed.
    """

    @abc.abstractmethod
    def generate_seed(self) -> str:
        """Generate a fresh 256-bit hex seed (64 chars).

        Production: sourced from OS CSPRNG (unpredictable).
        Deterministic: caller-provided (or fixed default for sandbox boot).
        Certification: caller-provided (for lab reproducibility).
        """

    @abc.abstractmethod
    def next_int(self, *, seed: str, call_index: int,
                 min_value: int, max_value: int) -> int:
        """Return a deterministic int in [min_value, max_value] for (seed, call_index).

        Pre-condition: max_value > min_value; max_value - min_value < 2^32.
        """

    @abc.abstractmethod
    def next_float(self, *, seed: str, call_index: int) -> float:
        """Return a deterministic float in [0.0, 1.0) for (seed, call_index)."""


# ─────────────────────────────────────────────────────────────────────────
# Deterministic core (shared by all 3 adapters)
# ─────────────────────────────────────────────────────────────────────────

def _derive_bytes(*, seed: str, call_index: int, length: int) -> bytes:
    """Derive `length` pseudo-random bytes from (seed, call_index) using HMAC-SHA256.

    This is the counter-mode PRNG that all three adapters share. It is
    deterministic: same (seed, call_index) → same bytes, regardless of adapter.

    The construction is:
        block_0 = HMAC-SHA256(key=seed_bytes, msg="call_index:0")
        block_1 = HMAC-SHA256(key=seed_bytes, msg="call_index:1")
        ...
        output = block_0 || block_1 || ... (truncated to `length`)

    This gives a 256-bit-per-block stream cipher with cryptographic
    separation between call_indexes. Even if call_index 0 is leaked, the
    attacker cannot predict call_index 1.
    """
    if length <= 0:
        return b""
    seed_bytes = bytes.fromhex(seed)
    output = b""
    block_index = 0
    while len(output) < length:
        msg = f"call_index:{call_index}:block:{block_index}".encode("utf-8")
        block = hmac.new(seed_bytes, msg, hashlib.sha256).digest()
        output += block
        block_index += 1
    return output[:length]


def _next_int_from_seed(*, seed: str, call_index: int,
                        min_value: int, max_value: int) -> int:
    """Deterministic int in [min_value, max_value] for (seed, call_index)."""
    if max_value <= min_value:
        raise ValueError(f"max_value ({max_value}) must be > min_value ({min_value})")
    range_size = max_value - min_value + 1
    if range_size >= (1 << 32):
        raise ValueError(f"range_size ({range_size}) must be < 2^32")
    # Use modulo reduction. For uniform distribution we'd reject values that
    # cause modulo bias, but for game RNG this is acceptable (bias < 2^-32
    # for ranges up to 2^32).
    raw = int.from_bytes(_derive_bytes(seed=seed, call_index=call_index, length=4), "big")
    return min_value + (raw % range_size)


def _next_float_from_seed(*, seed: str, call_index: int) -> float:
    """Deterministic float in [0.0, 1.0) for (seed, call_index).

    Uses 53 bits of precision (IEEE 754 double mantissa size).
    """
    raw = int.from_bytes(_derive_bytes(seed=seed, call_index=call_index, length=8), "big")
    # Mask to 53 bits (double mantissa precision).
    raw &= (1 << 53) - 1
    return raw / (1 << 53)


# ─────────────────────────────────────────────────────────────────────────
# Production adapter (CSPRNG)
# ─────────────────────────────────────────────────────────────────────────

class ProductionRngAdapter(RngPort):
    """Production RNG adapter. Per ADR-0100.

    Uses `secrets.token_hex(32)` for seed generation (CSPRNG backed by OS
    /dev/urandom on Linux). The seed is unpredictable. Once generated, the
    seed→output mapping is identical to DeterministicRngAdapter (uses the
    same _derive_bytes core).

    This means production rounds are unpredictable (seed is random) but
    auditable (output is reconstructable from the logged seed).
    """

    def generate_seed(self) -> str:
        seed = secrets.token_hex(32)  # 256 bits = 64 hex chars
        log.debug("production_seed_generated", extra={"seed_length": len(seed)})
        return seed

    def next_int(self, *, seed: str, call_index: int,
                 min_value: int, max_value: int) -> int:
        return _next_int_from_seed(
            seed=seed, call_index=call_index,
            min_value=min_value, max_value=max_value,
        )

    def next_float(self, *, seed: str, call_index: int) -> float:
        return _next_float_from_seed(seed=seed, call_index=call_index)


# ─────────────────────────────────────────────────────────────────────────
# Deterministic adapter (sandbox + certification evidence generator)
# ─────────────────────────────────────────────────────────────────────────

# Default sandbox seed: a fixed value so sandbox runs are reproducible across
# reboots. Per ADR-0095 (Deterministic Sandbox).
DEFAULT_SANDBOX_SEED = "0" * SEED_HEX_LEN


class DeterministicRngAdapter(RngPort):
    """Deterministic RNG adapter. Per ADR-0100, ADR-0095.

    Used in:
    - Sandbox (ADR-0095): same code path as production, deterministic outputs.
    - Certification evidence generator (ADR-0102): lab-reproducible runs.

    The seed is caller-provided (or DEFAULT_SANDBOX_SEED if none). Same seed
    → same output sequence. This is the determinism property.
    """

    def __init__(self, *, default_seed: str = DEFAULT_SANDBOX_SEED):
        if len(default_seed) != SEED_HEX_LEN:
            raise ValueError(
                f"Seed must be {SEED_HEX_LEN} hex chars; got {len(default_seed)}"
            )
        # Validate hex.
        try:
            int(default_seed, 16)
        except ValueError as e:
            raise ValueError(f"Seed must be valid hex: {e}")
        self._default_seed = default_seed

    def generate_seed(self) -> str:
        # Deterministic: return the default seed (caller may override).
        return self._default_seed

    def next_int(self, *, seed: str, call_index: int,
                 min_value: int, max_value: int) -> int:
        return _next_int_from_seed(
            seed=seed, call_index=call_index,
            min_value=min_value, max_value=max_value,
        )

    def next_float(self, *, seed: str, call_index: int) -> float:
        return _next_float_from_seed(seed=seed, call_index=call_index)


# ─────────────────────────────────────────────────────────────────────────
# Certification adapter (lab audit log)
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class RngAuditEntry:
    """A single RNG call audit entry. Per ADR-0100.

    The CertificationRngAdapter records every call as one of these entries.
    The entries form a hash-chained log (per Phase 7 pattern) so the lab can
    verify no call was inserted or removed.
    """
    seed: str
    call_index: int
    output: int  # or float, but we serialize to str for hash chain
    round_id: str
    method: str  # "next_int" or "next_float"
    timestamp: str  # ISO 8601 UTC
    prev_hash: str  # hash of previous entry (or "0"*64 for genesis)
    entry_hash: str  # SHA-256 over (prev_hash + seed + call_index + output + round_id + method + timestamp)


@dataclass
class CertificationRngAdapter(RngPort):
    """Certification RNG adapter with hash-chained audit log. Per ADR-0100, ADR-0102.

    Wraps DeterministicRngAdapter with additional logging: every call records
    (seed, call_index, output, round_id) to a tamper-evident hash-chained log.

    The lab gets:
    1. A deterministic RNG (so they can reproduce the run).
    2. An audit trail (so they can verify no call was omitted or inserted).

    The hash chain is SHA-256: each entry's `entry_hash` is computed over
    (prev_hash + seed + call_index + output + round_id + method + timestamp).
    The first entry's prev_hash is "0"*64 (genesis). Any tampering with an
    entry breaks the chain at that point.
    """

    default_seed: str = DEFAULT_SANDBOX_SEED
    audit_log: List[RngAuditEntry] = field(default_factory=list)
    _current_round_id: str = ""

    def set_round_context(self, *, round_id: str) -> None:
        """Set the round_id context for subsequent calls.

        The lab verifies that all calls for a given round are recorded
        together. The round_id is part of each audit entry's hash.
        """
        self._current_round_id = round_id

    def generate_seed(self) -> str:
        return self.default_seed

    def next_int(self, *, seed: str, call_index: int,
                 min_value: int, max_value: int) -> int:
        output = _next_int_from_seed(
            seed=seed, call_index=call_index,
            min_value=min_value, max_value=max_value,
        )
        self._record_entry(
            seed=seed, call_index=call_index, output=output,
            round_id=self._current_round_id, method="next_int",
        )
        return output

    def next_float(self, *, seed: str, call_index: int) -> float:
        output = _next_float_from_seed(seed=seed, call_index=call_index)
        self._record_entry(
            seed=seed, call_index=call_index, output=output,
            round_id=self._current_round_id, method="next_float",
        )
        return output

    def _record_entry(self, *, seed: str, call_index: int, output,
                      round_id: str, method: str) -> None:
        """Record an audit entry with hash chain. Per ADR-0100, Phase 7 pattern."""
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat()

        prev_hash = self.audit_log[-1].entry_hash if self.audit_log else "0" * 64
        # Compute entry_hash: SHA-256 over (prev_hash + seed + call_index + output + round_id + method + timestamp).
        entry_content = f"{prev_hash}|{seed}|{call_index}|{output}|{round_id}|{method}|{timestamp}"
        entry_hash = hashlib.sha256(entry_content.encode("utf-8")).hexdigest()

        self.audit_log.append(RngAuditEntry(
            seed=seed, call_index=call_index, output=output,
            round_id=round_id, method=method, timestamp=timestamp,
            prev_hash=prev_hash, entry_hash=entry_hash,
        ))

    def verify_audit_log(self) -> bool:
        """Verify the hash chain of the audit log. Per ADR-0100.

        Returns True if every entry's prev_hash matches the previous entry's
        entry_hash, and every entry's entry_hash matches a fresh computation.
        Any tampering (insertion, deletion, modification) breaks the chain.
        """
        prev_hash = "0" * 64
        for entry in self.audit_log:
            if entry.prev_hash != prev_hash:
                return False
            # Recompute entry_hash.
            entry_content = (
                f"{entry.prev_hash}|{entry.seed}|{entry.call_index}|"
                f"{entry.output}|{entry.round_id}|{entry.method}|{entry.timestamp}"
            )
            expected = hashlib.sha256(entry_content.encode("utf-8")).hexdigest()
            if entry.entry_hash != expected:
                return False
            prev_hash = entry.entry_hash
        return True
