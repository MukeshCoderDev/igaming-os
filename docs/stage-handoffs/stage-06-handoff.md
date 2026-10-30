# Stage 06 Handoff — Phase 7 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-06-handoff.md` |
| Version | 5.7 (Phase 6) |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | Phase 6 hard acceptance; BLUEPRINT §10, §11 |

This document defines what Phase 6 hands off to Phase 7, the entry
criteria Phase 7 must satisfy, and the contracts Phase 7 must honor.

## 1. Phase 6 deliverables handed off

### 1.1 ADRs (4 ACCEPTED in Phase 6)

| ADR | Title | Status | Approver |
|---|---|---|---|
| ADR-0031 | AuthN strategy (JWT + refresh + Argon2id + MFA + API keys + service JWTs) | ACCEPTED | Identity Lead + Security Lead + Architecture Lead |
| ADR-0032 | RBAC model (permission-based, closed catalog, baseline roles) | ACCEPTED | Identity Lead + Architecture Lead + API Lead |
| ADR-0033 | Tenant resolution order (JWT claim + membership validation + switch) | ACCEPTED | Architecture Lead + Identity Lead + Security Lead |
| ADR-0034 | Service/agent identity (shadow→live gate + typ=service JWT + endpoint separation) | ACCEPTED | Identity Lead + Engineering Lead + Security Lead |

### 1.2 Identity data model

| Path | Purpose |
|---|---|
| `src/noventra/apps/identity/domain/aggregates.py` | User, TenantMembership, Role, Permission, ServiceIdentity aggregates + status enums. |
| `src/noventra/apps/identity/domain/permissions.py` | Closed permission catalog (15 codes); BASELINE_ROLE_PERMISSIONS (admin/manager/viewer/service). |
| `src/noventra/apps/identity/domain/ports.py` | UserRepository, TenantMembershipRepository, RoleRepository, ServiceIdentityRepository ports. |
| `src/noventra/apps/identity/adapters/orm.py` | Django ORM: User, TenantMembership, Role, Permission, RolePermission, ServiceIdentity, RefreshTokenBlacklist. |
| `src/noventra/apps/identity/adapters/jwt.py` | JWT issuance (HS256) + verification; access (15min) + refresh (30d) + service (1h). |
| `src/noventra/apps/identity/migrations/0001_initial.py` | 7 tables + RLS on tenant-scoped (membership, service_identity) + baseline roles/permissions/users/memberships/service identities. |

### 1.3 AuthN + RBAC middleware

| Path | Purpose |
|---|---|
| `src/noventra/middleware/authn.py` | AuthNMiddleware: JWT verification, sets request.jwt_claims + jwt_tenant_id, separates human/service, blacklisted token check. |
| `src/noventra/middleware/permissions.py` | @human_only, @service_only, @require_permission decorators. Defense-in-depth for service.mutate (shadow denied). |
| `src/noventra/middleware/tenant.py` (extended) | Tenant middleware now consumes request.jwt_tenant_id from AuthN middleware (Phase 5 + Phase 6 coupling per ADR-0033). |

### 1.4 AuthN API

| Path | Purpose |
|---|---|
| `src/noventra/apps/identity/api/views.py` | LoginView, RefreshView, LogoutView, SwitchTenantView. |
| `src/noventra/apps/identity/api/urls.py` | /auth/login/, /auth/refresh/, /auth/logout/, /auth/switch-tenant/. |

### 1.5 Documentation

| Path | Purpose |
|---|---|
| `docs/architecture/permission-matrix.md` | (role × endpoint × outcome) matrix; closed test parametrization. |
| `docs/stage-handoffs/stage-06-handoff.md` | This document. |
| `docs/audits/phase-006-audit.md` | Phase 6 audit. |

### 1.6 Tests

| Path | Tests |
|---|---|
| `tests/test_identity_rbac.py` | Permission catalog closed; JWT issuance/verification/tamper; cross-tenant denial at membership level; agent-vs-human enforcement; shadow→live gate; refresh rotation; MFA fields. |

## 2. Contracts Phase 7 must honor

### 2.1 AuthN contract

- JWT shape: `{sub, tenant_id, typ, role, jti, iat, exp}`.
  - `typ` ∈ {"bearer" (human), "service", "refresh"}.
  - `sub` = user_uuid (human) or service_uuid (service).
  - `tenant_id` = the tenant context.
  - `role` = role name (admin/manager/viewer/service).
- Refresh flow: POST /auth/refresh/ with refresh_token; old JTI blacklisted; new access + refresh issued.
- Logout: POST /auth/logout/ blacklists the refresh token.
- Switch-tenant: POST /auth/switch-tenant/ with tenant_id; validates active membership; re-issues tokens.

### 2.2 Permission catalog contract

- New endpoints MUST register their required permission in `permissions.py` (closed catalog).
- New endpoints MUST use `@require_permission("code")` decorator.
- Service-only endpoints MUST use `@service_only`; human-only MUST use `@human_only`.
- The (role × endpoint) matrix in `permission-matrix.md` MUST be updated for every new endpoint.
- Linter rule 35 verifies the catalog is closed.

### 2.3 Tenant resolution order contract (ADR-0033)

- Resolution order: (1) JWT `tenant_id` claim (validated against active membership); (2) X-Tenant-ID header (service accounts only); (3) missing/malformed → 400; (4) no active membership → 403.
- Multi-tenant users switch via /auth/switch-tenant/.
- First-login default tenant: user's `default_tenant_uuid` or first active membership.

### 2.4 Phase 4 + 5 contracts (still in force)

- Error format: `problem_response()` for all errors.
- Logging: structured logging with correlation_id + tenant_id + user_id on every auth event.
- PII redaction: passwords never logged; tokens hashed in logs (`hash_token_for_logging`).
- RLS: every new tenant-scoped table has RLS + policy.
- pgbouncer: SET LOCAL only, ATOMIC_REQUESTS, prepare_threshold=None.

## 3. Phase 7 entry criteria

Phase 7 starts only when ALL of the following are true:

### 3.1 Phase 0 evidence gate passed
Q1, Q2, Q4, Q5 resolved or formally BLOCKED.

### 3.2 Phase 6 hard acceptance met
- Migrations produce schema + baseline roles + permissions + service identities.
- (user × tenant) cross-tenant denial tests pass at user-membership level.
- Agent identities cannot authenticate as humans on human-only endpoints; vice versa.
- Shadow→live promotion gate enforced; shadow agents cannot mutate.
- AuthN endpoints return Phase 4 error format with correlation_id; auth events logged.
- Permission catalog closed (rule 35 green); every (role, endpoint) pair has explicit test outcome.
- ADR-0031..0034 ACCEPTED with recorded approvers.
- Linter rules 1–17, 24, 26, 27 (inherited) + 29, 30, 31, 32, 35 green.
- Coverage ≥80% on identity module; mypy strict green.
- OpenAPI drift check green.
- stage-05-handoff.md constraints fully consumed.

### 3.3 Linter green on rules 1–35

### 3.4 Open-questions carry-over explicit
Q1 blocks user data jurisdiction pinning; Q5 blocks MFA via SMS + token revocation storage. Q43–Q48 added.

## 4. Phase 7 scope (preview)

Phase 7 hardens identity + begins audit log:

| Deliverable | Owner |
|---|---|
| RS256 JWT signing + key rotation | Identity Lead |
| Real Argon2id password hashing (argon2-cffi) | Identity Lead |
| TOTP MFA verification (pyotp) | Identity Lead |
| API key authN for partner integrations | Identity Lead |
| Custom roles + permission management UI | Identity Lead |
| Audit log implementation (Phase 8 scope may pull forward) | Architecture Lead |
| Membership list endpoint + Redis cache | Identity Lead |
| Promotion gate automation (ops console) | Engineering Lead |
| ADR-0004 (OIDC) → ACCEPTED | Identity Lead |
| ADR-0015 (RBAC delegation) → ACCEPTED | Identity Lead |
| Real test factories (UserFactory, TenantMembershipFactory) | Engineering Lead |
| Coverage 85%@15 (per ADR-0027) | Engineering Lead |

## 5. Handoff sign-off

- **Engineering Lead** — Phase 6 acceptance criteria met.
- **Architecture Lead** — 4 ADRs ACCEPTED; contracts documented.
- **Identity Lead** — AuthN + RBAC + service identity verified.
- **Security Lead** — Shadow→live gate + PII redaction + auth event logging verified.

## 6. Worklog pointer

`/home/z/my-project/worklog.md` — Phase 6 close-out entry.
