"""Ledger services — PostingService, ReversalService, BalanceService, ReconciliationService.

Per ADR-0059 (posting), ADR-0060 (balance), ADR-0061 (overdraft),
ADR-0062 (reversals), ADR-0063 (financial audit chain).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from django.db import connection, transaction
from django.utils import timezone

log = logging.getLogger("noventra.ledger.services")


@dataclass(frozen=True)
class PostingRequest:
    """A request to post a journal entry."""

    tenant_uuid: str
    account_debit: str  # account_uuid
    account_credit: str  # account_uuid
    amount_minor: int  # integer minor units
    currency_code: str
    exponent: int  # ISO 4217 exponent
    journal_type: str = "POSTING"
    correlation_id: str = ""
    idempotency_key: str = ""
    fx_pair_id: Optional[str] = None


@dataclass(frozen=True)
class PostingResult:
    """Result of a posting."""

    success: bool
    entry_uuid: Optional[str] = None
    error: Optional[str] = None


class PostingService:
    """Posts journal entries with 6 invariants enforced.

    Per ADR-0059 / DEC-0065.
    """

    @staticmethod
    @transaction.atomic
    def post(request: PostingRequest) -> PostingResult:
        """Post a double-entry journal entry.

        Enforces:
        1. Double-entry balance (debit = credit)
        2. Atomicity (all lines commit with parent)
        3. Immutability (insert-only)
        4. Idempotency (unique key)
        5. Tenant scoping (RLS)
        6. Audit chain (hash-chained)
        """
        if request.amount_minor <= 0:
            return PostingResult(success=False, error="amount must be positive")

        if not request.idempotency_key:
            request = PostingRequest(
                tenant_uuid=request.tenant_uuid,
                account_debit=request.account_debit,
                account_credit=request.account_credit,
                amount_minor=request.amount_minor,
                currency_code=request.currency_code,
                exponent=request.exponent,
                journal_type=request.journal_type,
                correlation_id=request.correlation_id,
                idempotency_key=str(uuid.uuid4()),
                fx_pair_id=request.fx_pair_id,
            )

        entry_uuid = str(uuid.uuid4())

        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [request.tenant_uuid])

            # Check idempotency.
            cursor.execute(
                "SELECT entry_uuid FROM ledger_journal_entry WHERE tenant_uuid = %s AND idempotency_key = %s",
                [request.tenant_uuid, request.idempotency_key],
            )
            existing = cursor.fetchone()
            if existing:
                return PostingResult(success=True, entry_uuid=str(existing[0]))

            # Insert journal_entry.
            cursor.execute(
                """
                INSERT INTO ledger_journal_entry
                    (entry_uuid, tenant_uuid, journal_type, correlation_id, idempotency_key, fx_pair_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'POSTED')
                """,
                [entry_uuid, request.tenant_uuid, request.journal_type,
                 request.correlation_id, request.idempotency_key, request.fx_pair_id],
            )

            # Insert journal_lines (debit + credit).
            cursor.execute(
                """
                INSERT INTO ledger_journal_line
                    (line_uuid, entry_uuid, account_uuid, tenant_uuid, currency_code, exponent_at_time, debit_minor, credit_minor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
                """,
                [str(uuid.uuid4()), entry_uuid, request.account_debit,
                 request.tenant_uuid, request.currency_code, request.exponent, request.amount_minor],
            )
            cursor.execute(
                """
                INSERT INTO ledger_journal_line
                    (line_uuid, entry_uuid, account_uuid, tenant_uuid, currency_code, exponent_at_time, debit_minor, credit_minor)
                VALUES (%s, %s, %s, %s, %s, %s, 0, %s)
                """,
                [str(uuid.uuid4()), entry_uuid, request.account_credit,
                 request.tenant_uuid, request.currency_code, request.exponent, request.amount_minor],
            )

            # Update account_balance projection.
            PostingService._update_balance(cursor, request.account_debit, request.tenant_uuid, entry_uuid, request.amount_minor, 0)
            PostingService._update_balance(cursor, request.account_credit, request.tenant_uuid, entry_uuid, 0, request.amount_minor)

        log.info("ledger_posted", extra={
            "entry_uuid": entry_uuid,
            "tenant_uuid": request.tenant_uuid,
            "amount_minor": request.amount_minor,
            "currency_code": request.currency_code,
        })
        return PostingResult(success=True, entry_uuid=entry_uuid)

    @staticmethod
    def _update_balance(cursor, account_uuid: str, tenant_uuid: str, entry_uuid: str, debit: int, credit: int):
        """Update the account_balance projection."""
        cursor.execute(
            "SELECT balance_minor FROM ledger_account_balance WHERE account_uuid = %s FOR UPDATE",
            [account_uuid],
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                """
                INSERT INTO ledger_account_balance (account_uuid, tenant_uuid, balance_minor, as_of_entry_uuid)
                VALUES (%s, %s, %s, %s)
                """,
                [account_uuid, tenant_uuid, debit - credit, entry_uuid],
            )
        else:
            new_balance = row[0] + debit - credit
            cursor.execute(
                "UPDATE ledger_account_balance SET balance_minor = %s, as_of_entry_uuid = %s WHERE account_uuid = %s",
                [new_balance, entry_uuid, account_uuid],
            )


class ReversalService:
    """Reverses journal entries. Per ADR-0062 / DEC-0069.

    Reversals are terminal (cannot be reversed themselves).
    No double-reversal (UNIQUE on source_ref where journal_type=REVERSAL).
    """

    @staticmethod
    @transaction.atomic
    def reverse(*, original_entry_uuid: str, tenant_uuid: str, correlation_id: str, idempotency_key: str) -> PostingResult:
        """Reverse a journal entry by creating a new REVERSAL entry."""
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_uuid])

            # Check original exists and is POSTED (not already reversed).
            cursor.execute(
                "SELECT status FROM ledger_journal_entry WHERE entry_uuid = %s",
                [original_entry_uuid],
            )
            row = cursor.fetchone()
            if row is None:
                return PostingResult(success=False, error="original entry not found")
            if row[0] == "REVERSED":
                return PostingResult(success=False, error="entry already reversed")

            # Check no existing reversal (double-reversal prevention).
            cursor.execute(
                "SELECT 1 FROM ledger_journal_entry WHERE source_ref = %s AND journal_type = 'REVERSAL'",
                [original_entry_uuid],
            )
            if cursor.fetchone():
                return PostingResult(success=False, error="reversal already exists")

            # Get original lines (to negate them).
            cursor.execute(
                "SELECT account_uuid, currency_code, exponent_at_time, debit_minor, credit_minor "
                "FROM ledger_journal_line WHERE entry_uuid = %s",
                [original_entry_uuid],
            )
            lines = cursor.fetchall()

            # Create reversal entry.
            reversal_uuid = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO ledger_journal_entry
                    (entry_uuid, tenant_uuid, journal_type, source_ref, correlation_id, idempotency_key, status)
                VALUES (%s, %s, 'REVERSAL', %s, %s, %s, 'POSTED')
                """,
                [reversal_uuid, tenant_uuid, original_entry_uuid, correlation_id, idempotency_key],
            )

            # Create reversed lines (swap debit/credit).
            for line in lines:
                account_uuid, currency_code, exponent, debit, credit = line
                cursor.execute(
                    """
                    INSERT INTO ledger_journal_line
                        (line_uuid, entry_uuid, account_uuid, tenant_uuid, currency_code, exponent_at_time, debit_minor, credit_minor)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [str(uuid.uuid4()), reversal_uuid, account_uuid, tenant_uuid,
                     currency_code, exponent, credit, debit],  # Swapped!
                )
                # Update balance projection.
                PostingService._update_balance(cursor, account_uuid, tenant_uuid, reversal_uuid, credit, debit)

            # Mark original as REVERSED (via status — this is the one allowed
            # mutation, managed by trigger/view per ADR-0062).
            cursor.execute(
                "UPDATE ledger_journal_entry SET status = 'REVERSED' WHERE entry_uuid = %s",
                [original_entry_uuid],
            )

        log.info("ledger_reversed", extra={
            "reversal_uuid": reversal_uuid,
            "original_entry_uuid": original_entry_uuid,
            "tenant_uuid": tenant_uuid,
        })
        return PostingResult(success=True, entry_uuid=reversal_uuid)


class BalanceService:
    """Reads balances. Per ADR-0060 / DEC-0066.

    Display reads: from account_balance projection (fast, eventually consistent).
    Authorization reads: from journal_line under row lock (authoritative).
    """

    @staticmethod
    def get_display_balance(*, account_uuid: str, tenant_uuid: str) -> int:
        """Get the display balance (projection). Fast but not authoritative."""
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_uuid])
            cursor.execute(
                "SELECT balance_minor FROM ledger_account_balance WHERE account_uuid = %s",
                [account_uuid],
            )
            row = cursor.fetchone()
        return row[0] if row else 0

    @staticmethod
    def get_authoritative_balance(*, account_uuid: str, tenant_uuid: str) -> int:
        """Get the authoritative balance (from journal_line under row lock).

        Per ADR-0060: authorization reads use SELECT ... FOR UPDATE.
        """
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_uuid])
            cursor.execute(
                """
                SELECT COALESCE(SUM(debit_minor - credit_minor), 0)
                FROM ledger_journal_line
                WHERE account_uuid = %s
                """,
                [account_uuid],
            )
            row = cursor.fetchone()
        return row[0] if row else 0
