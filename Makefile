# Makefile — Noventra dev targets (Phase 3).
# Per Phase 3 spec hard acceptance: make targets bootstrap, migrate, test,
# lint, typecheck, runserver must exist. Linter rule 14 enforces.

PYTHON ?= python
PIP ?= pip
DJANGO_SETTINGS_MODULE ?= noventra.settings.local

.PHONY: help bootstrap install migrate test lint typecheck runserver \
        format openapi-check check-rls clean docker-up docker-down \
        coverage-baseline mypy strict gitleaks pip-audit apply-branch-protection

help:  ## Show this help.
        @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
                awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

bootstrap: install migrate  ## Full bootstrap: install deps + migrate DB.

install:  ## Install Python deps (editable, with dev extras).
        $(PIP) install -e ".[dev]"

migrate:  ## Apply database migrations.
        DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) $(PYTHON) manage.py migrate

test:  ## Run pytest suite.
        DJANGO_SETTINGS_MODULE=noventra.settings.test $(PYTHON) -m pytest

lint:  ## Run ruff linter.
        $(PYTHON) -m ruff check src tests

format:  ## Run ruff formatter (auto-fix).
        $(PYTHON) -m ruff format src tests
        $(PYTHON) -m ruff check --fix src tests

typecheck:  ## Run type checker (Phase 4+: mypy or pyright).
        @echo "Phase 3: typecheck not yet wired (Phase 4+ deliverable)."
        @echo "  Ruff covers basic checks in the meantime."

runserver:  ## Run Django dev server.
        DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) $(PYTHON) manage.py runserver 0.0.0.0:8000

openapi-check:  ## Check OpenAPI spec drift (Phase 3: manual; Phase 4: CI).
        DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) $(PYTHON) manage.py spectacular --file /tmp/openapi-check.yaml
        @diff docs/api/openapi.yaml /tmp/openapi-check.yaml && echo "OpenAPI: in sync" || echo "OpenAPI: DRIFT (run: python manage.py spectacular --file docs/api/openapi.yaml)"

check-rls:  ## Check RLS coverage (Phase 3: vacuous pass).
        DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) $(PYTHON) manage.py check_rls_coverage

docker-up:  ## Start docker-compose stack (postgres + redis + app).
        docker compose --profile app up -d

docker-down:  ## Stop docker-compose stack.
        docker compose down

clean:  ## Remove build artifacts and caches.
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
        rm -rf .pytest_cache .ruff_cache staticfiles

# ─── Phase 4 targets (ADR-0025..0028) ──────────────────────────────────
coverage-baseline:  ## Generate coverage baseline (run after test suite).
        DJANGO_SETTINGS_MODULE=noventra.settings.test $(PYTHON) -m pytest --cov=noventra --cov-report=term
        @echo "Phase 4: regenerate .coverage-baseline-phase4.txt from coverage.xml"

mypy:  ## Run mypy on strict modules (per ADR-0027).
        $(PYTHON) -m mypy --strict src/noventra

strict: mypy  ## Alias for mypy.

gitleaks:  ## Run gitleaks secret scan (compare against baseline).
        @gitleaks detect --source . --baseline-path .gitleaks-baseline.json --redact --verbose

pip-audit:  ## Run pip-audit dependency scan (CVSS ≥7.0 blocks).
        $(PYTHON) -m pip_audit --strict --vulnerability-service osv --desc

apply-branch-protection:  ## Apply GitHub branch protection rules.
        bash deploy/ci/apply-branch-protection.sh

# ─── Stage B Verification (Phases 11-14) ────────────────────────────────
.PHONY: verify-stage-b

verify-stage-b: ## Run Stage B verification for Phases 11-14 (requires Docker).
	@echo "=== Stage B Verification for Phases 11-14 ==="
	@echo "Starting verification stack (Postgres + Redis + pgbouncer)..."
	docker compose -f docker-compose.verify.yml up -d
	@echo "Waiting for services to be healthy (30s)..."
	sleep 30
	@echo ""
	@echo "=== 1. Linter (rules 1-110) ==="
	docker compose -f docker-compose.verify.yml exec app bash scripts/check_traceability.sh
	@echo ""
	@echo "=== 2. Full test suite with coverage ==="
	docker compose -f docker-compose.verify.yml exec app pytest \
		--cov=src/noventra/modules/ledger \
		--cov=src/noventra/modules/fx \
		--cov=src/noventra/modules/bonuses \
		--cov=src/noventra/modules/protection \
		--cov-report=term-missing --cov-branch --cov-fail-under=95 -v
	@echo ""
	@echo "=== 3. Phase 11 concurrency tests ==="
	docker compose -f docker-compose.verify.yml exec app pytest tests/concurrency/ -v
	@echo ""
	@echo "=== 4. Financial audit chain tamper test ==="
	docker compose -f docker-compose.verify.yml exec app pytest tests/security/test_financial_audit_chain_tamper.py -v
	@echo ""
	@echo "=== 5. PCI DLP injection test ==="
	docker compose -f docker-compose.verify.yml exec app pytest tests/security/test_pci_dlp_injection.py -v
	@echo ""
	@echo "=== 6. Cross-module SE enforcement test ==="
	docker compose -f docker-compose.verify.yml exec app pytest tests/integration/test_cross_module_se_enforcement.py -v
	@echo ""
	@echo "=== 7. SE-survives-erasure test ==="
	docker compose -f docker-compose.verify.yml exec app pytest tests/integration/test_se_survives_erasure.py -v
	@echo ""
	@echo "=== 8. Kill Switch <200ms SLO load test ==="
	docker compose -f docker-compose.verify.yml exec app python manage.py runserver 0.0.0.0:8000 &
	@sleep 10
	docker compose -f docker-compose.verify.yml exec load-tester python scripts/kill_switch_load_test.py \
		--target http://app:8000 --connections 100 --triggers 10 \
		--output /results/kill_switch_results.json
	docker compose -f docker-compose.verify.yml exec load-tester python scripts/verify_kill_switch_slo.py \
		--input /results/kill_switch_results.json --threshold-ms 200
	@echo ""
	@echo "=== 9. Generate verification report ==="
	docker compose -f docker-compose.verify.yml exec app python scripts/generate_verification_report.py \
		--output docs/audits/stage-b-verification-report.md
	@echo ""
	@echo "=== 10. Check gate ==="
	docker compose -f docker-compose.verify.yml exec app python scripts/check_phase_15_gate.py \
		--report docs/audits/stage-b-verification-report.md
	@echo ""
	@echo "=== Cleaning up ==="
	docker compose -f docker-compose.verify.yml down
	@echo ""
	@echo "=== Stage B Verification Complete ==="
	@echo "Check docs/audits/stage-b-verification-report.md for verdict."
	@echo "Check verify-results/kill_switch_results.json for <200ms SLO details."
