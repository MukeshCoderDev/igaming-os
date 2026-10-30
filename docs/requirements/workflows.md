# Workflows — Increment 1 (Phase 1)

| Field | Value |
|---|---|
| Document | `docs/requirements/workflows.md` |
| Version | 5.2 |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | BLUEPRINT §9; `triage-table.md` |

This document specifies the ten workflows triaged in
`triage-table.md`. Each workflow has: a trigger, a set of actors, a
step sequence, the audit events emitted, the failure modes, and the
REQs/DECs that govern it. Workflows not present in `triage-table.md`
are out of Increment 1 and are not specified here.

The ten workflows are grouped by the four capability areas in scope
for Increment 1: Tenancy, Identity, Audit, Reliable Core.

## 1. Tenancy workflows

### 1.1 WF-01: Tenant provisioning

**Capability area:** Tenancy.
**Trigger:** A new customer contract is signed (Commercial Lead
notifies the platform via the tenant-provisioning API).
**Actors:** Commercial Lead (initiates); Platform (executes);
Compliance Lead (approves).
**Steps:**
1. Commercial Lead submits provisioning request with tenant legal
   name, jurisdiction, contract ID, and SSO protocol preference.
2. Platform validates the request against the contract record.
3. Compliance Lead approves the provisioning (recorded as a
   compliance event).
4. Platform creates the tenant aggregate root (DEC-0014).
5. Platform assigns the tenant's data partition (row-level security
   key per DEC-0003).
6. Platform emits `tenant.provisioned` domain event (MB-REQ-0012).
7. Platform emits `audit.tenant_provisioned` audit event
   (MB-REQ-0004).
8. Platform notifies the Commercial Lead and the new tenant's
   nominated admin user.

**Audit events:** `audit.tenant_provisioned`,
`audit.tenant_admin_invited`, `audit.compliance_approved_provisioning`.
**Failure modes:** (a) Contract validation fails → request rejected,
no state change. (b) Compliance approval denied → request rejected,
audit event `audit.compliance_denied_provisioning` emitted. (c)
Provisioning partial failure → compensating action: tenant aggregate
marked `provisioning_failed`, no data partition assigned, audit event
emitted.
**REQs/DECs:** DEC-0003, DEC-0014, MB-REQ-0001, MB-REQ-0002,
MB-REQ-0023, MB-REQ-0012, MB-REQ-0004, Pain-REQ-0002.

### 1.2 WF-02: Tenant configuration update

**Capability area:** Tenancy.
**Trigger:** A tenant admin submits a configuration change for their
own tenant.
**Actors:** Tenant admin (initiates); Platform (executes).
**Steps:**
1. Tenant admin submits configuration delta.
2. Platform validates the delta against the tenant's allowed
   configuration schema.
3. Platform applies the delta to the tenant's configuration record.
4. Platform emits `tenant.configuration_updated` domain event.
5. Platform emits `audit.tenant_configuration_updated` audit event
   with the delta and the actor identity.

**Audit events:** `audit.tenant_configuration_updated`.
**Failure modes:** (a) Schema validation fails → delta rejected, no
state change, audit event `audit.tenant_configuration_update_rejected`
emitted with reason. (b) Concurrent update conflict → optimistic
locking retry; if retry exhausts, audit event emitted and admin
notified.
**REQs/DECs:** DEC-0014, MB-REQ-0012, MB-REQ-0004, MB-REQ-0018.

## 2. Identity workflows

### 2.1 WF-03: User invitation and acceptance

**Capability area:** Identity.
**Trigger:** A tenant admin invites a new user to their tenant.
**Actors:** Tenant admin (initiates); invitee (accepts); Platform
(executes); Identity service (verifies).
**Steps:**
1. Tenant admin submits invitation with invitee email and proposed
   role.
2. Platform validates the role against the tenant's role set.
3. Platform emits an invitation token (single-use, time-bounded).
4. Platform emits `audit.user_invited` audit event.
5. Invitee accepts the invitation (out-of-band email link).
6. Identity service verifies the token and creates the user record.
7. Platform emits `user.created` domain event.
8. Platform emits `audit.user_created` audit event.

**Audit events:** `audit.user_invited`, `audit.user_invitation_expired`,
`audit.user_created`.
**Failure modes:** (a) Token expired → invitee must request
re-invitation; audit event `audit.user_invitation_expired` emitted.
(b) Token reused → identity service rejects; audit event
`audit.user_invitation_replay_rejected` emitted. (c) Role validation
fails → invitation rejected at submission.
**REQs/DECs:** DEC-0004, MB-REQ-0003, Pain-REQ-0012, MB-REQ-0004,
MB-REQ-0013.

### 2.2 WF-04: Single sign-on authentication

**Capability area:** Identity.
**Trigger:** A user attempts to authenticate.
**Actors:** User (initiates); Identity service (executes); Platform
(records session).
**Steps:**
1. User submits credentials or is redirected to the tenant's IdP
   (OIDC per DEC-0004, or SAML per DEC-0005).
2. Identity service verifies credentials or processes the IdP
   assertion.
3. Identity service issues an auth token (MB-REQ-0003 — identity
   service is the sole issuer).
4. Platform records the session.
5. Platform emits `audit.user_authenticated` audit event with the
   authentication method, the actor identity, and the time.

**Audit events:** `audit.user_authenticated`,
`audit.user_authentication_failed`.
**Failure modes:** (a) Invalid credentials → identity service rejects;
audit event with reason. (b) IdP unavailable → circuit breaker
(MB-REQ-0015) opens; user redirected to retry; audit event emitted.
(c) Rate limit exceeded (Pain-REQ-0008) → identity service returns
429 with backpressure header.
**REQs/DECs:** DEC-0004, DEC-0005, MB-REQ-0003, MB-REQ-0013,
MB-REQ-0014, MB-REQ-0015, Pain-REQ-0003, Pain-REQ-0008, MB-REQ-0004.

### 2.3 WF-05: Role assignment and delegation

**Capability area:** Identity.
**Trigger:** A tenant admin assigns a role to a user, or a user
delegates a subset of their permissions to another user.
**Actors:** Tenant admin or delegating user (initiates); Identity
service (executes).
**Steps:**
1. Initiator submits role assignment or delegation request.
2. Identity service validates the initiator's authority to make the
   assignment (RBAC check).
3. Identity service validates the delegation chain depth (DEC-0015).
4. Identity service records the assignment or delegation.
5. Platform emits `user.role_assigned` or `user.delegated` domain
   event.
6. Platform emits `audit.role_assigned` or `audit.delegation_created`
   audit event.

**Audit events:** `audit.role_assigned`, `audit.delegation_created`,
`audit.role_assignment_revoked`.
**Failure modes:** (a) Initiator lacks authority → request rejected;
audit event `audit.role_assignment_unauthorized` emitted. (b)
Delegation chain depth exceeded → request rejected; audit event
emitted.
**REQs/DECs:** DEC-0015, MB-REQ-0003, Pain-REQ-0012, MB-REQ-0004.

## 3. Audit workflows

### 3.1 WF-06: Audit event emission

**Capability area:** Audit.
**Trigger:** Any state-changing operation in the platform.
**Actors:** Any service (emits); Audit service (records).
**Steps:**
1. Emitting service constructs an audit event with: timestamp,
   actor identity, tenant ID, operation, before-state hash, after-state
   hash.
2. Emitting service submits the event to the audit service's append
   API (MB-REQ-0004 — append-only).
3. Audit service computes the hash chain: `hash_n = SHA256(hash_n-1
   || event_n)` (DEC-0007).
4. Audit service persists the event with its hash.
5. Audit service returns the assigned sequence number to the
   emitter.
6. Emitting service logs the sequence number for reconciliation.

**Audit events:** (This workflow is the audit log itself; the audit
event recorded IS the audit event for the triggering operation. The
meta-event `audit.hash_chain_advance` is emitted but is not itself
hash-chained; it is a telemetry signal, not an audit record.)
**Failure modes:** (a) Audit service unavailable → emitting service
must not commit the state change. State change is conditional on
audit write success. (b) Hash chain mismatch (detected on read) →
alert; the platform halts mutations for the affected tenant until
investigated.
**REQs/DECs:** DEC-0006, DEC-0007, MB-REQ-0004, Law-REQ-0010,
MB-REQ-0012, MB-REQ-0020.

### 3.2 WF-07: Audit log query and export

**Capability area:** Audit.
**Trigger:** A compliance-team user queries the audit log or requests
an export.
**Actors:** Compliance user (initiates); Audit service (executes).
**Steps:**
1. Compliance user submits a query (filters: tenant, time range,
   actor, operation type).
2. Audit service validates the user's authority to query the
   specified tenant.
3. Audit service executes the query against the append-only log.
4. For exports: audit service generates a signed export bundle
   (CSV or JSON-LD) with a manifest.
5. Platform emits `audit.query_executed` and `audit.export_generated`
   audit events (the audit service audits its own reads; this is the
   "trust but verify" property).

**Audit events:** `audit.query_executed`, `audit.export_generated`.
**Failure modes:** (a) User lacks authority → query rejected; audit
event `audit.query_unauthorized` emitted. (b) Query times out →
backpressure signal returned (MB-REQ-0014); user offered async
export. (c) Export bundle generation fails → audit event emitted,
user notified.
**REQs/DECs:** DEC-0006, MB-REQ-0004, Pain-REQ-0004, MB-REQ-0014.

## 4. Reliable Core workflows

### 4.1 WF-08: Heartbeat and health monitoring

**Capability area:** Reliable Core.
**Trigger:** Continuous (every 10 seconds per service).
**Actors:** Each service (emits); Observability backend (aggregates).
**Steps:**
1. Each service emits a heartbeat telemetry signal
   (MB-REQ-0020) containing: service name, version, tenant counts,
   request rate, error rate, queue depth.
2. Observability backend aggregates heartbeats.
3. Observability backend alerts on: missing heartbeat > 60s,
   error rate > threshold, queue depth > threshold.
4. Alerts are routed to the on-call operator (Operations Lead).

**Audit events:** None (this is telemetry, not audit). However,
alert acknowledgment and resolution ARE audited: `audit.alert_acknowledged`,
`audit.alert_resolved`.
**Failure modes:** (a) Observability backend unavailable → services
buffer heartbeats locally for up to 5 minutes; on restore, heartbeats
are forwarded. (b) Alert router unavailable → alerts fall through to
a secondary pager.
**REQs/DECs:** DEC-0020, MB-REQ-0020, MB-REQ-0014, MB-REQ-0015.

### 4.2 WF-09: Backup execution

**Capability area:** Reliable Core.
**Trigger:** Scheduled (daily full, hourly incremental) and on-demand
(by Operations Lead).
**Actors:** Operations Lead (on-demand); Platform (executes);
Storage backend (records).
**Steps:**
1. Platform initiates backup per schedule.
2. Platform snapshots the tenant data partitions, the audit log, and
   the configuration store.
3. Platform computes a manifest of included objects with checksums.
4. Platform uploads the backup bundle to the storage backend.
5. Platform emits `audit.backup_completed` audit event with the
   manifest hash.

**Audit events:** `audit.backup_completed`, `audit.backup_failed`.
**Failure modes:** (a) Backup fails → audit event `audit.backup_failed`
emitted; alert raised; on-call operator investigates. (b) Backup
verification (manifest vs. actual) fails → backup marked
`verification_failed`, must be re-run; old backups retained until
verification passes.
**REQs/DECs:** DEC-0020, MB-REQ-0020, Law-REQ-0021 (BCP), MB-REQ-0004.

### 4.3 WF-10: Restore (disaster recovery drill)

**Capability area:** Reliable Core.
**Trigger:** Scheduled (quarterly DR drill) or emergency (actual
incident).
**Actors:** Operations Lead (initiates); Platform (executes);
Compliance Lead (approves emergency restore).
**Steps:**
1. Operations Lead submits restore request with: target environment,
   backup ID, tenant scope.
2. Platform validates the backup manifest.
3. For emergency restore: Compliance Lead approves; audit event
   `audit.emergency_restore_approved` emitted.
4. Platform provisions a fresh environment and restores the backup.
5. Platform runs verification checks (row counts, hash chain
   validation, configuration schema).
6. Platform emits `audit.restore_completed` audit event with the
   verification result.

**Audit events:** `audit.emergency_restore_approved`,
`audit.restore_completed`, `audit.restore_verification_failed`.
**Failure modes:** (a) Verification fails → environment is not
promoted; Operations Lead notified; root-cause investigation
required. (b) Backup missing or corrupt → restore cannot proceed;
audit event `audit.restore_blocked_missing_backup` emitted; the
BCP/DR plan is invoked at the Operations Lead level.
**REQs/DECs:** DEC-0020, MB-REQ-0020, Law-REQ-0021, Law-REQ-0022,
MB-REQ-0004, MB-REQ-0021.

## 5. Workflows deferred to later phases

The following workflows are NOT specified in this document because
they are triaged out of Increment 1 in `triage-table.md`. They are
listed here only to confirm their absence is intentional.

- **Customer deposit** — Phase 12+. Not specified.
- **Ledger posting** — Phase 11. Not specified.
- **KYC verification** — Increment 2. Blocked on Q6 (vendor).
- **Sanctions/PEP screening** — Increment 2. Blocked on Q7 (vendor).
- **Payment instruction** — Increment 3. Not specified.
- **FX conversion** — Increment 3. Not specified.

Each of these will receive its own workflow specification document
in the phase that delivers it. The Phase 1 specification set is
closed at ten workflows.
