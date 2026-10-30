# Permission Matrix — Role × Endpoint × Outcome

| Field | Value |
|---|---|
| Document | `docs/architecture/permission-matrix.md` |
| Version | 5.7 (Phase 6) |
| Status | Approved |
| Owner | Identity Lead |
| Authority | ADR-0032 / DEC-0037 |

This document is the closed test parametrization for the (role ×
endpoint × outcome) matrix required by Phase 6 spec output #10. Every
(role, endpoint) pair has an explicit expected outcome. The test
suite (`tests/test_permission_matrix.py`) parametrizes over this
matrix.

## 1. Roles

Per ADR-0032 / `permissions.py`:

| Role | Description | Key permissions |
|---|---|---|
| admin | Full access (no service permissions) | All non-service.* |
| manager | Read + write + invite (no delete) | tenancy.*.read/write, identity.user.read/write/invite, audit.log.read |
| viewer | Read-only | tenancy.*.read, identity.user.read, identity.role.read, audit.log.read |
| service | Service-account role | read + service.mutate (LIVE only) + service.promote |

## 2. Endpoints

Phase 6 endpoints:

| Endpoint | Method | Required permission | Human/Service |
|---|---|---|---|
| `/auth/login/` | POST | (public) | Both |
| `/auth/refresh/` | POST | (public) | Both |
| `/auth/logout/` | POST | (authenticated) | Both |
| `/auth/switch-tenant/` | POST | (authenticated + active membership) | Both |
| `/health/` | GET | (public) | Both |
| `/metrics/` | GET | (public) | Both |

Phase 7+ endpoints (preview; not yet implemented):

| Endpoint | Method | Required permission | Human/Service |
|---|---|---|---|
| `/api/v1/tenants/{uuid}/` | GET | tenancy.tenant.read | Human |
| `/api/v1/tenants/` | POST | tenancy.tenant.write | Human |
| `/api/v1/tenants/{uuid}/` | DELETE | tenancy.tenant.delete | Human |
| `/api/v1/users/` | GET | identity.user.read | Human |
| `/api/v1/users/` | POST | identity.user.invite | Human |
| `/api/v1/audit/log/` | GET | audit.log.read | Human |
| `/api/v1/audit/export/` | POST | audit.log.export | Human |
| `/api/v1/services/{uuid}/promote/` | POST | service.promote | Service |
| `/internal/mutate/` | POST | service.mutate | Service (LIVE only) |

## 3. (Role × Endpoint) matrix

| Endpoint | admin | manager | viewer | service (shadow) | service (live) |
|---|---|---|---|---|---|
| `/auth/login/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/auth/refresh/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/auth/logout/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/auth/switch-tenant/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/health/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/metrics/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/tenants/{uuid}/` GET | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/tenants/` POST | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 |
| `/api/v1/tenants/{uuid}/` DELETE | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| `/api/v1/users/` GET | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/users/` POST (invite) | ✅ | ✅ | ❌ 403 | ❌ 403 (human-only) | ❌ 403 (human-only) |
| `/api/v1/audit/log/` GET | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/audit/export/` POST | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| `/api/v1/services/{uuid}/promote/` POST | ❌ 403 (service-only) | ❌ 403 | ❌ 403 | ✅ | ✅ |
| `/internal/mutate/` POST | ❌ 403 (service-only) | ❌ 403 | ❌ 403 | ❌ 403 (shadow denied) | ✅ |

## 4. Test parametrization

The test suite parametrizes over the matrix in §3. Each (role, endpoint)
pair is a test case. The test:
1. Issues a JWT for the role.
2. Calls the endpoint.
3. Asserts the expected outcome (✅ = 2xx; ❌ 403 = 403).

Shadow service denial: for `/internal/mutate/`, the test verifies that
a shadow service gets 403 even though the service role has
`service.mutate` (defense-in-depth per ADR-0034).

## 5. Cross-references

- ADR-0032: `docs/adr/ADR-0032.md`
- Permission catalog: `src/noventra/apps/identity/domain/permissions.py`
- Permission decorators: `src/noventra/middleware/permissions.py`
- Linter rule 35: `scripts/check_traceability.sh`
