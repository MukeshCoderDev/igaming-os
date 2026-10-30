# Security Architecture — STRIDE Threat Model

| Field | Value |
|---|---|
| Document | `docs/architecture/security.md` |
| Version | 5.3 (Phase 2) |
| Status | Approved |
| Owner | Security Lead |
| Authority | DEC-0025; STRIDE (Microsoft, 1999) |
| Scope | Phase 2 stub; full depth deferred to Phase 24 |

This document records the Phase 2 STRIDE threat model across the
five platform external surfaces: **player API**, **partner API**,
**admin**, **webhooks**, **realtime**. Vendor surfaces are recorded
in `risk-register.md` §3 (vendor risk). Full threat-model depth
(attack trees, exploit chains, control catalog mapping) is deferred
to Phase 24 per the Phase 2 hard acceptance.

## 1. Surface inventory

The five external surfaces are the only places where untrusted input
enters the platform. Every other interaction is internal and
service-to-service (mTLS, short-lived tokens).

| Surface | Audience | Protocol | Auth | Phase 2 status |
|---|---|---|---|---|
| **Player API** | End users of tenant applications (the "players" on tenant customer platforms) | HTTPS / JSON | OIDC bearer token (DEC-0004) | Stub; full def. Phase 4 |
| **Partner API** | Tenant integrators and B2B partners | HTTPS / JSON; mTLS optional | OIDC + API key; mTLS for high-trust partners | Stub; full def. Phase 4 |
| **Admin** | Tenant admins and platform operators | HTTPS / JSON | OIDC + MFA enforced; RBAC with delegation (DEC-0015) | Stub; full def. Phase 5 |
| **Webhooks** | Outbound to tenant-configured endpoints | HTTPS POST | HMAC signature; retry with backoff | Stub; full def. Phase 6 |
| **Realtime** | Realtime event stream to tenant clients (e.g., balance updates, audit events) | WebSocket / SSE | OIDC bearer token; per-tenant channel | Stub; full def. Phase 7 |

## 2. STRIDE overview

STRIDE categorizes threats into six classes. The Phase 2 stub
requires ≥1 finding per category per surface (5 surfaces × 6
categories = 30 minimum findings). Findings below are stubs; each
will be expanded in Phase 24 with attack trees, control mappings,
and residual-risk ratings.

| Class | Property violated | Typical controls |
|---|---|---|
| **S**poofing | Authentication | MFA, mTLS, short-lived tokens, replay protection |
| **T**ampering | Integrity | Hash chains (DEC-0007), signatures, RLS (DEC-0003), input validation |
| **R**epudiation | Non-repudiation | Audit log (DEC-0006), signed webhooks, idempotency keys (DEC-0008) |
| **I**nformation disclosure | Confidentiality | Encryption at rest (NFR §1.1) and in transit (NFR §1.2); RLS; least privilege |
| **D**enial of service | Availability | Rate limiting (Pain-REQ-0008), backpressure (MB-REQ-0014), circuit breakers (MB-REQ-0015) |
| **E**levation of privilege | Authorization | RBAC with delegation (DEC-0015), tenant isolation (DEC-0003), boundary flag eval (DEC-0016) |

## 3. Player API — STRIDE findings

| ID | Class | Threat (stub) | Control (stub) | Phase 24 expansion |
|---|---|---|---|---|
| PA-S-01 | Spoofing | Stolen bearer token replayed from a different IP / device | Short token lifetime (≤1h); refresh-token rotation; optional device binding | Attack tree; control effectiveness rating |
| PA-T-01 | Tampering | Malicious tenant modifies request body after signing | mTLS for high-trust tenants; request signing for sensitive mutations | Tamper-detection coverage map |
| PA-R-01 | Repudiation | User denies initiating a transaction; no audit trail of the API call | Every mutation appends to audit log (DEC-0006) with actor + request hash | Audit-log completeness test plan |
| PA-I-01 | Information disclosure | API response leaks another tenant's data via nested serializer | RLS (DEC-0003); serializer field filtering per role; integration tests | Field-level disclosure test matrix |
| PA-D-01 | Denial of service | Tenant floods API with requests; degrades service for others | Per-tenant rate limit (Pain-REQ-0008); backpressure (MB-REQ-0014); circuit breaker on downstream | Load-test plan; throttle tuning guide |
| PA-E-01 | Elevation of privilege | User forges role claim in token to access admin endpoint | Identity service sole token issuer (MB-0003); RBAC check at boundary; flag eval at boundary (DEC-0016) | RBAC test matrix; token forgery red-team |

## 4. Partner API — STRIDE findings

| ID | Class | Threat (stub) | Control (stub) | Phase 24 expansion |
|---|---|---|---|---|
| PP-S-01 | Spoofing | Partner API key compromised; attacker impersonates partner | API key rotation; mTLS for high-trust partners; short-lived OAuth tokens | Key rotation drill; mTLS rollout plan |
| PP-T-01 | Tampering | Man-in-the-middle modifies partner request in transit | TLS 1.2+ (NFR §1.2); mTLS; request body signing for high-value mutations | MITM test plan |
| PP-R-01 | Repudiation | Partner disputes a posted transaction; claims they didn't send it | Idempotency key (DEC-0008) records request hash; audit log records partner identity | Non-repudiation evidence pack template |
| PP-I-01 | Information disclosure | Partner A can read Partner B's transactions via API | RLS (DEC-0003); partner-scope tokens; field-level filtering | Partner isolation test plan |
| PP-D-01 | Denial of service | Partner's misbehaving integration hammers API | Per-partner rate limit (separate from per-tenant); backpressure; circuit breaker | Partner throttle policy |
| PP-E-01 | Elevation of privilege | Partner exceeds authorized scope (e.g., writes when they should read) | Scope-down tokens; RBAC check on every mutation; least-privilege default | Scope audit checklist |

## 5. Admin — STRIDE findings

| ID | Class | Threat (stub) | Control (stub) | Phase 24 expansion |
|---|---|---|---|---|
| AD-S-01 | Spoofing | Admin phished; credentials stolen | MFA enforced (NFR §1.3); hardware key for high-privilege admins; anomalous-login alert | Phishing-resistance assessment |
| AD-T-01 | Tampering | Admin modifies audit log directly via SQL | RLS denies admin write to audit log; no update/delete API (DEC-0006); DB credentials separate from admin app | Tamper-attempt red-team |
| AD-R-01 | Repudiation | Admin denies changing tenant configuration | Audit log records admin identity + delta (WF-02); admin actions signed | Admin-action evidence template |
| AD-I-01 | Information disclosure | Admin of tenant A views tenant B's data | RLS (DEC-0003); admin scope limited to own tenant; super-admin scope audited separately | Cross-tenant access test plan |
| AD-D-01 | Denial of service | Admin bulk operation (e.g., bulk user import) starves DB | Bulk endpoints throttled; background processing for >1k records; backpressure | Bulk-operation load test |
| AD-E-01 | Elevation of privilege | Admin self-assigns super-admin role | Role assignment requires two-person approval for super-admin; delegation chain depth limit (DEC-0015) | Privilege-escalation red-team |

## 6. Webhooks — STRIDE findings

| ID | Class | Threat (stub) | Control (stub) | Phase 24 expansion |
|---|---|---|---|---|
| WH-S-01 | Spoofing | Attacker sends fake webhook to tenant endpoint | HMAC signature; tenant verifies signature; timestamp window | Signature verification test plan |
| WH-T-01 | Tampering | Man-in-the-middle modifies webhook payload in transit | TLS 1.2+ (NFR §1.2); HMAC covers body + headers | Tamper-detection test |
| WH-R-01 | Repudiation | Tenant claims webhook was never delivered; provider can't prove it | Delivery log records attempt + response code + signature; retry chain logged | Delivery evidence template |
| WH-I-01 | Information disclosure | Webhook payload contains PII that tenant endpoint logs in plaintext | PII minimization in payload (see `data-classification.md`); tenant contract requires encrypted storage | PII inventory reconciliation |
| WH-D-01 | Denial of service | Tenant endpoint slow; provider's webhook queue backs up | Per-tenant webhook queue; backpressure (MB-REQ-0014); circuit breaker on tenant endpoint; max retries | Queue-depth alert tuning |
| WH-E-01 | Elevation of privilege | Webhook triggers an action on tenant side that the webhook receiver shouldn't be able to invoke | Webhook receiver should use least-privilege actions; provider signs webhook type; tenant verifies type before acting | Receiver-side control checklist |

## 7. Realtime — STRIDE findings

| ID | Class | Threat (stub) | Control (stub) | Phase 24 expansion |
|---|---|---|---|---|
| RT-S-01 | Spoofing | Stolen token used to subscribe to another tenant's realtime channel | Token bound to tenant; channel subscription enforces RLS-equivalent at connection time | Cross-tenant subscription red-team |
| RT-T-01 | Tampering | Attacker injects fake event into realtime stream | Server-only sends; clients receive only; event signature on sensitive events | Event-signature scheme |
| RT-R-01 | Repudiation | Tenant denies receiving a critical realtime event (e.g., balance update) | Realtime delivery is best-effort; critical events also written to audit log (DEC-0006) and queryable via API | Delivery-vs-audit reconciliation |
| RT-I-01 | Information disclosure | Tenant A subscribes to tenant B's channel | Channel name includes tenant_id; subscription check at join; RLS-equivalent | Channel-isolation test plan |
| RT-D-01 | Denial of service | Tenant opens excessive connections; exhausts server resources | Per-tenant connection limit; backpressure; close idle connections | Connection-limit tuning |
| RT-E-01 | Elevation of privilege | Tenant client attempts to publish (write) via realtime channel | Realtime is read-only for clients; writes go through Player API with full auth + audit | Publish-attempt red-team |

## 8. Coverage matrix

The Phase 2 stub requires ≥1 finding per STRIDE class per surface.
The matrix below confirms coverage. Every cell is non-empty.

| Surface \ STRIDE | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| Player API | PA-S-01 | PA-T-01 | PA-R-01 | PA-I-01 | PA-D-01 | PA-E-01 |
| Partner API | PP-S-01 | PP-T-01 | PP-R-01 | PP-I-01 | PP-D-01 | PP-E-01 |
| Admin | AD-S-01 | AD-T-01 | AD-R-01 | AD-I-01 | AD-D-01 | AD-E-01 |
| Webhooks | WH-S-01 | WH-T-01 | WH-R-01 | WH-I-01 | WH-D-01 | WH-E-01 |
| Realtime | RT-S-01 | RT-T-01 | RT-R-01 | RT-I-01 | RT-D-01 | RT-E-01 |

**30 findings** (5 surfaces × 6 classes). All are stubs; expansion
to Phase 24 deliverable depth is tracked as a Phase 24 task in
`stage-02-handoff.md` §6.

## 9. Vendor surfaces (deferred to risk-register)

Vendor surfaces (KYC, sanctions/PEP, IdP, cloud provider, payment
rails) are out of scope for this document. They are recorded in
`docs/architecture/risk-register.md` §3 (vendor risk) with their
own threat stubs. The split is intentional: this document covers
platform-owned surfaces; `risk-register.md` covers vendor surfaces.

## 10. Phase 24 expansion plan

Each finding above is a stub. Phase 24 expands each stub into:

1. **Attack tree** — step-by-step exploitation path.
2. **Control mapping** — which existing controls mitigate, with
   coverage assessment.
3. **Residual risk rating** — likelihood × impact after controls.
4. **Test plan** — how the control is verified (automated test,
   red-team exercise, third-party assessment).
5. **Owner and due date** — for any residual risk that requires
   additional controls.

Phase 24 deliverable: 30 expanded findings (one per stub above) +
vendor-surface findings (per `risk-register.md`).

## 11. Cross-references

- DEC-0025 (architecture inventory map): `traceability.md` §C
- NFR §1 (security): `docs/requirements/nfr.md`
- Risk register (vendor surfaces): `docs/architecture/risk-register.md`
- PII register: `docs/architecture/data-classification.md`
- Capacity assumptions (rate limits, etc.): `docs/architecture/capacity-assumptions.md`
- Phase 2 handoff (Phase 24 threat-model expansion): `docs/stage-handoffs/stage-02-handoff.md`
