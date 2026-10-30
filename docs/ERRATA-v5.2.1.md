# Errata v5.2.1

| Field | Value |
|---|---|
| Document | `docs/ERRATA-v5.2.1.md` |
| Applies to | BLUEPRINT v5.2 |
| Errata version | 5.2.1 |
| Status | Applied |
| Applied by | Architecture Lead |
| Commit tag | `blueprint-v5.2` (errata folded into v5.2 commit) |

This document records the seven corrections (E1–E7) folded into BLUEPRINT
v5.2. Each correction is self-contained: it cites the stale text, the
corrected text, the reason, and the authority (DEC or ADR) that governs
the correction.

---

## E1 — Removed stale "DEC-001 = business model" reference

**Stale text (v3.1 template, inherited by v4.0, v5.0, v5.1):**

> DEC-001 — B2B OS provider business model (Option A).

**Corrected text:**

> DEC-0024 — B2B OS provider business model (Option A) — HUMAN-APPROVED.

**Reason:** The v3.1 template reserved DEC-001 for the business model
decision. During the DEC re-seed for v5.2, the business model decision
was assigned DEC-0024 (the last slot in the seed), and DEC-0001 was
reassigned to "Adopt event-sourced domain model" (1:1 with ADR-0001).
The stale reference caused two distinct decisions to share an ID, which
would have violated linter rule 6 (ID uniqueness).

**Authority:** DEC-0024; ADR-DEC mapping law (DEC-0023).

**Locations updated:** BLUEPRINT §8 (DEC table); `traceability.md` §C
(DEC seed); `roles.md` RACI (business-model approver row); legacy
references in pre-v5.2 commit history (annotated but not rewritten).

---

## E2 — Removed stale "DEC-0022 = definitions" reference

**Stale text (Phase Plan Rev 2, inherited by v5.0, v5.1):**

> DEC-0022 — Semantic definitions: "application code"; DEC↔ADR mapping law.

**Corrected text:**

> DEC-0023 — Semantic definitions: "application code"; DEC↔ADR mapping law.
> DEC-0022 — Agent delivery schedule + shadow→live promotion gate (9 agents).

**Reason:** Phase Plan Rev 2 reserved DEC-0022 for the semantic-definitions
decision. During the v5.2 re-seed, the agent delivery schedule was given
DEC-0022 (to align with its appearance in §6 of the blueprint) and the
semantic-definitions decision was shifted to DEC-0023. The stale reference
would have caused the agent schedule and the mapping law to collide on
the same ID.

**Authority:** DEC-0022; DEC-0023.

**Locations updated:** BLUEPRINT §6, §8; `traceability.md` §C; all ADR
stubs whose rationale section previously cited "DEC-0022" for definitions
(none did at commit time, but the linter now enforces this going forward).

---

## E3 — Phase count corrected: 27 stages → 25 phases

**Stale text (v5.1, §5):**

> 26 phases derived from 27 stages.

**Corrected text:**

> 25 phases derived from 27 stages (two merges; see ADR-0021).

**Reason:** v5.1 undercounted the merges. The original 27-stage plan
contained two pairs of stages that the execution layer regrouped into
single phases:

1. Stage 7 (MFA) + Stage 8 (session management) → Phase 7.
2. Stage 22 (recon rules) + Stage 23 (recon runs) → Phase 22.

27 − 2 = 25, not 26. The arithmetic error was carried forward because
v5.1's phase table only listed the merged phases, not the count
difference.

**Authority:** DEC-0021; ADR-0021.

**Locations updated:** BLUEPRINT §5 (phase table) and §11 (acceptance
criteria, phase count reference); `stage-1-handoff.md` (Phase 2 entry
criteria reference the corrected count); `traceability.md` §C (DEC-0021
row's Decision column).

---

## E4 — Ledger phase clarified: Phase 11. First deposit ≥ Phase 12.

**Stale text (v5.1, §2):**

> Ledger deferred to a later phase.

**Corrected text:**

> Ledger (any posting, double-entry, or balance computation) — Phase 11.
> First customer deposit — Phase 12 or later.

**Reason:** v5.1 left the ledger and deposit phases ambiguous. Multiple
readings were possible ("later" could mean Phase 11 or Phase 25). The
triage rule in §9 requires unambiguous phase assignment for any
out-of-Increment-1 capability; the ambiguity violated that rule.

**Authority:** DEC-0021; triage rule (BLUEPRINT §9).

**Locations updated:** BLUEPRINT §2 (scope of Increment 1) and §5 (phase
table); `scope.md` (out-of-scope list); `triage-table.md` (workflow rows
for ledger posting and customer deposit).

---

## E5 — Agent count fixed: 9 agents (not 8)

**Stale text (v5.0, v5.1, §6):**

> Eight delivery agents operate on a fixed schedule.

**Corrected text:**

> Nine delivery agents operate on a fixed schedule.

**Reason:** The agent roster was finalised at nine members during the
DEC-0022 review. v5.0 was drafted before the ninth agent (the
"compliance evidence collector") was added, and v5.1 failed to propagate
the update. The promotion gate definition in DEC-0022 is unchanged; only
the count is corrected.

**Authority:** DEC-0022.

**Locations updated:** BLUEPRINT §6 (agent count); `roles.md` (agent
owner roster); `stage-1-handoff.md` (Phase 2 agent eligibility reference).

---

## E6 — REQ count reconciled: 24 + 12 + 26 = 62 minimum (not 60)

**Stale text (v5.1, §7):**

> 24 Law-REQs + 12 Pain-REQs + 24 MB-REQs = 60 minimum.

**Corrected text:**

> 24 Law-REQs + 12 Pain-REQs + 26 MB-REQs = 62 minimum.

**Reason:** v5.1 undercounted module-boundary REQs by two. The seed in
`traceability.md` §B has always carried 26 MB-REQs (the last two —
MB-REQ-0025 "Read models can be rebuilt from event log" and MB-REQ-0026
"No domain logic in infrastructure adapters" — were added during the
v5.0 review but not propagated to the count in §7). The arithmetic was
corrected to match the seeded rows.

**Authority:** BLUEPRINT §7; `traceability.md` §B (authority for the
seeded rows).

**Locations updated:** BLUEPRINT §7 (REQ count) and §11 (acceptance
criteria, REQ count); `traceability.md` §B (caption confirming the 62
floor); `stage-1-handoff.md` (REQ count reference).

---

## E7 — ADR-DEC mapping law clarified: front-matter `DEC: DEC-00XX`

**Stale text (v5.1, §8):**

> Every ADR cites exactly one DEC.

**Corrected text:**

> Every ADR file under `docs/adr/` MUST cite exactly one DEC in its YAML
> front-matter, in the form `DEC: DEC-00XX`.

**Reason:** v5.1's wording did not specify where the citation must live
or in what format. Multiple readings were possible (citation in body
text, citation in filename, citation in title). The clarification
requires the citation to be in YAML front-matter under the `DEC` key, in
the literal form `DEC: DEC-00XX` (four-digit zero-padded). This is the
format the linter (rule 7) parses.

**Authority:** DEC-0023; linter rule 7.

**Locations updated:** BLUEPRINT §3 (glossary entry for "ADR-DEC mapping
law"), §8 (mapping law wording); every ADR stub under `docs/adr/`
(front-matter `DEC:` field); `scripts/check_traceability.sh` (rule 7
parser).

---

## Application order

The errata were applied as a single commit. They are listed here in
dependency order: E1 and E2 must be applied before E7 (the mapping law
clarification depends on the DEC ID assignments being stable); E3, E4,
E5, and E6 are independent and may be applied in any order. The commit
message format is:

```
blueprint v5.2: seed Phase 1 governed foundation

Apply errata v5.2.1 (E1–E7).
- E1: supersede DEC-001= business model → DEC-0024
- E2: supersede DEC-0022= definitions → DEC-0023
- E3: 27 stages → 25 phases (was 26)
- E4: Ledger = Phase 11; first deposit ≥ Phase 12
- E5: 9 agents (was 8)
- E6: 62 REQs minimum (was 60)
- E7: ADR front-matter `DEC: DEC-00XX` is mandatory

Tag: blueprint-v5.2
```

The git tag `blueprint-v5.2` is applied to the same commit. The errata
commit is `errata-v5.2.1` (separate annotated tag) on the same SHA to
preserve the errata identity for audit purposes.
